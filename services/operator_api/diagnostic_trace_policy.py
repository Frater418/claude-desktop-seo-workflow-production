"""Capacity rules for durable diagnostic trace mutations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import NoReturn


@dataclass(frozen=True, slots=True)
class DiagnosticTraceLimits:
    max_closed_runs: int = 100
    max_operations_per_run: int = 1_000
    max_run_bytes: int = 5 * 1024 * 1024
    max_index_bytes: int = 1 * 1024 * 1024
    max_serialized_record_bytes: int = 64 * 1024
    close_reserve_bytes: int = 4 * 1024
    index_reserve_bytes: int = 4 * 1024


class DiagnosticTracePolicy:
    """Apply approved limits before any durable mutation."""

    def __init__(self, limits: DiagnosticTraceLimits, error: Callable[[str, str], NoReturn]) -> None:
        self._limits = limits
        self._error = error

    def create(self, *, path_exists: bool, closed_count: int, index_bytes: bytes, start_record: bytes) -> None:
        if path_exists:
            self._error("ERROR_DIAGNOSTIC_TRACE_CONFLICT", "Diagnostic trace identity already exists.")
        if closed_count >= self._limits.max_closed_runs:
            self._error("ERROR_DIAGNOSTIC_RETENTION_LIMIT", "Diagnostic trace retention limit reached.")
        if len(index_bytes) + self._limits.index_reserve_bytes > self._limits.max_index_bytes:
            self._error("ERROR_DIAGNOSTIC_INDEX_SIZE_LIMIT", "Diagnostic trace index size limit reached.")
        self.record(start_record)
        if len(start_record) + self._limits.close_reserve_bytes > self._limits.max_run_bytes:
            self._error("ERROR_DIAGNOSTIC_RUN_SIZE_LIMIT", "Diagnostic trace run size limit reached.")

    def close(self, *, run_bytes: bytes, index_bytes: bytes, terminal_record: bytes, index_record: bytes) -> None:
        self.record(terminal_record)
        self.record(index_record)
        if len(run_bytes) + len(terminal_record) > self._limits.max_run_bytes:
            self._error("ERROR_DIAGNOSTIC_RUN_SIZE_LIMIT", "Diagnostic trace run size limit reached.")
        if len(index_bytes) + len(index_record) > self._limits.max_index_bytes:
            self._error("ERROR_DIAGNOSTIC_INDEX_SIZE_LIMIT", "Diagnostic trace index size limit reached.")

    def record(self, payload: bytes) -> None:
        if len(payload) > self._limits.max_serialized_record_bytes:
            self._error("ERROR_DIAGNOSTIC_RECORD_SIZE_LIMIT", "Diagnostic trace record size limit reached.")

    @staticmethod
    def compact(timestamp: str) -> str:
        return timestamp.replace("-", "").replace(":", "")
