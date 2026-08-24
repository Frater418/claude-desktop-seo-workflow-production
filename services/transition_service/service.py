"""CLI and durable ledger boundary for the transition service."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .contracts import load_json, load_workflow_graph
from .engine import process_transition
from services.owned_file_lock import OwnedFileLock, OwnedFileLockError


class LedgerLockContentionError(RuntimeError):
    """Raised when another local transition process owns the ledger lock."""

    def __init__(self, ledger_path: Path) -> None:
        self.ledger_path = ledger_path
        super().__init__(f"ERROR_TRANSITION_LEDGER_LOCKED: Durable ledger lock is active: {ledger_path}")


@contextmanager
def durable_ledger_lock(ledger_path: Path) -> Iterator[None]:
    """Acquire the durable-local ledger lock or fail immediately on contention."""
    lock_path = ledger_path.with_suffix(ledger_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with OwnedFileLock(lock_path, grace_seconds=0):
            yield
    except OwnedFileLockError as exc:
        raise LedgerLockContentionError(ledger_path) from exc


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _load_ledger(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    fingerprints = load_json(path).get("fingerprints")
    if not isinstance(fingerprints, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in fingerprints.items()):
        raise RuntimeError("Transition ledger has an invalid durable-local format.")
    return fingerprints


def main() -> int:
    parser = argparse.ArgumentParser(description="Heartweb central transition service")
    parser.add_argument("--request", required=True, help="JSON request containing command, run, artifacts, gates and context")
    parser.add_argument("--output", required=True, help="Atomic transition-result output path")
    parser.add_argument("--ledger", required=True, help="Durable local idempotency ledger path")
    args = parser.parse_args()
    request = load_json(Path(args.request))
    ledger_path = Path(args.ledger)
    try:
        with durable_ledger_lock(ledger_path):
            ledger = _load_ledger(ledger_path)
            result = process_transition(command=request["command"], run=request["run"], current_artifact=request.get("current_artifact"), supporting_artifacts=request.get("supporting_artifacts"), quality_gate_runs=request.get("quality_gate_runs"), approval=request.get("approval"), predecessor_release=request.get("predecessor_release"), context=request.get("context"), idempotency_ledger=ledger, max_attempts=int(request.get("max_attempts", 3)))
            if result["ok"] and not result["replay"]:
                ledger[request["command"]["idempotency_key"]] = result["command_fingerprint"]
                _atomic_write(ledger_path, {"fingerprints": ledger})
            _atomic_write(Path(args.output), result)
    except LedgerLockContentionError as exc:
        print(exc, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
