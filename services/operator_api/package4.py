from __future__ import annotations

import hashlib

from pydantic import BaseModel, ConfigDict, Field, JsonValue
from .repository import ProjectRepository


class ArtifactValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    revision: int = Field(ge=1)
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class ArtifactValidation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_id: str
    revision: int
    content_sha256: str
    valid: bool


class Package4Error(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def validate_artifact(repository: ProjectRepository, tenant_id: str, project_id: str, artifact_id: str, request: ArtifactValidationRequest) -> ArtifactValidation:
    record = next((item for item in repository.artifacts(tenant_id, project_id) if item.get("artifact_id") == artifact_id), None)
    if record is None:
        raise Package4Error("ERROR_DOMAIN_REFERENCE_UNKNOWN", "Artifact revision is unavailable.")
    if record.get("revision") != request.revision or record.get("content_sha256") != request.content_sha256:
        raise Package4Error("ERR_STALE_REVISION", "Artifact validation must bind the exact revision and hash.")
    if hashlib.sha256(repository.artifact_content_bytes(tenant_id, project_id, artifact_id)).hexdigest() != request.content_sha256:
        raise Package4Error("ERR_STALE_REVISION", "Artifact content does not match its immutable revision hash.")
    return ArtifactValidation(artifact_id=artifact_id, revision=request.revision, content_sha256=request.content_sha256, valid=True)
