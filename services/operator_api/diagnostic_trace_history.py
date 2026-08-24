"""Read and derive canonical diagnostic trace history."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Final, NoReturn

from pydantic import BaseModel, ValidationError

from .diagnostic_trace_io import DiagnosticTraceStorage, DiagnosticTraceStorageError
from .diagnostic_trace_models import (
    DiagnosticTrace,
    DiagnosticTraceCloseRecord,
    DiagnosticTraceIndexEntry,
    DiagnosticTraceOperation,
    DiagnosticTraceOperationRecord,
    DiagnosticTracePointer,
    DiagnosticTraceStartRecord,
)

_TRACE_ID: Final = re.compile(r"^trace-[a-f0-9]{32}$")
_RUNS: Final = Path("runs")


class DiagnosticTraceHistory:
    """Validate immutable trace files through one typed failure boundary."""

    def __init__(self, storage: DiagnosticTraceStorage, invalid: Callable[[], NoReturn], unavailable: Callable[[], NoReturn]) -> None:
        self._storage = storage
        self._invalid = invalid
        self._unavailable = unavailable

    def trace_for(self, trace_id: str) -> tuple[DiagnosticTrace, Path]:
        if not _TRACE_ID.fullmatch(trace_id):
            self._invalid()
        runs = self._storage.member(_RUNS, directory=True)
        try:
            paths = tuple(path for path in runs.iterdir() if path.name.endswith(f"_{trace_id}.jsonl"))
        except FileNotFoundError:
            self._unavailable()
        except OSError:
            self._invalid()
        if not paths:
            self._unavailable()
        if len(paths) != 1:
            self._invalid()
        path = paths[0].relative_to(self._storage.root)
        return self.trace(path), path

    def trace(self, path: Path) -> DiagnosticTrace:
        lines = self.lines(path)
        start = self.parse(lines[0], DiagnosticTraceStartRecord).trace
        if start.status != "active" or start.operations or any(value is not None for value in (start.closed_at, start.last_successful_operation_id, start.first_failing_operation_id)):
            self._invalid()
        operations: list[DiagnosticTraceOperation] = []
        terminal: DiagnosticTraceCloseRecord | None = None
        for line in lines[1:]:
            if terminal is not None:
                self._invalid()
            record_type = self.record_type(line)
            if record_type == "operation":
                operation = self.parse(line, DiagnosticTraceOperationRecord).operation
                if operation.sequence != len(operations) + 1 or any(item.operation_id == operation.operation_id for item in operations):
                    self._invalid()
                operations.append(operation)
            elif record_type == "trace_closed":
                terminal = self.parse(line, DiagnosticTraceCloseRecord)
            else:
                self._invalid()
        if terminal is None:
            return start.model_copy(update={"operations": tuple(operations)})
        closed = start.model_copy(update={"operations": tuple(operations), "status": "closed", "closed_at": terminal.closed_at, "close_id": terminal.close_id, "last_successful_operation_id": terminal.last_successful_operation_id, "first_failing_operation_id": terminal.first_failing_operation_id})
        if terminal.trace_id != closed.trace_id or terminal.last_successful_operation_id != self.last_success(closed.operations) or terminal.first_failing_operation_id != self.first_failure(closed.operations):
            self._invalid()
        return closed

    def current(self, path: Path) -> DiagnosticTrace:
        pointer = self.parse(self.single_line(path), DiagnosticTracePointer)
        trace = self.trace(Path(pointer.relative_run_path))
        if pointer != self.pointer(trace, Path(pointer.relative_run_path)):
            self._invalid()
        return trace

    def index_entries(self, path: Path) -> tuple[DiagnosticTraceIndexEntry, ...]:
        if not self._storage.exists(path):
            return ()
        entries = tuple(self.parse(line, DiagnosticTraceIndexEntry) for line in self.lines(path))
        if len({entry.trace_id for entry in entries}) != len(entries):
            self._invalid()
        return entries

    def index_entry(self, trace: DiagnosticTrace, path: Path) -> DiagnosticTraceIndexEntry:
        if trace.closed_at is None:
            self._invalid()
        return DiagnosticTraceIndexEntry(**self.pointer(trace, path).model_dump(), closed_at=trace.closed_at, predecessor_trace_id=trace.predecessor_trace_id, last_successful_operation_id=trace.last_successful_operation_id, first_failing_operation_id=trace.first_failing_operation_id)

    def pointer(self, trace: DiagnosticTrace, path: Path) -> DiagnosticTracePointer:
        return DiagnosticTracePointer(trace_id=trace.trace_id, relative_run_path=path.as_posix(), tenant_id=trace.tenant_id, project_id=trace.project_id, run_id=trace.run_id, scenario_id=trace.scenario_id, status=trace.status)

    def read(self, path: Path) -> bytes:
        try:
            return self._storage.read(path)
        except DiagnosticTraceStorageError:
            self._invalid()

    def lines(self, path: Path) -> tuple[bytes, ...]:
        try:
            return self._storage.lines(path)
        except DiagnosticTraceStorageError:
            self._invalid()

    def single_line(self, path: Path) -> bytes:
        lines = self.lines(path)
        if len(lines) != 1:
            self._invalid()
        return lines[0]

    def parse(self, payload: bytes, model: type[BaseModel]) -> BaseModel:
        try:
            return model.model_validate_json(payload)
        except ValidationError:
            self._invalid()

    def record_type(self, payload: bytes) -> str:
        try:
            value = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._invalid()
        if not isinstance(value, dict) or not isinstance(value.get("record_type"), str):
            self._invalid()
        return value["record_type"]

    @staticmethod
    def last_success(operations: tuple[DiagnosticTraceOperation, ...]) -> str | None:
        matches = tuple(item.operation_id for item in operations if item.error_code is None and item.api_status < 400)
        return matches[-1] if matches else None

    @staticmethod
    def first_failure(operations: tuple[DiagnosticTraceOperation, ...]) -> str | None:
        return next((item.operation_id for item in operations if item.error_code is not None or item.api_status >= 400), None)
