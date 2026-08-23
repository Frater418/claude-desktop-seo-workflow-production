"""Typed durable intents for diagnostic trace mutations."""

from __future__ import annotations

from typing import Final, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from .diagnostic_trace_models import (
    DiagnosticTrace,
    DiagnosticTraceCloseRecord,
    DiagnosticTraceIndexEntry,
    DiagnosticTracePointer,
    DiagnosticTraceStart,
    DiagnosticTraceStartRecord,
)


class DiagnosticTraceCreateIntent(BaseModel):
    """The exact create records that recovery may materialize."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: Literal["1.0.0"]
    operation: Literal["create"]
    start: DiagnosticTraceStart
    relative_run_path: str
    start_record: DiagnosticTraceStartRecord
    current_pointer: DiagnosticTracePointer


class DiagnosticTraceCloseIntent(BaseModel):
    """The exact close records that recovery may materialize."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: Literal["1.0.0"]
    operation: Literal["close"]
    trace_id: str
    close_id: str
    closed_at: str
    relative_run_path: str
    terminal_record: DiagnosticTraceCloseRecord
    index_entry: DiagnosticTraceIndexEntry
    current_pointer: DiagnosticTracePointer


DiagnosticTracePendingIntent: TypeAlias = DiagnosticTraceCreateIntent | DiagnosticTraceCloseIntent
_PENDING_ADAPTER: Final = TypeAdapter(DiagnosticTracePendingIntent)


def parse_pending_intent(payload: bytes) -> DiagnosticTracePendingIntent:
    """Parse one canonical pending sidecar into its typed operation."""
    try:
        return _PENDING_ADAPTER.validate_json(payload)
    except ValidationError as exc:
        raise DiagnosticTracePendingIntentError from exc


class DiagnosticTracePendingIntentError(RuntimeError):
    """Raised when a pending sidecar does not match the strict contract."""
