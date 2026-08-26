from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from services.operator_api.repository import ProjectRepository, WorkspaceRegistration, WorkspaceRegistry
from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet
from services.operator_api.recovery_inventory import RecoveryInventory
from services.operator_api.runtime import (
    LocalFixtureProvider,
    LocalRuntimeService,
)
from services.operator_api.step_agents import load_step_agent_registry
from services.runtime_contracts.llm_records import RuntimeContractValidator


ROOT = Path(__file__).resolve().parents[1]
TENANT = "tenant-runtime"
PROJECT = "project-runtime"
RUN = "run-runtime-0001"
NOW = "2026-08-20T00:00:00Z"


def _write(workspace: Path, relative: str, value: object) -> None:
    path = workspace / "v2" / "operator" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _validator() -> RuntimeContractValidator:
    runtime = ROOT / "standards" / "runtime"
    names = ("logical-project-session", "official-prompt-registry", "worker-profile", "context-package", "llm-run-request", "llm-run-result")
    registry = json.loads((runtime / "official-prompt-registry.json").read_text(encoding="utf-8"))
    schemas = {name: json.loads((runtime / f"{name}.schema.json").read_text(encoding="utf-8")) for name in names}
    return RuntimeContractValidator(schemas, registry)


def _step_agent_registry():
    registry = json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8"))
    return load_step_agent_registry(ROOT, registry)


def _profile() -> dict[str, object]:
    return json.loads((ROOT / "tests" / "fixtures" / "context_builder" / "positive-worker-profile.json").read_text(encoding="utf-8"))


def _seed(workspace: Path, step_id: str) -> ProjectRepository:
    _write(workspace, "project.json", {"tenant_id": TENANT, "project_id": PROJECT, "name": "Runtime"})
    _write(workspace, "intake.json", {"tenant_id": TENANT, "project_id": PROJECT, "accepted": True})
    _write(workspace, "project-v2.json", {"tenant_id": TENANT, "project_id": PROJECT, "version": 2})
    intake_bytes = (workspace / "v2" / "operator" / "intake.json").read_bytes()
    _write(workspace, "logical-session.json", {"tenant_id": TENANT, "project_id": PROJECT, "logical_session_id": "logical-session-runtime-0001", "session_revision": 1, "project_source": {"source_id": "intake-runtime-0001", "revision": 1, "logical_ref": "runtime:intake/intake-runtime-0001", "content_sha256": hashlib.sha256(intake_bytes).hexdigest()}})
    _write(workspace, "workflow.json", {"tenant_id": TENANT, "project_id": PROJECT, "steps": [{"step_id": "0", "requires_released_predecessor": False}, {"step_id": "1", "requires_released_predecessor": True}], "initial_edges": [{"from_step_id": "0", "to_step_id": "1"}]})
    _write(workspace, f"runs/{RUN}.json", {"tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": step_id, "revision": 1, "input_hash": "a" * 64, "status": "pending"})
    _write(workspace, "context-packages.json", [])
    _write(workspace, "llm-runs.json", [])
    if step_id == "1":
        content = b"released step zero"
        artifact_id = "artifact-runtime-0001"
        path = workspace / "v2" / "operator" / "artifact-content" / f"{artifact_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        _write(workspace, "artifacts.json", [{
            "artifact_id": artifact_id,
            "tenant_id": TENANT,
            "project_id": PROJECT,
            "run_id": RUN,
            "step_id": "0",
            "revision": 1,
            "content_sha256": hashlib.sha256(content).hexdigest(),
        }])
        _write(workspace, "releases/release-runtime-0001.json", {"release_id": "release-runtime-0001", "tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": "0", "artifact_id": artifact_id, "artifact_sha256": hashlib.sha256(content).hexdigest(), "artifact_revision": 1, "status": "released"})
    return ProjectRepository(WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),)))


def _request(step_id: str, fixture_sha256: str | None = None) -> dict[str, str]:
    return {
        "tenant_id": TENANT,
        "project_id": PROJECT,
        "run_id": RUN,
        "step_id": step_id,
        "fixture_id": "fixture-runtime-0001",
        "fixture_sha256": fixture_sha256 or hashlib.sha256(b"candidate output").hexdigest(),
        "context_package_id": f"context-runtime-{step_id}-0001",
        "llm_run_request_id": f"llm-request-runtime-{step_id}-0001",
        "llm_run_result_id": f"llm-result-runtime-{step_id}-0001",
        "correlation_id": "correlation-runtime-0001",
        "idempotency_key": f"idempotency-runtime-{step_id}-0001",
        "actor_id": "operator-runtime",
        "requested_at": NOW,
        "started_at": NOW,
        "finished_at": "2026-08-20T00:00:01Z",
    }


