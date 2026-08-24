"""Canonical durable file operations for diagnostic trace storage."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Final

from pydantic import JsonValue


class DiagnosticTraceStorageError(RuntimeError):
    """Raised when diagnostic trace storage cannot be safely accessed."""


class DiagnosticTraceStorage:
    """Own safe paths and exact canonical JSONL bytes below one root."""

    def __init__(self, root: Path) -> None:
        self.root = self._resolve_root(root)

    def exists(self, relative_path: Path) -> bool:
        return self.member(relative_path).exists()

    def read(self, relative_path: Path) -> bytes:
        path = self.member(relative_path, file=True)
        try:
            return path.read_bytes()
        except OSError as exc:
            raise DiagnosticTraceStorageError from exc

    def lines(self, relative_path: Path) -> tuple[bytes, ...]:
        payload = self.read(relative_path)
        if not payload.endswith(b"\n"):
            raise DiagnosticTraceStorageError
        lines = tuple(payload[:-1].split(b"\n"))
        if not lines or any(not line or self.canonical_json(line) != line for line in lines):
            raise DiagnosticTraceStorageError
        return lines

    def append(self, relative_path: Path, payload: bytes) -> None:
        path = self.member(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.member(relative_path)
        descriptor = -1
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0), 0o600)
            written = os.write(descriptor, payload)
            if written != len(payload):
                raise DiagnosticTraceStorageError
            os.fsync(descriptor)
        except OSError as exc:
            raise DiagnosticTraceStorageError from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    def replace(self, relative_path: Path, payload: bytes) -> None:
        path = self.member(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.member(relative_path)
        descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        temporary = Path(name)
        try:
            written = os.write(descriptor, payload)
            if written != len(payload):
                raise DiagnosticTraceStorageError
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1
            os.replace(temporary, path)
        except OSError as exc:
            raise DiagnosticTraceStorageError from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

    def remove(self, relative_path: Path) -> None:
        try:
            self.member(relative_path, file=True).unlink()
        except OSError as exc:
            raise DiagnosticTraceStorageError from exc

    def member(self, relative_path: Path, *, directory: bool = False, file: bool = False) -> Path:
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise DiagnosticTraceStorageError
        path = self.root / relative_path
        current = self.root
        for index, part in enumerate(relative_path.parts):
            current = current / part
            try:
                mode = current.lstat().st_mode
            except FileNotFoundError:
                continue
            final = index == len(relative_path.parts) - 1
            if stat.S_ISLNK(mode) or (not final and not stat.S_ISDIR(mode)):
                raise DiagnosticTraceStorageError
            if final and directory and not stat.S_ISDIR(mode):
                raise DiagnosticTraceStorageError
            if final and file and not stat.S_ISREG(mode):
                raise DiagnosticTraceStorageError
        return path

    @staticmethod
    def canonical(value: JsonValue) -> bytes:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")

    @classmethod
    def canonical_json(cls, payload: bytes) -> bytes:
        try:
            return cls.canonical(json.loads(payload))
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise DiagnosticTraceStorageError from exc

    @staticmethod
    def _resolve_root(root: Path) -> Path:
        try:
            absolute = root.absolute()
            resolved = absolute.resolve(strict=True)
            mode = resolved.lstat().st_mode
        except OSError as exc:
            raise DiagnosticTraceStorageError from exc
        if absolute != resolved or not stat.S_ISDIR(mode):
            raise DiagnosticTraceStorageError
        return resolved
