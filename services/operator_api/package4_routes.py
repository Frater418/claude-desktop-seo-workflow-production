from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime
from typing import Mapping

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field, JsonValue

from .actions import confirm_action, preview_action
from .artifact_preflight import ArtifactPreflightResponse, ArtifactPreflightService, ArtifactValidationRequest
from .artifact_revision_types import ArtifactContentResponse, ArtifactDiffRequest, ArtifactDiffResponse, ArtifactRevisionListResponse
from .artifact_revisions import ArtifactRevisionService
from .provider_outputs import ProviderOutput, ProviderOutputSet
from .intake import IntakeAcceptanceRequest, IntakePreview, IntakePreviewRequest, confirm_intake, preview_intake
from .models import ActionConfirmRequest, ActionConfirmResult, ActionIntent, ActionPreview, DataEnvelope
from .package4 import Package4Error
from .provisioning import WorkspaceProvisioner
from .repository import ProjectRepository, WorkspaceRegistry
from .step_validation import GateContext, StepValidationService
from .validated_artifacts import ValidatedArtifactService


class ArtifactCandidateSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str = Field(pattern=r"^run-[a-z0-9][a-z0-9-]{2,63}$")
    expected_parent_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1)
    primary_document: dict[str, JsonValue]
    supporting_documents: tuple[dict[str, JsonValue], ...] = ()
    bundle: dict[str, JsonValue]
    gate_context: GateContext


