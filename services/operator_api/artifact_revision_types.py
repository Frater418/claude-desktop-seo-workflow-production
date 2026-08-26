from __future__ import annotations

import hashlib
import json
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from .provider_outputs import ProviderOutput, ProviderOutputSet


ARTIFACT_ID_PATTERN: Final = r"^artifact-[a-z0-9][a-z0-9-]{7,63}$"


class ArtifactIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_id: str
    tenant_id: str
    project_id: str
    run_id: str
    step_id: str
    revision: int = Field(ge=1)


class ArtifactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    tenant_id: str
    project_id: str
    run_id: str
    step_id: str
    revision: int = Field(ge=1)
    input_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parent_artifact_ids: tuple[str, ...] = ()
    contract_version: str = "1.0.0"
    producer_version: str = "provider-output-set"
    storage_key: str
    created_at: str


class ArtifactRevisionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    records: tuple[ArtifactRecord, ...]
    quality_gate_runs: tuple[dict[str, JsonValue], ...] = ()
    derived_views: tuple["DerivedView", ...] = ()


class ArtifactRevisionListResponse(BaseModel):
    """Closed canonical revision list for one run-step identity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    artifacts: tuple[ArtifactRecord, ...]


class ArtifactContentResponse(BaseModel):
    """Exact immutable artifact bytes encoded for JSON transport."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact: ArtifactRecord
    content_base64: str


class ArtifactDiffRequest(BaseModel):
    """Two canonical artifact identities selected for a read-only comparison."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    left_artifact_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    right_artifact_id: str = Field(pattern=ARTIFACT_ID_PATTERN)


class ArtifactDiffResponse(BaseModel):
    """Deterministic unified text diff between two immutable artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    left_artifact: ArtifactRecord
    right_artifact: ArtifactRecord
    unified_diff: str


class DerivedView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9.-]{0,127}$")
    content: str


class ArtifactTransaction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: str
    project_id: str
    run_id: str
    step_id: str
    idempotency_key: str
    payload_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    target_revision: int = Field(ge=1)
    next_run: dict[str, JsonValue]
    records: tuple[ArtifactRecord, ...]
    contents: tuple[bytes, ...]
    quality_gate_runs: tuple[dict[str, JsonValue], ...] = ()
    derived_views: tuple[DerivedView, ...] = ()


def build_artifact_record(output: ProviderOutput, package_input_hash: str, parents: tuple[str, ...]) -> ArtifactRecord:
    artifact_id = artifact_id_for(ArtifactIdentity(contract_id=output.contract_id, tenant_id=output.tenant_id, project_id=output.project_id, run_id=output.run_id, step_id=output.step_id, revision=output.target_revision))
    return ArtifactRecord(artifact_id=artifact_id, tenant_id=output.tenant_id, project_id=output.project_id, run_id=output.run_id, step_id=output.step_id, revision=output.target_revision, input_hash=package_input_hash, content_sha256=output.content_sha256, parent_artifact_ids=parents, storage_key=f"tenants/{output.tenant_id}/projects/{output.project_id}/runs/{output.run_id}/artifacts/{artifact_id}/content.md", created_at=output.created_at.isoformat().replace("+00:00", "Z"))


def artifact_id_for(identity: ArtifactIdentity) -> str:
    source = "|".join((identity.contract_id, identity.tenant_id, identity.project_id, identity.run_id, identity.step_id, str(identity.revision)))
    return f"artifact-{hashlib.sha256(source.encode()).hexdigest()[:16]}"


def output_set_payload_sha256(output_set: ProviderOutputSet, package_input_hash: str) -> str:
    payload = {"package_input_hash": package_input_hash, "outputs": [output.model_dump(mode="json") for output in output_set.outputs]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