def _service(repository: ProjectRepository) -> LocalRuntimeService:
    step_id = repository.run(TENANT, PROJECT, RUN)["step_id"]
    contract_ids = {
        "0": "https://heartweb.example/schema/manifest-v2.schema.json",
        "1": "https://heartweb.example/schema/outputs/step-1-topic-inventory.schema.json",
    }
    content = b"candidate output"
    primary = ProviderOutput(
        contract_id=contract_ids[step_id], content_bytes=content,
        content_sha256=hashlib.sha256(content).hexdigest(), content_type="application/json",
        tenant_id=TENANT, project_id=PROJECT, run_id=RUN, step_id=step_id,
        idempotency_key=f"idempotency-runtime-{step_id}-0001", parent_revision=1,
        target_revision=2, created_at=datetime(2026, 8, 20, tzinfo=UTC),
    )
    registry = json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8"))
    outputs = ProviderOutputSet.from_registry(registry, primary=primary)
    return LocalRuntimeService("simulated", LocalFixtureProvider("fixture-runtime-0001", outputs), RecoveryInventory(repository._registry))


class LocalRuntimeServiceTests(unittest.TestCase):

    def test_prepare_step_zero_uses_accepted_intake_and_persists_validated_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = _seed(Path(temporary), "0")

            service = _service(repository)
            prepared = service.prepare_step(repository, ROOT, _validator(), _profile(), _request("0", service.fixture_provider.fixture_sha256))

            self.assertEqual(b"candidate output", prepared.candidate_bytes)
            self.assertEqual("project_intake", prepared.context_package["project_context"]["binding_mode"])
            self.assertEqual(prepared.context_package["package_sha256"], repository.run(TENANT, PROJECT, RUN)["input_hash"])
            self.assertEqual([prepared.context_package], repository.collection(TENANT, PROJECT, "context-packages"))
            self.assertEqual([prepared.llm_request, prepared.llm_result], repository.collection(TENANT, PROJECT, "llm-runs"))

    def test_prepare_later_step_uses_exact_project_and_canonical_released_predecessor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository = _seed(workspace, "1")
            project_bytes = (workspace / "v2/operator/project-v2.json").read_bytes()

            service = _service(repository)
            prepared = service.prepare_step(repository, ROOT, _validator(), _profile(), _request("1", service.fixture_provider.fixture_sha256))

            sources = {source["source_kind"]: source for source in prepared.context_package["sources"]}
            self.assertEqual(hashlib.sha256(project_bytes).hexdigest(), sources["project_v2"]["content_sha256"])
            self.assertEqual("released_predecessor", sources["released_predecessor"]["source_kind"])

    def test_missing_provider_leaves_projections_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = _seed(Path(temporary), "0")
            service = LocalRuntimeService(
                execution_mode="real",
                fixture_provider=None,
                recovery_inventory=RecoveryInventory(repository._registry),
                hermes_provider=None,
                step_agent_registry=_step_agent_registry(),
            )

            with self.assertRaisesRegex(RuntimeError, "ERROR_RUNTIME_PROVIDER_BLOCKED"):
                service.prepare_step(repository, ROOT, _validator(), _profile(), _request("0"))

            self.assertEqual([], repository.collection(TENANT, PROJECT, "context-packages"))
            self.assertEqual([], repository.collection(TENANT, PROJECT, "llm-runs"))
            self.assertEqual("a" * 64, repository.run(TENANT, PROJECT, RUN)["input_hash"])

    def test_prepare_step_rejects_fixture_identity_that_differs_from_canonical_request(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = _seed(Path(temporary), "0")
            service = _service(repository)
            request = _request("0")
            request["idempotency_key"] = "idempotency-runtime-other-0001"

            with self.assertRaisesRegex(RuntimeError, "ERROR_LOCAL_FIXTURE_UNAVAILABLE"):
                service.prepare_step(repository, ROOT, _validator(), _profile(), request)

            self.assertEqual([], repository.collection(TENANT, PROJECT, "context-packages"))
            self.assertEqual([], repository.collection(TENANT, PROJECT, "llm-runs"))

    def test_runtime_persistence_recovers_after_mid_write_without_partial_collections(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = _seed(Path(temporary), "0")
            service = _service(repository)
            original_write = repository._write
            calls = 0

            def fail_after_context(*args: object) -> None:
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("injected")
                original_write(*args)

            with patch.object(repository, "_write", side_effect=fail_after_context):
                with self.assertRaises(RuntimeError):
                    service.prepare_step(repository, ROOT, _validator(), _profile(), _request("0", service.fixture_provider.fixture_sha256))

            self.assertEqual([], repository.collection(TENANT, PROJECT, "context-packages"))
            self.assertEqual([], repository.collection(TENANT, PROJECT, "llm-runs"))
            repository.recover_runtime_persistence(TENANT, PROJECT, RUN)
            self.assertEqual(1, len(repository.collection(TENANT, PROJECT, "context-packages")))
            self.assertEqual(2, len(repository.collection(TENANT, PROJECT, "llm-runs")))
            repository.recover_runtime_persistence(TENANT, PROJECT, RUN)
            self.assertEqual(1, len(repository.collection(TENANT, PROJECT, "context-packages")))
            self.assertEqual(2, len(repository.collection(TENANT, PROJECT, "llm-runs")))


if __name__ == "__main__":
    unittest.main()