def register_package4_routes(app: FastAPI, repository: ProjectRepository, provisioner: WorkspaceProvisioner, registry: WorkspaceRegistry) -> None:
    prefix = "/v1/tenants/{tenant_id}/projects/{project_id}"

    @app.post("/v1/tenants/{tenant_id}/intake/preview", response_model=DataEnvelope, operation_id="previewMarkdownIntake")
    def intake_preview(tenant_id: str, body: IntakePreviewRequest) -> DataEnvelope:
        preview = preview_intake(body.markdown, app.state.operator_id, app.state.clock.now())
        app.state.intake_previews[preview.preview_hash] = preview
        return DataEnvelope(data=preview.model_dump(mode="json"))

    @app.post("/v1/tenants/{tenant_id}/intake/accept", response_model=DataEnvelope, operation_id="acceptMarkdownIntake")
    def intake_accept(tenant_id: str, body: IntakeAcceptanceRequest) -> DataEnvelope:
        _assert_mutation_ready(app)
        preview = app.state.intake_previews.get(body.preview_hash)
        if not isinstance(preview, IntakePreview):
            raise Package4Error("ERR_STALE_REVISION", "Intake preview is unavailable.")
        return DataEnvelope(data=provisioner.provision(tenant_id, confirm_intake(tenant_id, body, preview, app.state.operator_id)))

    @app.get(f"{prefix}/intake", response_model=DataEnvelope, operation_id="getMarkdownIntake")
    def intake(tenant_id: str, project_id: str) -> DataEnvelope:
        return DataEnvelope(data=repository.intake(tenant_id, project_id))

    @app.post(f"{prefix}/artifacts", response_model=DataEnvelope, operation_id="saveArtifactRevision")
    def artifact_save(tenant_id: str, project_id: str, body: ArtifactCandidateSaveRequest) -> DataEnvelope:
        if not app.state.ready:
            raise Package4Error("ERROR_CONTEXT_SOURCE_INVALID", "Operator API recovery is pending.")
        bundle = _artifact_bundle(repository, tenant_id, project_id, body)
        return DataEnvelope(data=_validated_artifacts(app, repository).persist(
            _output_set(app, repository, tenant_id, project_id, body),
            _run_input_hash(repository, tenant_id, project_id, body),
            bundle,
            body.gate_context,
        ).model_dump(mode="json"))

    @app.get(f"{prefix}/runs/{{run_id}}/steps/{{step_id}}/artifact-revisions", response_model=ArtifactRevisionListResponse, operation_id="listArtifactRevisions")
    def artifact_revisions(tenant_id: str, project_id: str, run_id: str, step_id: str) -> ArtifactRevisionListResponse:
        return ArtifactRevisionListResponse(artifacts=_artifact_revisions(app, repository).list_revisions(tenant_id, project_id, run_id, step_id))

    @app.get(f"{prefix}/artifacts/{{artifact_id}}", response_model=ArtifactContentResponse, operation_id="getArtifactRevision")
    @app.get(f"{prefix}/artifacts/{{artifact_id}}/content", response_model=ArtifactContentResponse, operation_id="getArtifactRevisionContent")
    def artifact_content(tenant_id: str, project_id: str, artifact_id: str) -> ArtifactContentResponse:
        service = _artifact_revisions(app, repository)
        return ArtifactContentResponse(artifact=service.artifact(tenant_id, project_id, artifact_id), content_base64=base64.b64encode(service.content_bytes(tenant_id, project_id, artifact_id)).decode("ascii"))

    @app.post(f"{prefix}/artifact-revisions/compare", response_model=ArtifactDiffResponse, operation_id="compareArtifactRevisions")
    def artifact_diff(tenant_id: str, project_id: str, body: ArtifactDiffRequest) -> ArtifactDiffResponse:
        service = _artifact_revisions(app, repository)
        return ArtifactDiffResponse(left_artifact=service.artifact(tenant_id, project_id, body.left_artifact_id), right_artifact=service.artifact(tenant_id, project_id, body.right_artifact_id), unified_diff=service.text_diff(tenant_id, project_id, body.left_artifact_id, body.right_artifact_id))

    @app.post(f"{prefix}/artifacts/{{artifact_id}}/validate", response_model=ArtifactPreflightResponse, operation_id="validateArtifactRevision")
    def artifact_validate(tenant_id: str, project_id: str, artifact_id: str, body: ArtifactValidationRequest) -> ArtifactPreflightResponse:
        preflight = ArtifactPreflightService(
            _artifact_revisions(app, repository),
            StepValidationService.from_root(app.state.repository_root),
        )
        return preflight.validate(tenant_id, project_id, artifact_id, body)

    @app.get(f"{prefix}/operator-records/{{record_type}}/{{record_id}}", response_model=DataEnvelope, operation_id="getOperatorRecord")
    def operator_record(tenant_id: str, project_id: str, record_type: str, record_id: str) -> DataEnvelope:
        return DataEnvelope(data=repository.operator_record(tenant_id, project_id, record_type, record_id))

    @app.post(f"{prefix}/actions/{{verb}}/preview", response_model=ActionPreview, operation_id="previewAdminAction")
    def action_preview(tenant_id: str, project_id: str, verb: str, body: ActionIntent) -> ActionPreview:
        _assert_mutation_ready(app)
        registry.resolve(tenant_id, project_id)
        if body.action != verb or body.tenant_id != tenant_id or body.project_id != project_id:
            raise Package4Error("ERR_TENANT_ISOLATION", "Action and route identity do not match.")
        return preview_action(repository, app, body)

    @app.post(f"{prefix}/actions/{{verb}}/confirm", response_model=ActionConfirmResult, operation_id="confirmAdminAction")
    def action_confirm(tenant_id: str, project_id: str, verb: str, body: ActionConfirmRequest) -> ActionConfirmResult:
        if not app.state.ready:
            raise Package4Error("ERROR_CONTEXT_SOURCE_INVALID", "Operator API recovery is pending.")
        registry.resolve(tenant_id, project_id)
        if body.intent.action != verb or body.intent.tenant_id != tenant_id or body.intent.project_id != project_id:
            raise Package4Error("ERR_TENANT_ISOLATION", "Action and route identity do not match.")
        return confirm_action(repository, registry, app, body)


def _artifact_revisions(app: FastAPI, repository: ProjectRepository) -> ArtifactRevisionService:
    schema = app.state.dependencies["record_schemas"]["artifact-record.schema"]
    if not isinstance(schema, dict):
        raise RuntimeError("Artifact schema is unavailable.")
    return ArtifactRevisionService(repository, schema, app.state.recovery_inventory)


