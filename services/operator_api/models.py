"""HTTP-only Pydantic models for the local Operator API."""

from __future__ import annotations

from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator


CommandVerb: TypeAlias = Literal[
    "start", "request-revision", "request-input", "create-defect", "escalate",
    "request-waiver", "submit-for-gate", "approve", "complete", "reject", "resolve", "resume",
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


class CurrentRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    tenant_id: str = Field(pattern=r"^tenant-[a-z0-9][a-z0-9-]{2,63}$")
    project_id: str = Field(pattern=r"^project-[a-z0-9][a-z0-9-]{2,63}$")
    run_id: str = Field(pattern=r"^run-[a-z0-9][a-z0-9-]{2,63}$")
    step_id: Literal["0", "1", "1b", "1c", "2", "3", "4a", "4b"]
    expected_revision: int = Field(ge=1)


class CommandResult(BaseModel):
    """Stable response wrapper for accepted or replayed commands."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    command_id: str
    correlation_id: str
    replay: bool
    event: dict[str, JsonValue]
    readback_url: str
    run: dict[str, JsonValue] | None = None


class ErrorEnvelope(BaseModel):
    """Path-free public rendering of a routed local failure."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str


ActionVerb: TypeAlias = Literal[
    "start", "submit-for-gate", "approve", "reject", "request-revision",
    "request-input", "escalate", "request-waiver", "resolve", "complete",
]


class ActionPayload(BaseModel):
    """Closed operator-authored details from which the server derives records."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reason: str = Field(default="Operator action is required.", min_length=1)
    instructions: str = Field(default="Apply the canonical action.", min_length=1)
    affected_sections: tuple[str, ...] = ("Canonical operator review",)
    immutable_constraints: tuple[str, ...] = ("Preserve the canonical run identity.",)
    options: tuple[str, ...] = ("Proceed", "Escalate")
    impacts: tuple[str, ...] = ("The current workflow step remains blocked.",)
    source_id: str | None = None
    source_type: Literal["operator_task", "blocker", "revision_request", "workflow_defect", "escalation"] | None = None


class ActionIntent(BaseModel):
    """The only client-supplied expression of a public admin action."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: ActionVerb
    tenant_id: str = Field(pattern=r"^tenant-[a-z0-9][a-z0-9-]{2,63}$")
    project_id: str = Field(pattern=r"^project-[a-z0-9][a-z0-9-]{2,63}$")
    run_id: str = Field(pattern=r"^run-[a-z0-9][a-z0-9-]{7,63}$")
    step_id: str = Field(pattern=r"^(0|1|1b|1c|2|3|3b|4a|4b)$")
    expected_revision: int = Field(ge=1)
    payload: ActionPayload = ActionPayload()

    @model_validator(mode="after")
    def require_resolve_source(self) -> ActionIntent:
        if self.action == "resolve" and (self.payload.source_type is None or self.payload.source_id is None):
            raise ValueError("resolve requires source_type and source_id")
        return self


class ActionBlocker(BaseModel):
    """A canonical lifecycle or schema blocker with a direct remediation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str
    remediation: str


class ActionPreview(BaseModel):
    """Read-only canonical consequences for an action intent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: ActionIntent
    allowed: bool
    blockers: tuple[ActionBlocker, ...]
    consequence: dict[str, JsonValue]
    preview_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class ActionConfirmRequest(BaseModel):
    """Explicit confirmation bound to one action intent and preview."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: ActionIntent
    preview_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    idempotency_key: str = Field(pattern=r"^idem-[a-z0-9][a-z0-9-]{7,127}$")
    confirmed: Literal[True]


class ActionConfirmResult(BaseModel):
    """Accepted or replayed action with server-loaded canonical projections."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    replay: bool
    preview_hash: str
    readback_urls: tuple[str, ...]
    canonical: dict[str, JsonValue]
