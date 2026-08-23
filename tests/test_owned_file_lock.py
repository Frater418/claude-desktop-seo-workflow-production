from __future__ import annotations

import json
import multiprocessing
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.owned_file_lock import OwnedFileLock, OwnedFileLockError


class _SynchronizedOwnedFileLock(OwnedFileLock):
    def __init__(self, path: Path, barrier: multiprocessing.synchronize.Barrier) -> None:
        super().__init__(path, grace_seconds=0)
        self._barrier = barrier

    def _before_takeover_coordination(self) -> None:
        self._barrier.wait(timeout=5)


def _contend_for_stale_lock(
    path: str,
    barrier: multiprocessing.synchronize.Barrier,
    results: multiprocessing.queues.Queue[tuple[str, str]],
    release_winner: multiprocessing.synchronize.Event,
) -> None:
    lock = _SynchronizedOwnedFileLock(Path(path), barrier)
    try:
        with lock:
            results.put(("acquired", lock.token))
            release_winner.wait(timeout=5)
    except OwnedFileLockError:
        results.put(("contended", ""))


class OwnedFileLockTests(unittest.TestCase):
    def test_second_contender_cannot_remove_new_owner_after_stale_takeover(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "resource.lock"
            path.write_text(json.dumps({"schema_version": 1, "pid": 999_999_999, "hostname": socket.gethostname(), "token": "stale-owner"}), encoding="utf-8")
            os.utime(path, (0, 0))
            first = OwnedFileLock(path, grace_seconds=0)

            with patch("services.owned_file_lock.os.kill", side_effect=ProcessLookupError):
                first.__enter__()

            second = OwnedFileLock(path, grace_seconds=0)
            with self.assertRaisesRegex(OwnedFileLockError, "lock is active"):
                second.__enter__()
            self.assertEqual(first.token, json.loads(path.read_text(encoding="utf-8"))["token"])
            first.__exit__(None, None, None)

    def test_concurrent_stale_takeover_has_one_owner_and_loser_cannot_remove_it(self) -> None:
        # Given: two processes inspect the same stale primary lock before takeover coordination
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "resource.lock"
            path.write_text(json.dumps({"schema_version": 1, "pid": 999_999_999, "hostname": socket.gethostname(), "token": "stale-owner"}), encoding="utf-8")
            os.utime(path, (0, 0))
            context = multiprocessing.get_context("spawn")
            barrier = context.Barrier(2)
            results = context.Queue()
            release_winner = context.Event()
            contenders = [
                context.Process(target=_contend_for_stale_lock, args=(str(path), barrier, results, release_winner))
                for _ in range(2)
            ]
            for contender in contenders:
                contender.start()

            # When: both contenders advance together into kernel takeover coordination
            outcomes = {results.get(timeout=10), results.get(timeout=10)}

            # Then: exactly one owns the replacement lock while the loser only observes contention
            self.assertEqual(1, sum(outcome[0] == "acquired" for outcome in outcomes))
            self.assertEqual(1, sum(outcome[0] == "contended" for outcome in outcomes))
            winner_token = next(token for status, token in outcomes if status == "acquired")
            self.assertEqual(winner_token, json.loads(path.read_text(encoding="utf-8"))["token"])
            release_winner.set()
            for contender in contenders:
                contender.join(timeout=10)
                self.assertEqual(0, contender.exitcode)

    def test_stale_takeover_recovers_after_process_crashes_while_holding_coordination(self) -> None:
        # Given: a stale primary lock and a child that hard-crashes while holding takeover coordination
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "resource.lock"
            path.write_text(json.dumps({"schema_version": 1, "pid": 999_999_999, "hostname": socket.gethostname(), "token": "stale-owner"}), encoding="utf-8")
            os.utime(path, (0, 0))
            script = "\n".join((
                "from pathlib import Path",
                "import os",
                "import sys",
                "from services.owned_file_lock import OwnedFileLock",
                "lock = OwnedFileLock(Path(sys.argv[1]), grace_seconds=0)",
                "lock.path.parent.mkdir(parents=True, exist_ok=True)",
                "with lock._takeover_coordination():",
                "    os._exit(73)",
            ))

            # When: the coordination owner exits without cleanup
            crashed = subprocess.run([sys.executable, "-c", script, str(path)], cwd=Path(__file__).resolve().parents[1], check=False)

            # Then: the kernel releases coordination and a new owner can recover stale primary metadata
            self.assertEqual(73, crashed.returncode)
            with OwnedFileLock(path, grace_seconds=0) as recovered:
                self.assertNotEqual("stale-owner", recovered.token)


if __name__ == "__main__":
    unittest.main()
