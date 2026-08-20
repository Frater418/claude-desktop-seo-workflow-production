"""HTTP-only Pydantic models for the local Operator API."""

from __future__ import annotations

from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, JsonValue, model_validator


CommandVerb: TypeAlias = Literal[
    "start", "request-revision", "request-input", "create-defect", "escalate",
    "request-waiver", "approve", "reject", "resolve", "resume",
]


class CommandRequest(BaseModel):
    """Closed transport shape for a single versioned command."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    command: CommandVerb
    command_id: str
    correlation_id: str
    idempotency_key: str
    tenant_id: str
    project_id: str
    run_id: str
    step_id: str
    expected_revision: int
    transition_command: dict[str, JsonValue] | None = None
    record_type: str | None = None
    operator_record: dict[str, JsonValue] | None = None
    event: dict[str, JsonValue]

    @model_validator(mode="after")
    def require_one_command_shape(self) -> CommandRequest:
        has_transition = self.transition_command is not None
        has_record = self.operator_record is not None and self.record_type is not None
        if has_transition == has_record:
            raise ValueError("exactly one transition command or typed operator record is required")
        return self


class DataEnvelope(BaseModel):
    """Stable response wrapper for a projection or command result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    data: JsonValue


class CommandResult(BaseModel):
    """Stable response wrapper for accepted or replayed commands."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    command_id: str
    correlation_id: str
    replay: bool
    event: dict[str, JsonValue]
    run: dict[str, JsonValue] | None = None


class ErrorEnvelope(BaseModel):
    """Path-free public rendering of a routed local failure."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str
