from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


_GATES = {"0": "GATE-0", "1": "GATE-1", "1b": "GATE-1B", "1c": "GATE-1C", "2": "GATE-2", "3": "GATE-3", "3b": "GATE-3B", "4a": "GATE-4A", "4b": "GATE-4B"}


class ReleaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    release_id: str = Field(pattern=r"^release-[a-z0-9][a-z0-9-]{7,63}$")
    tenant_id: str = Field(pattern=r"^tenant-[a-z0-9][a-z0-9-]{2,63}$")
    project_id: str = Field(pattern=r"^project-[a-z0-9][a-z0-9-]{2,63}$")
    run_id: str = Field(pattern=r"^run-[a-z0-9][a-z0-9-]{7,63}$")
    step_id: Literal["0", "1", "1b", "1c", "2", "3", "3b", "4a", "4b"]
    gate_id: str = Field(pattern=r"^GATE-(0|1|1B|1C|2|3|3B|4A|4B)$")
    artifact_id: str = Field(pattern=r"^artifact-[a-z0-9][a-z0-9-]{7,63}$")
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifact_revision: int = Field(ge=1)
    approval_id: str = Field(pattern=r"^approval-[a-z0-9][a-z0-9-]{7,63}$")
    policy_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    status: Literal["released"]
    released_at: datetime

    @model_validator(mode="after")
    def gate_matches_step(self) -> "ReleaseRecord":
        if self.released_at.tzinfo is None or self.released_at.utcoffset() is None:
            raise ValueError("release timestamp must include a timezone")
        if self.gate_id != _GATES[self.step_id]:
            raise ValueError("release gate does not match step")
        return self