def _validated_artifacts(app: FastAPI, repository: ProjectRepository) -> ValidatedArtifactService:
    return ValidatedArtifactService(StepValidationService.from_root(app.state.repository_root), _artifact_revisions(app, repository))


def _run_input_hash(repository: ProjectRepository, tenant_id: str, project_id: str, body: ArtifactCandidateSaveRequest) -> str:
    run = repository.run(tenant_id, project_id, body.run_id)
    input_hash = run.get("input_hash")
    if not isinstance(input_hash, str):
        raise Package4Error("ERROR_CONTEXT_SOURCE_INVALID", "Run input hash is unavailable.")
    return input_hash


def _artifact_bundle(repository: ProjectRepository, tenant_id: str, project_id: str, body: ArtifactCandidateSaveRequest) -> Mapping[str, JsonValue]:
    run = repository.run(tenant_id, project_id, body.run_id)
    if run.get("step_id") != "0":
        return body.bundle
    return {
        **body.bundle,
        "project": repository.project_v2(tenant_id, project_id),
        "accepted_intake": repository.intake(tenant_id, project_id),
    }


def _output_set(app: FastAPI, repository: ProjectRepository, tenant_id: str, project_id: str, body: ArtifactCandidateSaveRequest) -> ProviderOutputSet:
    run = repository.run(tenant_id, project_id, body.run_id)
    step_id, revision = run.get("step_id"), run.get("revision")
    if not isinstance(step_id, str) or not isinstance(revision, int) or revision < body.expected_parent_revision:
        raise Package4Error("ERR_STALE_REVISION", "Artifact candidate does not target the current run parent.")
    registry = StepValidationService.from_root(app.state.repository_root).prompt_registry
    documents = (body.primary_document, *body.supporting_documents)
    entry = next((item for item in registry.get("entries", []) if isinstance(item, dict) and item.get("step_id") == step_id and item.get("active") is True), None)
    if not isinstance(entry, dict) or not isinstance(entry.get("output_contracts"), list) or len(entry["output_contracts"]) != len(documents):
        raise Package4Error("ERROR_OUTPUT_CONTRACT_INVALID", "Candidate outputs do not match the run contract.")
    created_at = _run_created_at(run, app.state.clock.now())
    outputs = tuple(
        ProviderOutput(
            contract_id=contract["contract_id"], content_bytes=_canonical_bytes(document), content_sha256=hashlib.sha256(_canonical_bytes(document)).hexdigest(), content_type="application/json",
            tenant_id=tenant_id, project_id=project_id, run_id=body.run_id, step_id=step_id, idempotency_key=body.idempotency_key,
            parent_revision=body.expected_parent_revision, target_revision=body.expected_parent_revision + 1, created_at=created_at,
        )
        for contract, document in zip(entry["output_contracts"], documents, strict=True)
        if isinstance(contract, dict) and isinstance(contract.get("contract_id"), str)
    )
    if len(outputs) != len(documents):
        raise Package4Error("ERROR_OUTPUT_CONTRACT_INVALID", "Candidate output contract is invalid.")
    return ProviderOutputSet.from_registry(dict(registry), primary=outputs[0], supporting=outputs[1:])


def _canonical_bytes(document: JsonValue) -> bytes:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _run_created_at(run: Mapping[str, JsonValue], server_now: str) -> datetime:
    value = run.get("created_at")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise Package4Error("ERROR_CONTEXT_SOURCE_INVALID", "Run creation time is invalid.") from None
    try:
        return datetime.fromisoformat(server_now.replace("Z", "+00:00"))
    except ValueError:
        raise Package4Error("ERROR_CONTEXT_SOURCE_INVALID", "Server clock time is invalid.") from None


def _assert_mutation_ready(app: FastAPI) -> None:
    if not app.state.ready:
        raise Package4Error("ERROR_CONTEXT_SOURCE_INVALID", "Operator API recovery is pending.")
    app.state.recovery_inventory.authorize()
