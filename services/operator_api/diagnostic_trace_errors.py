from __future__ import annotations

from typing import NoReturn

from .diagnostic_trace_types import DiagnosticTraceStoreError


def history_invalid() -> DiagnosticTraceStoreError:
    return DiagnosticTraceStoreError("ERROR_DIAGNOSTIC_TRACE_HISTORY_INVALID", "Diagnostic trace history is invalid.")


def raise_history_invalid() -> NoReturn:
    raise history_invalid()


def raise_unavailable() -> NoReturn:
    raise DiagnosticTraceStoreError("ERROR_DIAGNOSTIC_TRACE_UNAVAILABLE", "Diagnostic trace is unavailable.")


def raise_error(code: str, message: str) -> NoReturn:
    raise DiagnosticTraceStoreError(code, message)


def recovery_required() -> DiagnosticTraceStoreError:
    return DiagnosticTraceStoreError("ERROR_DIAGNOSTIC_RECOVERY_REQUIRED", "Diagnostic trace recovery is required.")


def error(code: str, message: str) -> DiagnosticTraceStoreError:
    return DiagnosticTraceStoreError(code, message)
