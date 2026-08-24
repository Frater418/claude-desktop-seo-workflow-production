"""Closed diagnostic trace records safe for local operator evidence."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .diagnostic_trace_validation import ACTION_IDENTIFIER, MAX_ACTIONS, REMEDIATION_IDENTIFIER, action_identifiers

_IDENTIFIER = r"^[a-z][a-z0-9-]{2,127}$"
_UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _utc_timestamp(value: str) -> str:
    if not _UTC_TIMESTAMP.fullmatch(value):
        raise ValueError("timestamp must be an exact UTC second timestamp")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("timestamp must be valid") from exc
    return value


def _relative_path(value: str) -> str:
    parts = value.split("/")
    if (
        not value
        or value.startswith("/")
        or "\\" in value
        or "?" in value
        or "#" in value
        or ":" in value
        or "%" in value
        or "\x00" in value
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ValueError("evidence path must be a safe repository-relative path")
    return value


class TraceEvidenceReference(BaseModel):
    """A safe pointer to a retained diagnostic artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    kind: Literal["screenshot", "artifact", "transition", "event", "readback", "browser_console", "network_failure"]
    relative_path: str = Field(min_length=1, max_length=512)

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        return _relative_path(value)

    @model_validator(mode="after")
    def validate_screenshot_path(self) -> TraceEvidenceReference:
        if self.kind == "screenshot" and not self.relative_path.endswith(".png"):
            raise ValueError("screenshot evidence must reference a .png file")
        return self


