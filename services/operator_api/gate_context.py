from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, JsonValue


EvidenceId: TypeAlias = Annotated[str, Field(pattern=r"^evidence-[a-z0-9][a-z0-9-]{7,63}$")]
Sha256: TypeAlias = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
NonBlankString: TypeAlias = Annotated[str, Field(min_length=1, pattern=r".*\S.*")]
EvidenceClassification: TypeAlias = Literal["local_validation", "local_simulated", "external_report"]


class GateEvidenceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    evidence_id: EvidenceId
    tool: NonBlankString
    report_sha256: Sha256
    subject_content_sha256: Sha256
    classification: EvidenceClassification
    source: NonBlankString


class GateContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    site_status: Literal["existing_site", "non_existing_site"] | None = None
    production: bool = False
    configured_tools: tuple[str, ...] = Field(default_factory=tuple, strict=False)
    available_tools: tuple[str, ...] = Field(default_factory=tuple, strict=False)
    not_applicable_decisions: Mapping[str, Mapping[str, JsonValue]] = Field(default_factory=dict)
    evidence_by_gate: Mapping[str, Mapping[str, str | int | float | bool]]
    evidence_documents: tuple[GateEvidenceDocument, ...] = Field(default_factory=tuple, strict=False)
