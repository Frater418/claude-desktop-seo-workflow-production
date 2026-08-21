from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from services.operator_api.artifact_revisions import ArtifactRevisionError, ArtifactRevisionService
from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet
from services.operator_api.recovery_inventory import RecoveryInventory
from services.operator_api.repository import ProjectRepository, WorkspaceRegistration, WorkspaceRegistry
from services.operator_api.step_validation import GateContext, StepValidationError, StepValidationService
from services.operator_api.validated_artifacts import ValidatedArtifactService


ROOT = Path(__file__).resolve().parents[1]
TENANT = "tenant-neutral"
PROJECT = "project-neutral"
RUN = "run-neutral-0001"
INPUT_HASH = "a" * 64


def _write(workspace: Path, relative: str, value: dict[str, object] | list[object]) -> None:
    path = workspace / "v2" / "operator" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _service(workspace: Path) -> tuple[ProjectRepository, ValidatedArtifactService]:
    _write(workspace, "artifacts.json", [])
    _write(workspace, "gates.json", [])
    _write(workspace, f"runs/{RUN}.json", {"tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": "0", "revision": 1, "input_hash": INPUT_HASH, "status": "pending"})
    repository = ProjectRepository(WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),)))
    schema = json.loads((ROOT / "standards/runtime/artifact-record.schema.json").read_text(encoding="utf-8"))
    revisions = ArtifactRevisionService(repository, schema, RecoveryInventory(repository._registry))
    return repository, ValidatedArtifactService(StepValidationService.from_root(ROOT), revisions)


def _outputs(content: bytes) -> ProviderOutputSet:
    registry = json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8"))
    contract_id = next(item["output_contracts"][0]["contract_id"] for item in registry["entries"] if item["step_id"] == "0" and item["active"])
    output = ProviderOutput(contract_id=contract_id, content_bytes=content, content_sha256=hashlib.sha256(content).hexdigest(), content_type="application/json", tenant_id=TENANT, project_id=PROJECT, run_id=RUN, step_id="0", idempotency_key="validated-step-zero", parent_revision=1, target_revision=2, created_at=datetime(2026, 8, 20, tzinfo=UTC))
    return ProviderOutputSet.from_registry(registry, primary=output)


def _bundle() -> dict[str, object]:
    project = json.loads((ROOT / "tests/fixtures/domain/real-customer-matrix/national-b2b.json").read_text(encoding="utf-8"))
    project["project_id"] = PROJECT
    project["tenant"]["tenant_id"] = TENANT
    return {"project": project, "accepted_intake": {"source_sha256": "68cf4c5938b8e44ba95650155ba8706b55627fe8017fbbb7d9ea1fb524b82526", "reviewed": {"project_name": "National B2B", "project_v2": project}}}


def _context(content: bytes) -> GateContext:
    return GateContext.model_validate({"site_status": "non_existing_site", "configured_tools": [], "available_tools": [], "not_applicable_decisions": {}, "evidence_by_gate": {"qg-domain-contract": {"schema_id": "https://heartweb.example/schema/manifest.schema.json", "schema_version": "1.0.0", "artifact_sha256": hashlib.sha256(content).hexdigest(), "validator_result": "simulated:fixture-validated"}}})


class ValidatedArtifactServiceTests(unittest.TestCase):
    def test_persists_validated_artifact_qgr_and_views_atomically_and_replays_exactly(self) -> None:
        content = json.dumps(json.loads((ROOT / "tests/fixtures/operator/neutral-step0-manifest.json").read_text(encoding="utf-8")), separators=(",", ":"), sort_keys=True).encode()
        with tempfile.TemporaryDirectory() as temporary:
            repository, service = _service(Path(temporary))
            result = service.persist(_outputs(content), INPUT_HASH, _bundle(), _context(content))
            replay = service.persist(_outputs(content), INPUT_HASH, _bundle(), _context(content))
            self.assertEqual(result, replay)
            self.assertEqual(1, len(repository.artifacts(TENANT, PROJECT)))
            self.assertEqual(1, len(repository.quality_gate_runs(TENANT, PROJECT)))
            qgr = repository.quality_gate_runs(TENANT, PROJECT)[0]
            self.assertEqual(result.records[0].artifact_id, qgr["artifact_id"])
            self.assertEqual(result.records[0].content_sha256, qgr["artifact_sha256"])
            self.assertEqual(result.records[0].revision, qgr["artifact_revision"])
            self.assertEqual("simulated:fixture-validated", qgr["evidence"]["validator_result"])
            conflicting = GateContext.model_validate({"site_status": "non_existing_site", "configured_tools": [], "available_tools": [], "not_applicable_decisions": {}, "evidence_by_gate": {"qg-domain-contract": {"schema_id": "https://heartweb.example/schema/manifest.schema.json", "schema_version": "1.0.0", "artifact_sha256": hashlib.sha256(content).hexdigest(), "validator_result": "simulated:conflicting-fixture"}}})
            with self.assertRaisesRegex(ArtifactRevisionError, "ERR_IDEMPOTENCY_CONFLICT"):
                service.persist(_outputs(content), INPUT_HASH, _bundle(), conflicting)

    def test_rejects_invalid_candidate_or_missing_evidence_before_any_write(self) -> None:
        invalid = b'{"invalid":true}'
        with tempfile.TemporaryDirectory() as temporary:
            repository, service = _service(Path(temporary))
            with self.assertRaisesRegex(StepValidationError, "ERROR_OUTPUT_SCHEMA_INVALID"):
                service.persist(_outputs(invalid), INPUT_HASH, {"project": {}}, _context(invalid))
            self.assertEqual([], repository.artifacts(TENANT, PROJECT))
            self.assertEqual([], repository.quality_gate_runs(TENANT, PROJECT))

    def test_recovery_hides_partial_qgr_projection_and_persists_contained_view(self) -> None:
        content = json.dumps(json.loads((ROOT / "tests/fixtures/operator/neutral-step0-manifest.json").read_text(encoding="utf-8")), separators=(",", ":"), sort_keys=True).encode()
        with tempfile.TemporaryDirectory() as temporary:
            repository, service = _service(Path(temporary))
            validated = service.validation.validate(_outputs(content), INPUT_HASH, _bundle(), _context(content))
            qgrs = validated.quality_gate_runs
            original = service.revisions._repository._project._write
            calls = 0

            def fail_on_gates(*args: object) -> None:
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("injected")
                original(*args)

            from unittest.mock import patch
            with patch.object(service.revisions._repository._project, "_write", side_effect=fail_on_gates):
                with self.assertRaisesRegex(ArtifactRevisionError, "ERROR_ARTIFACT_PERSISTENCE"):
                    service.revisions._persist_validated_transaction(_outputs(content), INPUT_HASH, qgrs, {"fixture-view.md": "derived fixture"})
            self.assertEqual([], repository.artifacts(TENANT, PROJECT))
            self.assertEqual([], repository.quality_gate_runs(TENANT, PROJECT))
            recovered = service.revisions.recover_output_set(TENANT, PROJECT, RUN, "0", "validated-step-zero")
            view = Path(temporary) / "v2/operator/artifact-views" / recovered.records[0].artifact_id / "fixture-view.md"
            self.assertEqual("derived fixture", view.read_text(encoding="utf-8"))