class DiagnosticTraceStart(BaseModel):
    """The immutable request used to open a local diagnostic trace."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: Literal["1.0.0"]
    tenant_id: str = Field(pattern=_IDENTIFIER)
    project_id: str = Field(pattern=_IDENTIFIER)
    run_id: str = Field(pattern=_IDENTIFIER)
    scenario_id: str = Field(pattern=_IDENTIFIER)
    source: Literal["automated", "manual"]
    created_at: str

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: str) -> str:
        return _utc_timestamp(value)


class DiagnosticTraceOperation(BaseModel):
    """One bounded observable operation in a diagnostic trace."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    operation_id: str = Field(pattern=_IDENTIFIER)
    occurred_at: str
    action: str = Field(pattern=ACTION_IDENTIFIER)
    route: str = Field(min_length=1, max_length=512)
    api_method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    api_status: int = Field(ge=100, le=599)
    error_code: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]{2,127}$")
    remediation: str | None = Field(default=None, pattern=REMEDIATION_IDENTIFIER)
    expected_actions: tuple[str, ...] = Field(strict=False, max_length=MAX_ACTIONS)
    rendered_actions: tuple[str, ...] = Field(strict=False, max_length=MAX_ACTIONS)
    disabled_actions: tuple[str, ...] = Field(strict=False, max_length=MAX_ACTIONS)
    evidence_references: tuple[TraceEvidenceReference, ...] = Field(strict=False)
    sequence: int | None = Field(default=None, ge=1)

    @field_validator("occurred_at")
    @classmethod
    def validate_occurred_at(cls, value: str) -> str:
        return _utc_timestamp(value)

    @field_validator("route")
    @classmethod
    def validate_route(cls, value: str) -> str:
        parts = value.split("/")
        if (
            not value.startswith("/")
            or value.startswith("//")
            or "://" in value
            or any(character in value for character in ("?", "#", "\\", "\x00", "%"))
            or any(part in {"", ".", ".."} for part in parts[1:])
        ):
            raise ValueError("route must be a safe route template")
        return value

    @field_validator("expected_actions", "rendered_actions", "disabled_actions")
    @classmethod
    def validate_actions(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return action_identifiers(value)

    @model_validator(mode="after")
    def validate_failure_details(self) -> DiagnosticTraceOperation:
        if (self.error_code is None) != (self.remediation is None):
            raise ValueError("error code and remediation must be provided together")
        return self


class DiagnosticTrace(BaseModel):
    """The current materialized view of one append-only trace."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: Literal["1.0.0"]
    trace_id: str = Field(pattern=r"^trace-[a-f0-9]{32}$")
    tenant_id: str = Field(pattern=_IDENTIFIER)
    project_id: str = Field(pattern=_IDENTIFIER)
    run_id: str = Field(pattern=_IDENTIFIER)
    scenario_id: str = Field(pattern=_IDENTIFIER)
    source: Literal["automated", "manual"]
    created_at: str
    status: Literal["active", "closed"]
    predecessor_trace_id: str | None = Field(default=None, pattern=r"^trace-[a-f0-9]{32}$")
    operations: tuple[DiagnosticTraceOperation, ...] = ()
    closed_at: str | None = None
    close_id: str | None = Field(default=None, pattern=_IDENTIFIER)
    last_successful_operation_id: str | None = Field(default=None, pattern=_IDENTIFIER)
    first_failing_operation_id: str | None = Field(default=None, pattern=_IDENTIFIER)

    @field_validator("created_at", "closed_at")
    @classmethod
    def validate_trace_timestamps(cls, value: str | None) -> str | None:
        return None if value is None else _utc_timestamp(value)

    @model_validator(mode="after")
    def validate_trace_closure(self) -> DiagnosticTrace:
        if self.status == "active" and any(value is not None for value in (self.closed_at, self.close_id, self.last_successful_operation_id, self.first_failing_operation_id)):
            raise ValueError("an active trace cannot contain terminal fields")
        if self.status == "closed" and (self.closed_at is None or self.close_id is None):
            raise ValueError("a closed trace requires its closed timestamp")
        return self


class DiagnosticTracePointer(BaseModel):
    """The small stable pointer consumed by direct diagnostic readers."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    trace_id: str = Field(pattern=r"^trace-[a-f0-9]{32}$")
    relative_run_path: str
    tenant_id: str = Field(pattern=_IDENTIFIER)
    project_id: str = Field(pattern=_IDENTIFIER)
    run_id: str = Field(pattern=_IDENTIFIER)
    scenario_id: str = Field(pattern=_IDENTIFIER)
    status: Literal["active", "closed"]

    @field_validator("relative_run_path")
    @classmethod
    def validate_run_path(cls, value: str) -> str:
        return _relative_path(value)


class DiagnosticTraceIndexEntry(DiagnosticTracePointer):
    """An immutable index entry written only after a trace closes."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    status: Literal["closed"]
    closed_at: str
    predecessor_trace_id: str | None = Field(default=None, pattern=r"^trace-[a-f0-9]{32}$")
    last_successful_operation_id: str | None = Field(default=None, pattern=_IDENTIFIER)
    first_failing_operation_id: str | None = Field(default=None, pattern=_IDENTIFIER)

    @field_validator("closed_at")
    @classmethod
    def validate_closed_at(cls, value: str) -> str:
        return _utc_timestamp(value)


class DiagnosticTraceStartRecord(BaseModel):
    """The first JSONL record for a trace."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    record_type: Literal["trace_start"]
    trace: DiagnosticTrace


class DiagnosticTraceOperationRecord(BaseModel):
    """An ordered operation JSONL record."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    record_type: Literal["operation"]
    operation: DiagnosticTraceOperation


class DiagnosticTraceCloseRecord(BaseModel):
    """The single terminal JSONL record for a closed trace."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    record_type: Literal["trace_closed"]
    trace_id: str = Field(pattern=r"^trace-[a-f0-9]{32}$")
    close_id: str = Field(pattern=_IDENTIFIER)
    closed_at: str
    last_successful_operation_id: str | None = Field(default=None, pattern=_IDENTIFIER)
    first_failing_operation_id: str | None = Field(default=None, pattern=_IDENTIFIER)

    @field_validator("closed_at")
    @classmethod
    def validate_closed_at(cls, value: str) -> str:
        return _utc_timestamp(value)
