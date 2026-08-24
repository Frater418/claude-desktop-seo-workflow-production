from __future__ import annotations

from enum import StrEnum


class DiagnosticTraceFailureBoundary(StrEnum):
    PENDING_CREATE = "pending_create"
    START_RECORD = "start_record"
    CREATE_CURRENT_REPLACE = "create_current_replace"
    PENDING_CLOSE_INTENT = "pending_close_intent"
    TERMINAL_RECORD = "terminal_record"
    INDEX_APPEND = "index_append"
    CLOSE_CURRENT_REPLACE = "close_current_replace"


class DiagnosticTraceStoreError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"
