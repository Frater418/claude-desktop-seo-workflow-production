from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import JsonValue

from services.operator_api.artifact_revision_types import ArtifactRecord, ArtifactRevisionResult, build_artifact_record
from services.operator_api.artifact_revisions import ArtifactRevisionService
from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet
from services.operator_api.recovery_inventory import RecoveryInventory
from services.operator_api.repository import ProjectRepository, WorkspaceRegistration, WorkspaceRegistry


ROOT = Path(__file__).resolve().parents[2]
TENANT = "tenant-revision"
PROJECT = "project-revision"
RUN = "run-revision-0001"
INPUT_HASH = "a" * 64


def write_projection(workspace: Path, relative: str, value: JsonValue) -> None:
    path = workspace / "v2" / "operator" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def repository(workspace: Path) -> ProjectRepository:
    write_projection(workspace, "artifacts.json", [])
    write_projection(workspace, "gates.json", [])
    write_projection(workspace, f"runs/{RUN}.json", {"tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": "1c", "revision": 1, "input_hash": INPUT_HASH, "status": "pending"})
    return ProjectRepository(WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),)))


def outputs(*, key: str = "idem-revision-0001", target: int = 2, primary_bytes: bytes = b"primary", supporting_bytes: bytes = b"supporting") -> ProviderOutputSet:
    registry = json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8"))
    contracts = next(item["output_contracts"] for item in registry["entries"] if item["step_id"] == "1c" and item["active"])

    def output(contract_id: str, content: bytes) -> ProviderOutput:
        return ProviderOutput(contract_id=contract_id, content_bytes=content, content_sha256=hashlib.sha256(content).hexdigest(), content_type="application/json", tenant_id=TENANT, project_id=PROJECT, run_id=RUN, step_id="1c", idempotency_key=key, parent_revision=target - 1, target_revision=target, created_at=datetime(2026, 8, 20, tzinfo=UTC))

    return ProviderOutputSet.from_registry(registry, primary=output(contracts[0]["contract_id"], primary_bytes), supporting=(output(contracts[1]["contract_id"], supporting_bytes),))


def service(project_repository: ProjectRepository) -> ArtifactRevisionService:
    schema = json.loads((ROOT / "standards/runtime/artifact-record.schema.json").read_text(encoding="utf-8"))
    return ArtifactRevisionService(project_repository, schema, RecoveryInventory(project_repository._registry))


def persist_transaction(revisions: ArtifactRevisionService, output_set: ProviderOutputSet) -> ArtifactRevisionResult:
    return revisions._persist_validated_transaction(output_set, INPUT_HASH, (), {})


def seed_revisions(workspace: Path, output_sets: tuple[ProviderOutputSet, ...]) -> tuple[tuple[ArtifactRecord, ...], ...]:
    revisions: list[tuple[ArtifactRecord, ...]] = []
    records: list[dict[str, JsonValue]] = []
    for output_set in output_sets:
        parents = tuple(() for _ in output_set.outputs) if not revisions else tuple((record.artifact_id,) for record in revisions[-1])
        current = tuple(build_artifact_record(output, INPUT_HASH, parent) for output, parent in zip(output_set.outputs, parents, strict=True))
        revisions.append(current)
        records.extend(record.model_dump(mode="json") for record in current)
        for record, output in zip(current, output_set.outputs, strict=True):
            path = workspace / "v2" / "operator" / "artifact-content" / f"{record.artifact_id}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(output.content_bytes)
    write_projection(workspace, "artifacts.json", records)
    return tuple(revisions)
