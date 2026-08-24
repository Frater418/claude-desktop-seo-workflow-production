# noqa: SIZE_OK - one ordered end-to-end lifecycle narrative
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from services.operator_api.app import AppConfig, create_app
from services.operator_api.local_e2e import LocalWorkflowService
from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet
from services.operator_api.repository import WorkspaceRegistry
from services.operator_api.runtime import LocalFixtureProvider, LocalRuntimeService, RuntimeProviderError
from services.operator_api.step_validation import GateContext
from services.runtime_contracts.llm_records import RuntimeContractValidator
from services.step1_preflight.validator import validate_step1_preflight
from services.step1b_preflight.validator import validate_step1b_preflight
from services.step1c_preflight.validator import validate_step1c_preflight
from services.step2_preflight.validator import validate_step2_preflight
from services.step3_preflight.validator import validate_step3_preflight
from services.step4a_preflight.validator import validate_step4a_preflight
from services.step4b_preflight.validator import validate_step4b_preflight
from tests.support.neutral_step1 import build_neutral_step1_fixture
from tests.support.neutral_step1b import build_neutral_step1b_fixture
from tests.support.neutral_step1c import build_neutral_step1c_fixture
from tests.support.neutral_step2 import build_neutral_step2_fixture
from tests.support.neutral_step3 import build_neutral_step3_fixture
from tests.support.neutral_step4a import build_neutral_step4a_fixture
from tests.support.neutral_step4b import build_neutral_step4b_fixture


ROOT = Path(__file__).resolve().parents[1]
TENANT = "tenant-neutral"
PROJECT = "project-neutral"
RUN = "run-neutral-0001"
ACTOR = "operator-heartweb-admin"
NOW = "2026-08-20T12:00:00Z"


def _project() -> dict[str, object]:
    project = json.loads((ROOT / "tests/fixtures/domain/real-customer-matrix/national-b2b.json").read_text(encoding="utf-8"))
    project["project_id"] = PROJECT
    project["tenant"]["tenant_id"] = TENANT
    return project


def _markdown() -> str:
    return "\n".join(("# National B2B", "", f"Tenant ID: {TENANT}", f"Project ID: {PROJECT}", "Project Name: National B2B", "", "## Project V2", "```json", json.dumps(_project(), separators=(",", ":")), "```"))


def _runtime_validator() -> RuntimeContractValidator:
    runtime = ROOT / "standards/runtime"
    names = ("logical-project-session", "official-prompt-registry", "worker-profile", "context-package", "llm-run-request", "llm-run-result")
    registry = json.loads((runtime / "official-prompt-registry.json").read_text(encoding="utf-8"))
    schemas = {name: json.loads((runtime / f"{name}.schema.json").read_text(encoding="utf-8")) for name in names}
    return RuntimeContractValidator(schemas, registry)


def _intent(action: str, run_id: str = RUN, step_id: str = "0", revision: int = 1) -> dict[str, object]:
    return {"action": action, "tenant_id": TENANT, "project_id": PROJECT, "run_id": run_id, "step_id": step_id, "expected_revision": revision}


def _confirm(client: TestClient, base: str, action: str, key: str, run_id: str = RUN, step_id: str = "0") -> dict[str, object]:
    intent = _intent(action, run_id, step_id, client.get(f"{base}/runs/{run_id}").json()["data"]["revision"])
    preview = client.post(f"{base}/actions/{action}/preview", json=intent)
    assert preview.status_code == 200, preview.text
    reviewed = preview.json()
    assert reviewed["allowed"], reviewed
    confirmed = client.post(f"{base}/actions/{action}/confirm", json={"intent": intent, "preview_hash": reviewed["preview_hash"], "idempotency_key": key, "confirmed": True})
    assert confirmed.status_code == 200, confirmed.text
    return confirmed.json()


def _output_set(content: bytes) -> ProviderOutputSet:
    registry = json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8"))
    contract = next(entry["output_contracts"][0]["contract_id"] for entry in registry["entries"] if entry["step_id"] == "0")
    output = ProviderOutput(contract_id=contract, content_bytes=content, content_sha256=hashlib.sha256(content).hexdigest(), content_type="application/json", tenant_id=TENANT, project_id=PROJECT, run_id=RUN, step_id="0", idempotency_key="idem-fixture-step0-0001", parent_revision=1, target_revision=2, created_at=datetime(2026, 8, 20, 12, tzinfo=UTC))
    return ProviderOutputSet.from_registry(registry, primary=output)


