"""Contained append-only Workflow Event V2 persistence."""

from __future__ import annotations

import copy
import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterator

from jsonschema import Draft202012Validator, FormatChecker

from .models import JsonValue

EVENTS_RELATIVE_PATH: Final = Path("v2/operator/events/events.jsonl")


class EventStoreError(RuntimeError):
    """Stable failure returned by the event-store boundary."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


@dataclass(frozen=True, slots=True)
class AppendResult:
    """An appended or idempotently replayed event."""

    event: dict[str, JsonValue]
    replay: bool


class EventStore:
    """One contained JSONL stream protected by a create-only portable lock."""

    def __init__(self, workspace: Path, event_schema: dict[str, JsonValue]) -> None:
        self._workspace = self._resolve_workspace(workspace)
        Draft202012Validator.check_schema(event_schema)
        self._validator = Draft202012Validator(event_schema, format_checker=FormatChecker())

    @classmethod
    def from_repository_root(cls, root: Path, workspace: Path) -> EventStore:
        schema_path = root / "standards/integrations/workflow-event-v2.schema.json"
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise EventStoreError("ERROR_DOMAIN_CONTRACT_FILE_MISSING", "Workflow Event V2 schema is unavailable.") from exc
        if not isinstance(schema, dict):
            raise EventStoreError("ERROR_CONTEXT_SCHEMA_INVALID", "Workflow Event V2 schema is invalid.")
        return cls(workspace, schema)

    def append(self, event: dict[str, JsonValue]) -> AppendResult:
        canonical = self._canonical_event(event)
        path = self._event_path()
        with self._lock(path):
            history = self._history(path)
            for existing in history:
                if existing["event_id"] == event["event_id"]:
                    if existing["idempotency_key"] == event["idempotency_key"] and self._canonical_event(existing) == canonical:
                        return AppendResult(copy.deepcopy(existing), True)
                    raise EventStoreError("ERROR_CONTEXT_SOURCE_INVALID", "Event history contains a duplicate event identity.")
                if existing["idempotency_key"] == event["idempotency_key"]:
                    if self._canonical_event(existing) == canonical:
                        return AppendResult(copy.deepcopy(existing), True)
                    raise EventStoreError("ERR_IDEMPOTENCY_CONFLICT", "Idempotency key was already used for a different event.")
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("ab") as stream:
                stream.write(canonical + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
        return AppendResult(copy.deepcopy(event), False)

    def history(self) -> list[dict[str, JsonValue]]:
        path = self._event_path()
        with self._lock(path):
            return copy.deepcopy(self._history(path))

    def validate_history(self) -> None:
        path = self._event_path()
        with self._lock(path):
            self._history(path)

    def _canonical_event(self, event: dict[str, JsonValue]) -> bytes:
        errors = sorted(self._validator.iter_errors(event), key=lambda error: list(error.absolute_path))
        if errors:
            raise EventStoreError("ERROR_CONTEXT_SCHEMA_INVALID", "Workflow event does not satisfy Event V2.")
        try:
            return json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise EventStoreError("ERROR_CONTEXT_SCHEMA_INVALID", "Workflow event cannot be canonically encoded.") from exc

    def _history(self, path: Path) -> list[dict[str, JsonValue]]:
        if not path.exists():
            return []
        try:
            payload = path.read_bytes()
            text = payload.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise EventStoreError("ERROR_CONTEXT_SOURCE_INVALID", "Workflow event history cannot be read.") from exc
        if text and not text.endswith("\n"):
            raise EventStoreError("ERROR_CONTEXT_SOURCE_INVALID", "Workflow event history has a partial tail.")
        records: list[dict[str, JsonValue]] = []
        event_ids: set[str] = set()
        for line in text.splitlines():
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EventStoreError("ERROR_CONTEXT_SOURCE_INVALID", "Workflow event history contains malformed JSON.") from exc
            if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
                raise EventStoreError("ERROR_CONTEXT_SOURCE_INVALID", "Workflow event history contains an invalid record.")
            record = dict(value)
            self._canonical_event(record)
            event_id = record.get("event_id")
            if not isinstance(event_id, str) or event_id in event_ids:
                raise EventStoreError("ERROR_CONTEXT_SOURCE_INVALID", "Workflow event history contains a duplicate event identity.")
            event_ids.add(event_id)
            records.append(record)
        return records

    def _event_path(self) -> Path:
        path = self._workspace / EVENTS_RELATIVE_PATH
        self._reject_unsafe_components(path)
        try:
            path.resolve(strict=False).relative_to(self._workspace)
        except ValueError as exc:
            raise EventStoreError("ERROR_OUTPUT_PATH_ESCAPE", "Event store path escapes the configured workspace.") from exc
        return path

    @contextmanager
    def _lock(self, path: Path) -> Iterator[None]:
        lock_path = path.with_suffix(path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        created = False
        try:
            with lock_path.open("x", encoding="utf-8"):
                created = True
                yield
        except FileExistsError as exc:
            raise EventStoreError("ERROR_TRANSITION_LEDGER_LOCKED", "Event store writer lock is active.") from exc
        finally:
            if created:
                lock_path.unlink()

    @staticmethod
    def _resolve_workspace(workspace: Path) -> Path:
        try:
            root = workspace.resolve(strict=True)
        except OSError as exc:
            raise EventStoreError("ERROR_OUTPUT_ROOT_INVALID", "Configured workspace is inaccessible.") from exc
        if not root.is_dir() or workspace.is_symlink():
            raise EventStoreError("ERROR_OUTPUT_ROOT_INVALID", "Configured workspace is not a safe directory.")
        return root

    def _reject_unsafe_components(self, path: Path) -> None:
        current = self._workspace
        for component in path.relative_to(self._workspace).parts:
            current = current / component
            if current.exists() and (current.is_symlink() or current.resolve() != current.absolute()):
                raise EventStoreError("ERROR_OUTPUT_PATH_ESCAPE", "Event store path traverses a link or reparse point.")
