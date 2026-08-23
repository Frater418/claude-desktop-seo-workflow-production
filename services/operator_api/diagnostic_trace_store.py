"""Bounded append-only diagnostic trace persistence."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from pydantic import BaseModel

from services.owned_file_lock import OwnedFileLock, OwnedFileLockError

from .diagnostic_trace_io import DiagnosticTraceStorage, DiagnosticTraceStorageError
from .diagnostic_trace_history import DiagnosticTraceHistory
from .diagnostic_trace_policy import DiagnosticTraceLimits, DiagnosticTracePolicy
from .diagnostic_trace_models import (
    DiagnosticTrace,
    DiagnosticTraceCloseRecord,
    DiagnosticTraceIndexEntry,
    DiagnosticTraceOperation,
    DiagnosticTraceOperationRecord,
    DiagnosticTracePointer,
    DiagnosticTraceStart,
    DiagnosticTraceStartRecord,
)
from .diagnostic_trace_recovery import (
    DiagnosticTraceCloseIntent,
    DiagnosticTraceCreateIntent,
    DiagnosticTracePendingIntent,
    DiagnosticTracePendingIntentError,
    parse_pending_intent,
)
from .diagnostic_trace_errors import error, history_invalid, raise_error, raise_history_invalid, raise_unavailable, recovery_required
from .diagnostic_trace_types import DiagnosticTraceFailureBoundary, DiagnosticTraceStoreError

_RUNS, _CURRENT, _INDEX, _PENDING, _LOCK = (Path("runs"), Path("current.json"), Path("index.jsonl"), Path("pending.json"), Path("locks/diagnostic-trace.lock"))


class DiagnosticTraceStore:
    _error = staticmethod(error)
    _history_invalid = staticmethod(history_invalid)
    _raise_error = staticmethod(raise_error)
    _raise_history_invalid = staticmethod(raise_history_invalid)
    _raise_unavailable = staticmethod(raise_unavailable)
    _recovery_required = staticmethod(recovery_required)

    def __init__(self, root: Path, *, limits: DiagnosticTraceLimits | None = None, failure_injector: Callable[[DiagnosticTraceFailureBoundary], None] | None = None) -> None:
        try:
            self._storage = DiagnosticTraceStorage(root)
        except DiagnosticTraceStorageError as exc:
            raise self._error("ERROR_DIAGNOSTIC_TRACE_ROOT_INVALID", "Diagnostic trace root is inaccessible.") from exc
        self._history = DiagnosticTraceHistory(self._storage, self._raise_history_invalid, self._raise_unavailable)
        self._limits = limits or DiagnosticTraceLimits()
        self._policy = DiagnosticTracePolicy(self._limits, self._raise_error)
        self._failure_injector = failure_injector
        self.replay = False

    def create(self, start: DiagnosticTraceStart) -> DiagnosticTrace:
        self.replay = False
        with self._locked():
            pending = self._pending()
            if pending is not None:
                match pending:
                    case DiagnosticTraceCreateIntent(start=stored_start):
                        if stored_start != start:
                            raise self._recovery_required()
                        self.replay = True
                        return self._resume_create(pending)
                    case _:
                        raise self._recovery_required()
            return self._begin_create(start, None)

    def append(self, trace_id: str, operation: DiagnosticTraceOperation) -> DiagnosticTraceOperation:
        self.replay = False
        with self._locked():
            self._require_no_pending()
            trace, path = self._history.trace_for(trace_id)
            if trace.status == "closed":
                raise self._error("ERROR_DIAGNOSTIC_TRACE_CLOSED", "Diagnostic trace is closed.")
            for recorded in trace.operations:
                if recorded.operation_id == operation.operation_id:
                    if recorded.model_copy(update={"sequence": None}) == operation.model_copy(update={"sequence": None}):
                        self.replay = True
                        return recorded
                    raise self._error("ERROR_DIAGNOSTIC_TRACE_CONFLICT", "Operation identity was reused with different content.")
            recorded = operation.model_copy(update={"sequence": len(trace.operations) + 1})
            payload = self._record_bytes(DiagnosticTraceOperationRecord(record_type="operation", operation=recorded))
            if len(trace.operations) >= self._limits.max_operations_per_run:
                raise self._error("ERROR_DIAGNOSTIC_OPERATION_LIMIT", "Diagnostic trace operation limit reached.")
            self._policy.record(payload)
            if len(self._read(path)) + len(payload) + self._limits.close_reserve_bytes > self._limits.max_run_bytes:
                raise self._error("ERROR_DIAGNOSTIC_RUN_SIZE_LIMIT", "Diagnostic trace run size limit reached.")
            self._append(path, payload)
            return recorded

    def close(self, trace_id: str, *, closed_at: str, close_id: str) -> DiagnosticTrace:
        self.replay = False
        with self._locked():
            pending = self._pending()
            if pending is not None:
                match pending:
                    case DiagnosticTraceCloseIntent(trace_id=stored_id, close_id=stored_close_id, closed_at=stored_at) if (stored_id, stored_close_id, stored_at) == (trace_id, close_id, closed_at):
                        self.replay = True
                        return self._resume_close(pending)
                    case _:
                        raise self._recovery_required()
            trace, path = self._history.trace_for(trace_id)
            if trace.status == "closed":
                if (trace.close_id, trace.closed_at) == (close_id, closed_at):
                    self.replay = True
                    return trace
                raise self._error("ERROR_DIAGNOSTIC_TRACE_CONFLICT", "Diagnostic trace close identity was reused with different content.")
            closed = trace.model_copy(update={"status": "closed", "closed_at": closed_at, "close_id": close_id, "last_successful_operation_id": self._history.last_success(trace.operations), "first_failing_operation_id": self._history.first_failure(trace.operations)})
            terminal = DiagnosticTraceCloseRecord(record_type="trace_closed", trace_id=trace_id, close_id=close_id, closed_at=closed_at, last_successful_operation_id=closed.last_successful_operation_id, first_failing_operation_id=closed.first_failing_operation_id)
            intent = DiagnosticTraceCloseIntent(schema_version="1.0.0", operation="close", trace_id=trace_id, close_id=close_id, closed_at=closed_at, relative_run_path=str(path), terminal_record=terminal, index_entry=self._history.index_entry(closed, path), current_pointer=self._history.pointer(closed, path))
            self._policy.close(run_bytes=self._read(path), index_bytes=self._index_bytes(), terminal_record=self._record_bytes(intent.terminal_record), index_record=self._record_bytes(intent.index_entry))
            self._replace(_PENDING, self._record_bytes(intent))
            self._inject(DiagnosticTraceFailureBoundary.PENDING_CLOSE_INTENT)
            return self._resume_close(intent)

    def retry(self, trace_id: str, *, started_at: str) -> DiagnosticTrace:
        with self._locked():
            self._require_no_pending()
            predecessor, _ = self._history.trace_for(trace_id)
            if predecessor.status != "closed":
                raise self._error("ERROR_DIAGNOSTIC_TRACE_STATE_INVALID", "Only a closed diagnostic trace can be retried.")
            start = DiagnosticTraceStart(schema_version=predecessor.schema_version, tenant_id=predecessor.tenant_id, project_id=predecessor.project_id, run_id=predecessor.run_id, scenario_id=predecessor.scenario_id, source=predecessor.source, created_at=started_at)
            return self._begin_create(start, predecessor.trace_id)

    def current(self) -> DiagnosticTrace:
        with self._locked():
            return self._history.current(_CURRENT)

    def trace(self, trace_id: str) -> DiagnosticTrace:
        with self._locked():
            trace, _ = self._history.trace_for(trace_id)
            return trace

    def index(self) -> tuple[DiagnosticTraceIndexEntry, ...]:
        with self._locked():
            self._require_no_pending()
            entries = self._history.index_entries(_INDEX)
            for entry in entries:
                trace = self._history.trace(Path(entry.relative_run_path))
                if entry != self._history.index_entry(trace, Path(entry.relative_run_path)):
                    raise self._history_invalid()
            return tuple(entries)

    def _begin_create(self, start: DiagnosticTraceStart, predecessor_trace_id: str | None) -> DiagnosticTrace:
        if self._storage.exists(_CURRENT):
            current = self._history.current(_CURRENT)
            if current.status == "active":
                if (current.schema_version, current.tenant_id, current.project_id, current.run_id, current.scenario_id, current.source, current.created_at) == (start.schema_version, start.tenant_id, start.project_id, start.run_id, start.scenario_id, start.source, start.created_at):
                    self.replay = True
                    return current
                raise self._error("ERROR_DIAGNOSTIC_TRACE_CONFLICT", "An active diagnostic trace already exists.")
        trace = DiagnosticTrace(**start.model_dump(), trace_id=f"trace-{uuid.uuid4().hex}", status="active", predecessor_trace_id=predecessor_trace_id)
        path = _RUNS / f"{DiagnosticTracePolicy.compact(start.created_at)}_{trace.trace_id}.jsonl"
        start_record = DiagnosticTraceStartRecord(record_type="trace_start", trace=trace)
        intent = DiagnosticTraceCreateIntent(schema_version="1.0.0", operation="create", start=start, relative_run_path=str(path), start_record=start_record, current_pointer=self._history.pointer(trace, path))
        self._policy.create(path_exists=self._storage.exists(path), closed_count=len(self._history.index_entries(_INDEX)), index_bytes=self._index_bytes(), start_record=self._record_bytes(intent.start_record))
        self._replace(_PENDING, self._record_bytes(intent))
        self._inject(DiagnosticTraceFailureBoundary.PENDING_CREATE)
        return self._resume_create(intent)

    def _resume_create(self, intent: DiagnosticTraceCreateIntent) -> DiagnosticTrace:
        path = Path(intent.relative_run_path)
        start_payload = self._record_bytes(intent.start_record)
        if self._storage.exists(path):
            if self._read(path) != start_payload:
                raise self._recovery_required()
        else:
            self._append(path, start_payload)
        self._inject(DiagnosticTraceFailureBoundary.START_RECORD)
        pointer_payload = self._record_bytes(intent.current_pointer)
        if self._storage.exists(_CURRENT):
            if self._read(_CURRENT) != pointer_payload:
                if self._history.current(_CURRENT).status != "closed":
                    raise self._recovery_required()
                self._replace(_CURRENT, pointer_payload)
        else:
            self._replace(_CURRENT, pointer_payload)
        self._inject(DiagnosticTraceFailureBoundary.CREATE_CURRENT_REPLACE)
        self._remove_pending()
        return intent.start_record.trace

    def _resume_close(self, intent: DiagnosticTraceCloseIntent) -> DiagnosticTrace:
        path = Path(intent.relative_run_path)
        terminal_payload = self._record_bytes(intent.terminal_record)
        existing = self._read(path)
        if not existing.endswith(terminal_payload):
            trace = self._history.trace(path)
            if trace.status == "closed":
                raise self._recovery_required()
            self._append(path, terminal_payload)
        self._inject(DiagnosticTraceFailureBoundary.TERMINAL_RECORD)
        index_payload = self._record_bytes(intent.index_entry)
        entries = self._history.index_entries(_INDEX)
        matches = [entry for entry in entries if entry.trace_id == intent.trace_id]
        if matches:
            if len(matches) != 1 or self._record_bytes(matches[0]) != index_payload:
                raise self._recovery_required()
        else:
            self._append(_INDEX, index_payload)
        self._inject(DiagnosticTraceFailureBoundary.INDEX_APPEND)
        pointer_payload = self._record_bytes(intent.current_pointer)
        if self._storage.exists(_CURRENT) and self._read(_CURRENT) != pointer_payload:
            active = self._history.pointer(self._history.trace(path).model_copy(update={"status": "active", "closed_at": None, "close_id": None, "last_successful_operation_id": None, "first_failing_operation_id": None}), path)
            if self._read(_CURRENT) != self._record_bytes(active):
                raise self._recovery_required()
            self._replace(_CURRENT, pointer_payload)
        elif not self._storage.exists(_CURRENT):
            self._replace(_CURRENT, pointer_payload)
        self._inject(DiagnosticTraceFailureBoundary.CLOSE_CURRENT_REPLACE)
        self._remove_pending()
        return self._history.trace(path)

    def _pending(self) -> DiagnosticTracePendingIntent | None:
        if not self._storage.exists(_PENDING):
            return None
        try:
            return parse_pending_intent(self._history.single_line(_PENDING))
        except DiagnosticTracePendingIntentError as exc:
            raise self._recovery_required() from exc

    def _require_no_pending(self) -> None:
        if self._pending() is not None:
            raise self._recovery_required()

    def _index_bytes(self) -> bytes:
        return self._history.read(_INDEX) if self._storage.exists(_INDEX) else b""

    def _read(self, path: Path) -> bytes:
        return self._history.read(path)

    def _append(self, path: Path, payload: bytes) -> None:
        try:
            self._storage.append(path, payload)
        except DiagnosticTraceStorageError as exc:
            raise self._error("ERROR_DIAGNOSTIC_TRACE_WRITE_FAILED", "Diagnostic trace cannot be written.") from exc

    def _replace(self, path: Path, payload: bytes) -> None:
        try:
            self._storage.replace(path, payload)
        except DiagnosticTraceStorageError as exc:
            raise self._error("ERROR_DIAGNOSTIC_TRACE_WRITE_FAILED", "Diagnostic trace cannot be written.") from exc

    def _remove_pending(self) -> None:
        try:
            self._storage.remove(_PENDING)
        except DiagnosticTraceStorageError as exc:
            raise self._error("ERROR_DIAGNOSTIC_TRACE_WRITE_FAILED", "Diagnostic trace cannot be written.") from exc

    @staticmethod
    def _record_bytes(record: BaseModel) -> bytes:
        return DiagnosticTraceStorage.canonical(record.model_dump(mode="json")) + b"\n"

    def _inject(self, boundary: DiagnosticTraceFailureBoundary) -> None:
        if self._failure_injector is not None:
            self._failure_injector(boundary)

    @contextmanager
    def _locked(self) -> Iterator[None]:
        try:
            with OwnedFileLock(self._storage.member(_LOCK), grace_seconds=0):
                yield
        except OwnedFileLockError as exc:
            raise self._error("ERROR_DIAGNOSTIC_TRACE_LOCKED", "Diagnostic trace writer lock is active.") from exc
