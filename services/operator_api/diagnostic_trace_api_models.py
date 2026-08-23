"""Public allowlisted request and response contracts for diagnostic writes."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .diagnostic_trace_models import DiagnosticTrace, DiagnosticTraceOperation, _IDENTIFIER, _utc_timestamp


class DiagnosticTraceCloseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    close_id: str = Field(pattern=_IDENTIFIER)
    closed_at: str

    @field_validator("closed_at")
    @classmethod
    def _validate_closed_at(cls, value: str) -> str:
        return _utc_timestamp(value)


class DiagnosticTraceStartResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    trace_id: str
    tenant_id: str
    project_id: str
    run_id: str
    scenario_id: str
    source: Literal["automated", "manual"]
    created_at: str
    status: Literal["active"]
    replay: bool

    @classmethod
    def from_trace(cls, trace: DiagnosticTrace, replay: bool) -> DiagnosticTraceStartResponse:
        return cls(**trace.model_dump(include={"trace_id", "tenant_id", "project_id", "run_id", "scenario_id", "source", "created_at", "status"}), replay=replay)


class DiagnosticTraceEntryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    trace_id: str
    operation_id: str
    sequence: int
    replay: bool

    @classmethod
    def from_operation(cls, trace_id: str, operation: DiagnosticTraceOperation, replay: bool) -> DiagnosticTraceEntryResponse:
        if operation.sequence is None:
            raise ValueError("Recorded diagnostic trace operations require a sequence.")
        return cls(trace_id=trace_id, operation_id=operation.operation_id, sequence=operation.sequence, replay=replay)


class DiagnosticTraceCloseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    trace_id: str
    status: Literal["closed"]
    close_id: str
    closed_at: str
    last_successful_operation_id: str | None
    first_failing_operation_id: str | None
    replay: bool

    @classmethod
    def from_trace(cls, trace: DiagnosticTrace, replay: bool) -> DiagnosticTraceCloseResponse:
        if trace.close_id is None or trace.closed_at is None:
            raise ValueError("Closed diagnostic trace requires close identity.")
        return cls(**trace.model_dump(include={"trace_id", "status", "close_id", "closed_at", "last_successful_operation_id", "first_failing_operation_id"}), replay=replay)
