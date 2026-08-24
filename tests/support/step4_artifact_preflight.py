from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from services.operator_api.app import AppConfig, create_app
from services.operator_api.artifact_revision_types import ArtifactRecord, build_artifact_record
from services.operator_api.artifact_revisions import ArtifactRevisionService
from services.operator_api.provider_outputs import ProviderOutput
from services.operator_api.recovery_inventory import RecoveryInventory
from services.operator_api.repository import ProjectRepository, WorkspaceRegistration, WorkspaceRegistry
from services.operator_api.step_validation import StepValidationService
from services.operator_api.validated_artifacts import ValidatedArtifactService
from tests.support.neutral_step4a import NeutralStep4AFixture, build_neutral_step4a_fixture
from tests.support.neutral_step4b import NeutralStep4BFixture, build_neutral_step4b_fixture


TENANT = "tenant-neutral"
PROJECT = "project-neutral"
INPUT_HASH = "a" * 64


def seed_step4_preflight(workspace: Path, root: Path, step_id: str) -> tuple[TestClient, NeutralStep4AFixture | NeutralStep4BFixture, ArtifactRecord]:
    project = _project(root)
    predecessor, release = _lineage(root, project, "3" if step_id == "4a" else "4a")
    run = {"tenant_id": TENANT, "project_id": PROJECT, "run_id": f"run-neutral-{step_id}-0001", "step_id": step_id, "revision": 1, "input_hash": INPUT_HASH, "status": "in_progress"}
    fixture = _fixture(root, project, predecessor, release, run, step_id)
    repository = _repository(workspace, run)
    schema = json.loads((root / "standards/runtime/artifact-record.schema.json").read_text(encoding="utf-8"))
    revisions = ArtifactRevisionService(repository, schema, RecoveryInventory(repository._registry))
    persisted = ValidatedArtifactService(StepValidationService.from_root(root), revisions).persist(
        fixture.output_set,
        INPUT_HASH,
        fixture.bundle,
        fixture.gate_context,
    )
    return TestClient(create_app(repository._registry, root, AppConfig(repository_root=root))), fixture, persisted.records[0]


def request_body(fixture: NeutralStep4AFixture | NeutralStep4BFixture) -> dict:
    return {
        "revision": fixture.output_set.primary.target_revision,
        "content_sha256": fixture.output_set.primary.content_sha256,
        "supporting_documents": [json.loads(output.content_bytes) for output in fixture.output_set.supporting],
        "bundle": fixture.bundle,
        "gate_context": fixture.gate_context.model_dump(mode="json"),
    }


def _project(root: Path) -> dict:
    project = json.loads((root / "tests/fixtures/domain/real-customer-matrix/national-b2b.json").read_text(encoding="utf-8"))
    project["project_id"] = PROJECT
    project["tenant"]["tenant_id"] = TENANT
    return project


def _lineage(root: Path, project: dict, step_id: str) -> tuple[dict, dict]:
    registry = json.loads((root / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8"))
    contract_id = next(entry["output_contracts"][0]["contract_id"] for entry in registry["entries"] if entry["step_id"] == step_id)
    output = ProviderOutput(
        contract_id=contract_id,
        content_bytes=b"{}",
        content_sha256=hashlib.sha256(b"{}").hexdigest(),
        content_type="application/json",
        tenant_id=TENANT,
        project_id=PROJECT,
        run_id=f"run-neutral-source-{step_id}-0001",
        step_id=step_id,
        idempotency_key=f"idem-neutral-source-{step_id}",
        parent_revision=1,
        target_revision=2,
        created_at=datetime(2026, 8, 20, tzinfo=UTC),
    )
    artifact = build_artifact_record(output, INPUT_HASH, ())
    release = {
        "release_id": "release-neutral-source-0001",
        "tenant_id": TENANT,
        "project_id": PROJECT,
        "run_id": output.run_id,
        "step_id": step_id,
        "gate_id": f"GATE-{step_id.upper()}",
        "artifact_id": artifact.artifact_id,
        "artifact_sha256": artifact.content_sha256,
        "artifact_revision": artifact.revision,
        "approval_id": "approval-neutral-source-0001",
        "policy_version": "1.0.0",
        "status": "released",
        "released_at": "2026-08-20T00:00:00Z",
    }
    return artifact.model_dump(mode="json"), release


def _fixture(root: Path, project: dict, predecessor: dict, release: dict, run: dict, step_id: str) -> NeutralStep4AFixture | NeutralStep4BFixture:
    if step_id == "4a":
        return build_neutral_step4a_fixture(root, project, predecessor, release, {}, run)
    return build_neutral_step4b_fixture(root, project, predecessor, release, {}, run)


def _repository(workspace: Path, run: dict) -> ProjectRepository:
    root = workspace / "v2/operator"
    root.mkdir(parents=True)
    (root / "artifacts.json").write_text("[]", encoding="utf-8")
    (root / "gates.json").write_text("[]", encoding="utf-8")
    runs = root / "runs"
    runs.mkdir()
    (runs / f"{run['run_id']}.json").write_text(json.dumps(run), encoding="utf-8")
    return ProjectRepository(WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),)))
