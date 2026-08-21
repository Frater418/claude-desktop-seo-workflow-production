from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


class OwnedFileLockError(RuntimeError):
    pass


class _TakeoverCoordinationUnavailable(RuntimeError):
    pass


@dataclass(slots=True)
class OwnedFileLock:
    path: Path
    grace_seconds: float = 1.0
    token: str = ""

    def __enter__(self) -> OwnedFileLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.token = uuid.uuid4().hex
        for _ in range(2):
            temporary = self._metadata_temp()
            try:
                os.link(temporary, self.path)
                return self
            except FileExistsError:
                if not self._recover_dead_owner():
                    raise OwnedFileLockError("lock is active") from None
            finally:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass
        raise OwnedFileLockError("lock is active")

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        try:
            metadata = self._metadata()
            if metadata.get("token") != self.token:
                raise OwnedFileLockError("lock ownership changed before release")
            self.path.unlink()
        except FileNotFoundError:
            return

    def _metadata_temp(self) -> Path:
        descriptor, name = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"schema_version": 1, "pid": os.getpid(), "hostname": socket.gethostname(), "token": self.token}, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        return Path(name)

    def _recover_dead_owner(self) -> bool:
        self._before_takeover_coordination()
        try:
            with self._takeover_coordination():
                return self._remove_dead_owner()
        except _TakeoverCoordinationUnavailable:
            return False

    def _remove_dead_owner(self) -> bool:
        try:
            metadata = self._metadata()
            age = time.time() - self.path.stat().st_mtime
        except (OSError, OwnedFileLockError):
            return False
        if age < self.grace_seconds or metadata.get("hostname") != socket.gethostname() or not isinstance(metadata.get("pid"), int):
            return False
        try:
            os.kill(metadata["pid"], 0)
        except ProcessLookupError:
            if self._metadata().get("token") != metadata.get("token"):
                return False
            try:
                self.path.unlink()
                return True
            except FileNotFoundError:
                return False
        except PermissionError:
            return False
        return False

    def _before_takeover_coordination(self) -> None:
        return

    @contextmanager
    def _takeover_coordination(self) -> Iterator[None]:
        coordination = self.path.with_name(f".{self.path.name}.takeover")
        with coordination.open("a+b") as stream:
            if sys.platform == "win32":
                import msvcrt

                stream.seek(0)
                if not stream.read(1):
                    stream.write(b"\0")
                    stream.flush()
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                try:
                    import fcntl
                except ModuleNotFoundError as exc:
                    raise _TakeoverCoordinationUnavailable from exc

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def _metadata(self) -> dict[str, str | int]:
        return self._metadata_at(self.path)

    @staticmethod
    def _metadata_at(path: Path) -> dict[str, str | int]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OwnedFileLockError("lock metadata is incomplete") from exc
        if not isinstance(value, dict) or value.get("schema_version") != 1 or not isinstance(value.get("pid"), int) or not isinstance(value.get("hostname"), str) or not isinstance(value.get("token"), str):
            raise OwnedFileLockError("lock metadata is invalid")
        return value