def _request(provider: LocalFixtureProvider, run_id: str = RUN, step_id: str = "0") -> dict[str, str]:
    return {"tenant_id": TENANT, "project_id": PROJECT, "run_id": run_id, "step_id": step_id, "fixture_id": provider.fixture_id, "fixture_sha256": provider.fixture_sha256, "context_package_id": f"context-neutral-step{step_id}-0001", "llm_run_request_id": f"llm-request-neutral-step{step_id}-0001", "llm_run_result_id": f"llm-result-neutral-step{step_id}-0001", "correlation_id": f"corr-neutral-step{step_id}-0001", "idempotency_key": provider.output_set.primary.idempotency_key, "actor_id": ACTOR, "requested_at": NOW, "started_at": NOW, "finished_at": "2026-08-20T12:00:01Z"}


class Sprint5Package4Tests(unittest.TestCase):
    def test_neutral_markdown_intake_runs_through_released_step_zero_with_canonical_readbacks(self) -> None:
        content = json.dumps(json.loads((ROOT / "tests/fixtures/operator/neutral-step0-manifest.json").read_text(encoding="utf-8")), separators=(",", ":"), sort_keys=True).encode()
        outputs = _output_set(content)
        provider = LocalFixtureProvider("fixture-neutral-step0-0001", outputs)
        with tempfile.TemporaryDirectory() as temporary:
            provisioning_root = Path(temporary) / "provisioned"
            app = create_app(WorkspaceRegistry(()), ROOT, AppConfig(repository_root=ROOT, provisioning_root=provisioning_root, provisioning_enabled=True, execution_mode="simulated", fixture_provider=provider))
            client = TestClient(app)
            intake = _markdown()
            preview = client.post(f"/v1/tenants/{TENANT}/intake/preview", json={"markdown": intake})
            self.assertEqual(200, preview.status_code)
            accepted = client.post(f"/v1/tenants/{TENANT}/intake/accept", json={"markdown": intake, "source_sha256": preview.json()["data"]["source_sha256"], "reviewed": preview.json()["data"]["reviewed"], "preview_hash": preview.json()["data"]["preview_hash"], "confirmed": True})
            self.assertEqual(200, accepted.status_code)
            base = f"/v1/tenants/{TENANT}/projects/{PROJECT}"
            self.assertEqual("not_due", client.get(f"{base}/steps/3b").json()["data"]["status"])
            started = _confirm(client, base, "start", "idem-action-start-0001")
            self.assertEqual("in_progress", client.get(started["readback_urls"][0]).json()["data"]["status"])
            repository = app.state.repository
            service = LocalWorkflowService.from_root(repository, ROOT, LocalRuntimeService("simulated", provider, app.state.recovery_inventory), _runtime_validator(), json.loads((ROOT / "tests/fixtures/context_builder/positive-worker-profile.json").read_text(encoding="utf-8")), app.state.dependencies["record_schemas"]["artifact-record.schema"], app.state.recovery_inventory)
            context = GateContext.model_validate({"site_status": "non_existing_site", "configured_tools": [], "available_tools": [], "not_applicable_decisions": {}, "evidence_by_gate": {"qg-domain-contract": {"schema_id": "https://heartweb.example/schema/manifest.schema.json", "schema_version": "1.0.0", "artifact_sha256": hashlib.sha256(content).hexdigest(), "validator_result": "simulated:neutral-fixture"}}})
            prepared, persisted = service.prepare_and_persist(_request(provider), {"project": _project()}, context)
            self.assertEqual(content, prepared.candidate_bytes)
            self.assertEqual(1, len(persisted.records))
            self.assertEqual(200, client.get(f"{base}/context-packages").status_code)
            self.assertEqual(1, len(client.get(f"{base}/artifacts").json()["data"]))
            self.assertEqual(1, len(client.get(f"{base}/gates").json()["data"]))
            self.assertEqual("awaiting_gate", client.get(_confirm(client, base, "submit-for-gate", "idem-action-submit-0001")["readback_urls"][0]).json()["data"]["status"])
            approved = _confirm(client, base, "approve", "idem-action-approve-0001")
            self.assertEqual("approved", client.get(approved["readback_urls"][0]).json()["data"]["status"])
            self.assertEqual(1, len(client.get(f"{base}/approvals").json()["data"]))
            completed = _confirm(client, base, "complete", "idem-action-complete-0001")
            replayed = client.post(f"{base}/actions/complete/confirm", json={"intent": _intent("complete", revision=2), "preview_hash": completed["preview_hash"], "idempotency_key": "idem-action-complete-0001", "confirmed": True})
            self.assertEqual(200, replayed.status_code)
            self.assertTrue(replayed.json()["replay"])
            self.assertEqual("completed", client.get(completed["readback_urls"][0]).json()["data"]["status"])
            self.assertEqual("released", client.get(f"{base}/releases").json()["data"][0]["status"])
            successor = _confirm(client, base, "start", "idem-action-start-step1-0001")
            successor_run = successor["canonical"]["run"]
            self.assertEqual("1", successor_run["step_id"])
            self.assertEqual("in_progress", client.get(successor["readback_urls"][0]).json()["data"]["status"])
            source_artifact = persisted.records[0].model_dump(mode="json")
            source_release = client.get(f"{base}/releases").json()["data"][0]
            gate0_qgr = next(gate for gate in client.get(f"{base}/gates").json()["data"] if gate["human_gate_id"] == "GATE-0")
            gate0_approval = client.get(f"{base}/approvals").json()["data"][0]
            step1_fixture = build_neutral_step1_fixture(ROOT, _project(), source_artifact, source_release, gate0_approval, gate0_qgr, successor_run)
            partial = copy.deepcopy(step1_fixture.bundle)
            partial["artifact"]["artifact_id"] = "artifact-partial-rebind"
            self.assertFalse(validate_step1_preflight(partial)["valid"])
            preflight = validate_step1_preflight(step1_fixture.bundle)
            self.assertTrue(preflight["valid"], preflight["errors"])
            step1_provider = LocalFixtureProvider("fixture-simulated-neutral-step1-0001", step1_fixture.output_set)
            step1_service = LocalWorkflowService.from_root(repository, ROOT, LocalRuntimeService("simulated", step1_provider, app.state.recovery_inventory), _runtime_validator(), json.loads((ROOT / "tests/fixtures/context_builder/positive-worker-profile.json").read_text(encoding="utf-8")), app.state.dependencies["record_schemas"]["artifact-record.schema"], app.state.recovery_inventory)
            prepared_step1, persisted_step1 = step1_service.prepare_and_persist(_request(step1_provider, successor_run["run_id"], "1"), step1_fixture.bundle, step1_fixture.gate_context)
            self.assertEqual(step1_fixture.output_set.primary.content_bytes, prepared_step1.candidate_bytes)
            self.assertEqual(successor_run["run_id"], prepared_step1.context_package["run_id"])
            self.assertEqual(successor_run["run_id"], prepared_step1.llm_request["run_id"])
            self.assertEqual(successor_run["run_id"], prepared_step1.llm_result["run_id"])
            self.assertEqual(1, len(persisted_step1.records))
            self.assertEqual(step1_fixture.bundle["artifact"]["artifact_id"], persisted_step1.records[0].artifact_id)
            self.assertEqual(4, len(client.get(f"{base}/gates").json()["data"]))
            self.assertEqual(2, len(client.get(f"{base}/artifacts").json()["data"]))
            step1_submitted = _confirm(client, base, "submit-for-gate", "idem-action-submit-step1-0001", successor_run["run_id"], "1")
            self.assertEqual("awaiting_gate", client.get(step1_submitted["readback_urls"][0]).json()["data"]["status"])
            step1_approved = _confirm(client, base, "approve", "idem-action-approve-step1-0001", successor_run["run_id"], "1")
            self.assertEqual("approved", client.get(step1_approved["readback_urls"][0]).json()["data"]["status"])
            self.assertEqual(2, len(client.get(f"{base}/approvals").json()["data"]))
            self.assertTrue(any(gate["quality_gate_id"] == "qg-gate1-artifact-approval" for gate in client.get(f"{base}/gates").json()["data"]))
            step1_completed = _confirm(client, base, "complete", "idem-action-complete-step1-0001", successor_run["run_id"], "1")
            record_counts = {name: len(client.get(f"{base}/{name}").json()["data"]) for name in ("artifacts", "gates", "approvals", "releases")}
            step1_replayed = client.post(f"{base}/actions/complete/confirm", json={"intent": _intent("complete", successor_run["run_id"], "1", step1_completed["canonical"]["run"]["revision"]), "preview_hash": step1_completed["preview_hash"], "idempotency_key": "idem-action-complete-step1-0001", "confirmed": True})
            self.assertEqual(200, step1_replayed.status_code)
            self.assertTrue(step1_replayed.json()["replay"])
            self.assertEqual(record_counts, {name: len(client.get(f"{base}/{name}").json()["data"]) for name in record_counts})
            self.assertEqual("completed", client.get(step1_completed["readback_urls"][0]).json()["data"]["status"])
            releases = client.get(f"{base}/releases").json()["data"]
            self.assertEqual(2, len(releases))
            self.assertEqual("released", next(release for release in releases if release["run_id"] == successor_run["run_id"])["status"])
            step1b_started = _confirm(client, base, "start", "idem-action-start-step1b-0001", successor_run["run_id"], "1")
            step1b_run = step1b_started["canonical"]["run"]
            self.assertEqual("1b", step1b_run["step_id"])
            step1_artifact = persisted_step1.records[0].model_dump(mode="json")
            step1_release = next(release for release in releases if release["run_id"] == successor_run["run_id"])
            step1_qgr = next(gate for gate in client.get(f"{base}/gates").json()["data"] if gate["run_id"] == successor_run["run_id"] and gate["quality_gate_id"] == "qg-domain-contract")
            step1b_fixture = build_neutral_step1b_fixture(ROOT, _project(), step1_artifact, step1_release, step1_qgr, step1b_run)
            partial_1b = copy.deepcopy(step1b_fixture.bundle)
            partial_1b["candidate"]["source_artifact_ids"] = []
            self.assertFalse(validate_step1b_preflight(partial_1b)["valid"])
            step1b_preflight = validate_step1b_preflight(step1b_fixture.bundle)
            self.assertTrue(step1b_preflight["valid"], step1b_preflight["errors"])
            step1b_provider = LocalFixtureProvider("fixture-simulated-neutral-step1b-0001", step1b_fixture.output_set)
            step1b_service = LocalWorkflowService.from_root(repository, ROOT, LocalRuntimeService("simulated", step1b_provider, app.state.recovery_inventory), _runtime_validator(), json.loads((ROOT / "tests/fixtures/context_builder/positive-worker-profile.json").read_text(encoding="utf-8")), app.state.dependencies["record_schemas"]["artifact-record.schema"], app.state.recovery_inventory)
            prepared_1b, persisted_1b = step1b_service.prepare_and_persist(_request(step1b_provider, step1b_run["run_id"], "1b"), step1b_fixture.bundle, step1b_fixture.gate_context)
            self.assertEqual(step1b_fixture.output_set.primary.content_bytes, prepared_1b.candidate_bytes)
            self.assertEqual(step1b_run["run_id"], prepared_1b.context_package["run_id"])
            self.assertEqual(step1b_run["run_id"], prepared_1b.llm_request["run_id"])
            self.assertEqual(step1b_run["run_id"], prepared_1b.llm_result["run_id"])
            self.assertEqual(1, len(persisted_1b.records))
            self.assertEqual(step1b_fixture.output_set.primary.content_sha256, persisted_1b.records[0].content_sha256)
            self.assertEqual({"architecture.md", "architecture.html"}, {view.name for view in persisted_1b.derived_views})
            step1b_submitted = _confirm(client, base, "submit-for-gate", "idem-action-submit-step1b-0001", step1b_run["run_id"], "1b")
            self.assertEqual("awaiting_gate", client.get(step1b_submitted["readback_urls"][0]).json()["data"]["status"])
            step1b_approved = _confirm(client, base, "approve", "idem-action-approve-step1b-0001", step1b_run["run_id"], "1b")
            self.assertEqual("approved", client.get(step1b_approved["readback_urls"][0]).json()["data"]["status"])
            self.assertTrue(any(gate["run_id"] == step1b_run["run_id"] and gate["quality_gate_id"] == "qg-gate1b-architecture-approval" for gate in client.get(f"{base}/gates").json()["data"]))
            step1b_completed = _confirm(client, base, "complete", "idem-action-complete-step1b-0001", step1b_run["run_id"], "1b")
            step1b_counts = {name: len(client.get(f"{base}/{name}").json()["data"]) for name in ("artifacts", "gates", "approvals", "releases")}
            step1b_replayed = client.post(f"{base}/actions/complete/confirm", json={"intent": _intent("complete", step1b_run["run_id"], "1b", step1b_completed["canonical"]["run"]["revision"]), "preview_hash": step1b_completed["preview_hash"], "idempotency_key": "idem-action-complete-step1b-0001", "confirmed": True})
            self.assertTrue(step1b_replayed.json()["replay"])
            self.assertEqual(step1b_counts, {name: len(client.get(f"{base}/{name}").json()["data"]) for name in step1b_counts})
            step1c_started = _confirm(client, base, "start", "idem-action-start-step1c-0001", step1b_run["run_id"], "1b")
            step1c_run = step1c_started["canonical"]["run"]
            self.assertEqual("1c", step1c_run["step_id"])
            step1b_artifact = persisted_1b.records[0].model_dump(mode="json")
            step1b_release = next(release for release in client.get(f"{base}/releases").json()["data"] if release["run_id"] == step1b_run["run_id"])
            step1b_qgr = next(gate for gate in client.get(f"{base}/gates").json()["data"] if gate["run_id"] == step1b_run["run_id"] and gate["quality_gate_id"] == "qg-step1b-architecture-integrity")
            step1c_fixture = build_neutral_step1c_fixture(ROOT, _project(), step1b_artifact, step1b_release, step1b_qgr, step1c_run)
            partial_1c = copy.deepcopy(step1c_fixture.bundle)
            partial_1c["templates"][0]["source_artifact_ids"] = []
            self.assertFalse(validate_step1c_preflight(partial_1c)["valid"])
            step1c_preflight = validate_step1c_preflight(step1c_fixture.bundle)
            self.assertTrue(step1c_preflight["valid"], step1c_preflight["errors"])
            step1c_provider = LocalFixtureProvider("fixture-simulated-neutral-step1c-0001", step1c_fixture.output_set)
            step1c_service = LocalWorkflowService.from_root(repository, ROOT, LocalRuntimeService("simulated", step1c_provider, app.state.recovery_inventory), _runtime_validator(), json.loads((ROOT / "tests/fixtures/context_builder/positive-worker-profile.json").read_text(encoding="utf-8")), app.state.dependencies["record_schemas"]["artifact-record.schema"], app.state.recovery_inventory)
            prepared_1c, persisted_1c = step1c_service.prepare_and_persist(_request(step1c_provider, step1c_run["run_id"], "1c"), step1c_fixture.bundle, step1c_fixture.gate_context)
            self.assertEqual(step1c_fixture.output_set.primary.content_bytes, prepared_1c.candidate_bytes)
            self.assertEqual(step1c_run["run_id"], prepared_1c.context_package["run_id"])
            self.assertEqual(step1c_run["run_id"], prepared_1c.llm_request["run_id"])
            self.assertEqual(step1c_run["run_id"], prepared_1c.llm_result["run_id"])
            self.assertEqual(2, len(persisted_1c.records))
            self.assertEqual(tuple(output.content_sha256 for output in step1c_fixture.output_set.outputs), tuple(record.content_sha256 for record in persisted_1c.records))
            self.assertNotEqual(persisted_1c.records[0].artifact_id, persisted_1c.records[1].artifact_id)
            self.assertEqual({"css", "html", "html.template-care-0001.html"}, {view.name for view in persisted_1c.derived_views})
            step1c_submitted = _confirm(client, base, "submit-for-gate", "idem-action-submit-step1c-0001", step1c_run["run_id"], "1c")
            self.assertEqual("awaiting_gate", client.get(step1c_submitted["readback_urls"][0]).json()["data"]["status"])
            step1c_approved = _confirm(client, base, "approve", "idem-action-approve-step1c-0001", step1c_run["run_id"], "1c")
            self.assertEqual("approved", client.get(step1c_approved["readback_urls"][0]).json()["data"]["status"])
            self.assertTrue(any(gate["run_id"] == step1c_run["run_id"] and gate["quality_gate_id"] == "qg-gate1c-design-approval" for gate in client.get(f"{base}/gates").json()["data"]))
            step1c_completed = _confirm(client, base, "complete", "idem-action-complete-step1c-0001", step1c_run["run_id"], "1c")
            step1c_counts = {name: len(client.get(f"{base}/{name}").json()["data"]) for name in ("artifacts", "gates", "approvals", "releases")}
            step1c_replayed = client.post(f"{base}/actions/complete/confirm", json={"intent": _intent("complete", step1c_run["run_id"], "1c", step1c_completed["canonical"]["run"]["revision"]), "preview_hash": step1c_completed["preview_hash"], "idempotency_key": "idem-action-complete-step1c-0001", "confirmed": True})
            self.assertTrue(step1c_replayed.json()["replay"])
            self.assertEqual(step1c_counts, {name: len(client.get(f"{base}/{name}").json()["data"]) for name in step1c_counts})
            step2_started = _confirm(client, base, "start", "idem-action-start-step2-0001", step1c_run["run_id"], "1c")
            step2_run = step2_started["canonical"]["run"]
            self.assertEqual("2", step2_run["step_id"])
            self.assertEqual("in_progress", client.get(step2_started["readback_urls"][0]).json()["data"]["status"])
            step1c_artifact = persisted_1c.records[0].model_dump(mode="json")
            step1c_release = next(release for release in client.get(f"{base}/releases").json()["data"] if release["run_id"] == step1c_run["run_id"])
            step1c_qgr = next(gate for gate in client.get(f"{base}/gates").json()["data"] if gate["run_id"] == step1c_run["run_id"] and gate["quality_gate_id"] == "qg-step1c-design-system")
            step2_fixture = build_neutral_step2_fixture(ROOT, _project(), step1c_artifact, step1c_release, step1c_qgr, step2_run)
            partial_2 = copy.deepcopy(step2_fixture.bundle)
            partial_2["provider_evidence_records"][0]["response"]["geo"] = {"country_code": "ZZ", "provider_location_code": 0}
            self.assertFalse(validate_step2_preflight(partial_2)["valid"])
            step2_preflight = validate_step2_preflight(step2_fixture.bundle)
            self.assertTrue(step2_preflight["valid"], step2_preflight["errors"])
            step2_provider = LocalFixtureProvider("fixture-simulated-neutral-step2-0001", step2_fixture.output_set)
            step2_service = LocalWorkflowService.from_root(repository, ROOT, LocalRuntimeService("simulated", step2_provider, app.state.recovery_inventory), _runtime_validator(), json.loads((ROOT / "tests/fixtures/context_builder/positive-worker-profile.json").read_text(encoding="utf-8")), app.state.dependencies["record_schemas"]["artifact-record.schema"], app.state.recovery_inventory)
            prepared_2, persisted_2 = step2_service.prepare_and_persist(_request(step2_provider, step2_run["run_id"], "2"), step2_fixture.bundle, step2_fixture.gate_context)
            self.assertEqual(step2_fixture.output_set.primary.content_bytes, prepared_2.candidate_bytes)
            self.assertEqual(step2_run["run_id"], prepared_2.context_package["run_id"])
            self.assertEqual(step2_run["run_id"], prepared_2.llm_request["run_id"])
            self.assertEqual(step2_run["run_id"], prepared_2.llm_result["run_id"])
            self.assertEqual(step2_fixture.output_set.primary.content_sha256, persisted_2.records[0].content_sha256)
            self.assertEqual({"keyword-evidence.csv"}, {view.name for view in persisted_2.derived_views})
            step2_submitted = _confirm(client, base, "submit-for-gate", "idem-action-submit-step2-0001", step2_run["run_id"], "2")
            self.assertEqual("awaiting_gate", client.get(step2_submitted["readback_urls"][0]).json()["data"]["status"])
            _confirm(client, base, "approve", "idem-action-approve-step2-0001", step2_run["run_id"], "2")
            step2_completed = _confirm(client, base, "complete", "idem-action-complete-step2-0001", step2_run["run_id"], "2")
            step2_counts = {name: len(client.get(f"{base}/{name}").json()["data"]) for name in ("artifacts", "gates", "approvals", "releases")}
            step2_replayed = client.post(f"{base}/actions/complete/confirm", json={"intent": _intent("complete", step2_run["run_id"], "2", step2_completed["canonical"]["run"]["revision"]), "preview_hash": step2_completed["preview_hash"], "idempotency_key": "idem-action-complete-step2-0001", "confirmed": True})
            self.assertTrue(step2_replayed.json()["replay"])
            self.assertEqual(step2_counts, {name: len(client.get(f"{base}/{name}").json()["data"]) for name in step2_counts})
            step3_started = _confirm(client, base, "start", "idem-action-start-step3-0001", step2_run["run_id"], "2")
            step3_run = step3_started["canonical"]["run"]
            self.assertEqual("3", step3_run["step_id"])
            step2_artifact = persisted_2.records[0].model_dump(mode="json")
            step2_release = next(release for release in client.get(f"{base}/releases").json()["data"] if release["run_id"] == step2_run["run_id"])
            step2_qgr = next(gate for gate in client.get(f"{base}/gates").json()["data"] if gate["run_id"] == step2_run["run_id"] and gate["quality_gate_id"] == "qg-domain-contract")
            step3_fixture = build_neutral_step3_fixture(ROOT, _project(), step2_artifact, step2_release, step2_qgr, step2_fixture.output_set.primary.content_bytes.decode("utf-8"), step3_run)
            partial_3 = copy.deepcopy(step3_fixture.bundle)
            partial_3["candidate"]["solver_output_sha256"] = "0" * 64
            self.assertFalse(validate_step3_preflight(partial_3)["valid"])
            step3_preflight = validate_step3_preflight(step3_fixture.bundle)
            self.assertTrue(step3_preflight["valid"], step3_preflight["errors"])
            step3_provider = LocalFixtureProvider("fixture-simulated-neutral-step3-0001", step3_fixture.output_set)
            step3_service = LocalWorkflowService.from_root(repository, ROOT, LocalRuntimeService("simulated", step3_provider, app.state.recovery_inventory), _runtime_validator(), json.loads((ROOT / "tests/fixtures/context_builder/positive-worker-profile.json").read_text(encoding="utf-8")), app.state.dependencies["record_schemas"]["artifact-record.schema"], app.state.recovery_inventory)
            prepared_3, persisted_3 = step3_service.prepare_and_persist(_request(step3_provider, step3_run["run_id"], "3"), step3_fixture.bundle, step3_fixture.gate_context)
            self.assertEqual(step3_fixture.output_set.primary.content_bytes, prepared_3.candidate_bytes)
            self.assertEqual(step3_run["run_id"], prepared_3.context_package["run_id"])
            self.assertEqual(step3_run["run_id"], prepared_3.llm_request["run_id"])
            self.assertEqual(step3_run["run_id"], prepared_3.llm_result["run_id"])
            self.assertEqual({"plan.md"}, {view.name for view in persisted_3.derived_views})
            step3_submitted = _confirm(client, base, "submit-for-gate", "idem-action-submit-step3-0001", step3_run["run_id"], "3")
            self.assertEqual("awaiting_gate", client.get(step3_submitted["readback_urls"][0]).json()["data"]["status"])
            _confirm(client, base, "approve", "idem-action-approve-step3-0001", step3_run["run_id"], "3")
            step3_completed = _confirm(client, base, "complete", "idem-action-complete-step3-0001", step3_run["run_id"], "3")
            step3_counts = {name: len(client.get(f"{base}/{name}").json()["data"]) for name in ("artifacts", "gates", "approvals", "releases")}
            step3_replayed = client.post(f"{base}/actions/complete/confirm", json={"intent": _intent("complete", step3_run["run_id"], "3", step3_completed["canonical"]["run"]["revision"]), "preview_hash": step3_completed["preview_hash"], "idempotency_key": "idem-action-complete-step3-0001", "confirmed": True})
            self.assertTrue(step3_replayed.json()["replay"])
            self.assertEqual(step3_counts, {name: len(client.get(f"{base}/{name}").json()["data"]) for name in step3_counts})
            step4a_started = _confirm(client, base, "start", "idem-action-start-step4a-0001", step3_run["run_id"], "3")
            step4a_run = step4a_started["canonical"]["run"]
            self.assertEqual("4a", step4a_run["step_id"])
            self.assertEqual("in_progress", client.get(step4a_started["readback_urls"][0]).json()["data"]["status"])
            step3_artifact = persisted_3.records[0].model_dump(mode="json")
            step3_release = next(release for release in client.get(f"{base}/releases").json()["data"] if release["run_id"] == step3_run["run_id"])
            step3_qgr = next(gate for gate in client.get(f"{base}/gates").json()["data"] if gate["run_id"] == step3_run["run_id"] and gate["quality_gate_id"] == "qg-step3-deterministic-plan")
            step4a_fixture = build_neutral_step4a_fixture(ROOT, _project(), step3_artifact, step3_release, step3_qgr, step4a_run)
            partial_4a = copy.deepcopy(step4a_fixture.bundle)
            partial_4a["briefing"]["jsonld"]["graph_hash"] = "0" * 64
            self.assertFalse(validate_step4a_preflight(partial_4a)["valid"])
            step4a_preflight = validate_step4a_preflight(step4a_fixture.bundle)
            self.assertTrue(step4a_preflight["valid"], step4a_preflight["errors"])
            step4a_provider = LocalFixtureProvider("fixture-simulated-neutral-step4a", step4a_fixture.output_set)
            step4a_service = LocalWorkflowService.from_root(repository, ROOT, LocalRuntimeService("simulated", step4a_provider, app.state.recovery_inventory), _runtime_validator(), json.loads((ROOT / "tests/fixtures/context_builder/positive-worker-profile.json").read_text(encoding="utf-8")), app.state.dependencies["record_schemas"]["artifact-record.schema"], app.state.recovery_inventory)
            prepared_4a, persisted_4a = step4a_service.prepare_and_persist(_request(step4a_provider, step4a_run["run_id"], "4a"), step4a_fixture.bundle, step4a_fixture.gate_context)
            self.assertEqual(step4a_run["run_id"], prepared_4a.llm_result["run_id"])
            self.assertTrue(persisted_4a.derived_views)
            _confirm(client, base, "submit-for-gate", "idem-action-submit-step4a", step4a_run["run_id"], "4a")
            _confirm(client, base, "approve", "idem-action-approve-step4a", step4a_run["run_id"], "4a")
            _confirm(client, base, "complete", "idem-action-complete-step4a", step4a_run["run_id"], "4a")
            step4b_started = _confirm(client, base, "start", "idem-action-start-step4b", step4a_run["run_id"], "4a")
            step4b_run = step4b_started["canonical"]["run"]
            step4a_artifact = persisted_4a.records[0].model_dump(mode="json")
            step4a_release = next(release for release in client.get(f"{base}/releases").json()["data"] if release["run_id"] == step4a_run["run_id"])
            step4a_qgr = next(gate for gate in client.get(f"{base}/gates").json()["data"] if gate["run_id"] == step4a_run["run_id"] and gate["quality_gate_id"] == "qg-step4a-claims-and-schema")
            step4b_fixture = build_neutral_step4b_fixture(ROOT, _project(), step4a_artifact, step4a_release, step4a_qgr, step4b_run)
            partial_4b = copy.deepcopy(step4b_fixture.bundle)
            partial_4b["page_spec"]["content_sha256"] = "0" * 64
            self.assertFalse(validate_step4b_preflight(partial_4b)["valid"])
            self.assertTrue(validate_step4b_preflight(step4b_fixture.bundle)["valid"])
            step4b_provider = LocalFixtureProvider("fixture-simulated-neutral-step4b", step4b_fixture.output_set)
            step4b_service = LocalWorkflowService.from_root(repository, ROOT, LocalRuntimeService("simulated", step4b_provider, app.state.recovery_inventory), _runtime_validator(), json.loads((ROOT / "tests/fixtures/context_builder/positive-worker-profile.json").read_text(encoding="utf-8")), app.state.dependencies["record_schemas"]["artifact-record.schema"], app.state.recovery_inventory)
            prepared_4b, persisted_4b = step4b_service.prepare_and_persist(_request(step4b_provider, step4b_run["run_id"], "4b"), step4b_fixture.bundle, step4b_fixture.gate_context)
            self.assertEqual(step4b_run["run_id"], prepared_4b.llm_result["run_id"])
            self.assertTrue(persisted_4b.derived_views)
            _confirm(client, base, "submit-for-gate", "idem-action-submit-step4b", step4b_run["run_id"], "4b")
            _confirm(client, base, "approve", "idem-action-approve-step4b", step4b_run["run_id"], "4b")
            completed_4b = _confirm(client, base, "complete", "idem-action-complete-step4b", step4b_run["run_id"], "4b")
            self.assertEqual("completed", client.get(completed_4b["readback_urls"][0]).json()["data"]["status"])
            sequence = {step_id: index for index, step_id in enumerate(("0", "1", "1b", "1c", "2", "3", "4a", "4b"))}
            self.assertEqual(["0", "1", "1b", "1c", "2", "3", "4a", "4b"], [release["step_id"] for release in sorted(client.get(f"{base}/releases").json()["data"], key=lambda release: sequence[release["step_id"]])])
            self.assertEqual("not_due", client.get(f"{base}/steps/3b").json()["data"]["status"])

    def test_missing_fixture_provider_blocks_runtime_before_artifacts_or_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = create_app(WorkspaceRegistry(()), ROOT, AppConfig(repository_root=ROOT, provisioning_root=root, provisioning_enabled=True, execution_mode="real"))
            client = TestClient(app)
            preview = client.post(f"/v1/tenants/{TENANT}/intake/preview", json={"markdown": _markdown()}).json()["data"]
            self.assertEqual(200, client.post(f"/v1/tenants/{TENANT}/intake/accept", json={"markdown": _markdown(), "source_sha256": preview["source_sha256"], "reviewed": preview["reviewed"], "preview_hash": preview["preview_hash"], "confirmed": True}).status_code)
            repository = app.state.repository
            with self.assertRaises(RuntimeProviderError):
                LocalRuntimeService("real", None, app.state.recovery_inventory).prepare_step(repository, ROOT, _runtime_validator(), json.loads((ROOT / "tests/fixtures/context_builder/positive-worker-profile.json").read_text(encoding="utf-8")), {"fixture_id": "fixture-neutral-step0-0001", "fixture_sha256": "0" * 64, "step_id": "0", "tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN})
            self.assertEqual([], repository.collection(TENANT, PROJECT, "context-packages"))
            self.assertEqual([], repository.artifacts(TENANT, PROJECT))
            self.assertEqual("pending", repository.run(TENANT, PROJECT, RUN)["status"])
