from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from services.preflight_common.boundary import validate_lineage
from services.provider_gateway.core import canonical_request_sha256
from services.step1b_preflight.validator import validate_step1b_preflight
from services.step1c_preflight.validator import validate_step1c_preflight
from services.step2_preflight.validator import validate_step2_preflight
from services.step3_preflight.solver_bridge import derive_step3_plan_fields
from services.step3_preflight.validator import validate_step3_preflight
from services.step3b_preflight.validator import validate_step3b_preflight
from services.step4a_preflight.validator import validate_step4a_preflight
from services.step4b_preflight.validator import validate_step4b_preflight


ROOT = Path(__file__).resolve().parents[1]


def _fixture(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _project() -> dict[str, object]:
    return _fixture("tests/fixtures/domain/real-customer-matrix/national-b2b.json")


def _predecessor(step_id: str, gate_id: str) -> tuple[dict[str, object], dict[str, object]]:
    artifact = {
        "artifact_id": "artifact-predecessor-0001",
        "tenant_id": "tenant-heartweb",
        "project_id": "project-national-b2b",
        "run_id": "run-predecessor-0001",
        "step_id": step_id,
        "revision": 1,
        "input_hash": "a" * 64,
        "content_sha256": "b" * 64,
        "contract_version": "2.0.0",
        "producer_version": "test",
        "storage_key": "tenants/tenant-heartweb/projects/project-national-b2b/runs/run-predecessor-0001/artifacts/artifact-predecessor-0001/output.json",
        "created_at": "2026-08-19T12:00:00Z",
    }
    release = {
        "release_id": "release-predecessor-0001",
        "tenant_id": artifact["tenant_id"],
        "project_id": artifact["project_id"],
        "run_id": artifact["run_id"],
        "step_id": step_id,
        "gate_id": gate_id,
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": artifact["content_sha256"],
        "artifact_revision": artifact["revision"],
        "approval_id": "approval-predecessor-0001",
        "policy_version": "1.0.0",
        "status": "released",
        "released_at": "2026-08-19T12:00:00Z",
    }
    return artifact, release


def _bind_candidate(candidate: dict[str, object]) -> dict[str, object]:
    candidate["project_id"] = "project-national-b2b"
    candidate["deployment_id"] = "dep-national-b2b-de"
    candidate["candidate_status"] = "awaiting_gate"
    candidate["source_artifact_ids"] = ["artifact-predecessor-0001"]
    return candidate


def _provider_records(candidate: dict[str, object]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for pillar in candidate["pillars"]:
        for index, row in enumerate(pillar["rows"], start=1):
            raw_response = {"keyword_metrics": [{"keyword": row["keyword"], "search_volume": row["search_volume"], "difficulty": row["difficulty"]}]}
            raw_response_sha256 = hashlib.sha256(json.dumps(raw_response, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
            request = {"schema_version": "2.0.0", "request_id": f"request-provider-{index:04d}", "run_id": candidate["run_id"], "project_id": candidate["project_id"], "deployment_id": candidate["deployment_id"], "revision": 1, "source_artifact_ids": candidate["source_artifact_ids"], "evidence_ids": [row["evidence_id"]], "decision_records": [{"decision_id": f"decision-provider-{index:04d}", "outcome": "research", "evidence_ids": [row["evidence_id"]]}], "candidate_status": "candidate", "provider": row["provider"], "operation": "keyword_metrics", "idempotency_key": f"provider-{index:04d}-key", "geo": candidate["geo"], "language": candidate["language"], "device": "mobile", "cost": {"currency": "USD", "maximum": 1}, "gateway_route": "provider_gateway"}
            request["request_sha256"] = canonical_request_sha256(request)
            response = {"schema_version": "2.0.0", "response_id": f"response-provider-{index:04d}", "request_id": request["request_id"], "run_id": candidate["run_id"], "project_id": candidate["project_id"], "deployment_id": candidate["deployment_id"], "revision": 1, "source_artifact_ids": candidate["source_artifact_ids"], "evidence_ids": [row["evidence_id"]], "decision_records": [{"decision_id": f"decision-provider-{index:04d}", "outcome": "research", "evidence_ids": [row["evidence_id"]]}], "candidate_status": "candidate", "provider": row["provider"], "provider_job_id": f"job-provider-{index:04d}", "status": "completed", "geo": candidate["geo"], "language": candidate["language"], "device": "mobile", "cost": {"currency": "USD", "actual": 0.5}, "raw_response": raw_response, "raw_response_sha256": raw_response_sha256}
            row["raw_response_sha256"] = raw_response_sha256
            response["raw_response_sha256"] = raw_response_sha256
            records.append({"evidence_id": row["evidence_id"], "request": request, "response": response})
    return records


class PreflightCommonTests(unittest.TestCase):
    def test_rejects_missing_predecessor_release(self) -> None:
        # Given: a canonical candidate without a released predecessor
        bundle = {"candidate": {"candidate_status": "awaiting_gate", "project_id": "project-solar-001", "deployment_id": "dep-solar-001", "source_artifact_ids": ["artifact-source-001"]}}
        # When: the shared boundary validates Step 2 lineage
        errors = validate_lineage(bundle, "2", "1c", "GATE-1C")
        # Then: direct preflight cannot report success
        self.assertIn("ERROR_PREFLIGHT_PREDECESSOR_RELEASE_INVALID", {error["code"] for error in errors})

    def test_rejects_completed_candidate(self) -> None:
        # Given: a candidate marked completed before the gate
        bundle = {"candidate": {"candidate_status": "completed"}}
        # When: the shared boundary validates it
        errors = validate_lineage(bundle, "2", "1c", "GATE-1C")
        # Then: the gate status is rejected
        self.assertIn("ERROR_PREFLIGHT_CANDIDATE_STATUS_INVALID", {error["code"] for error in errors})

    def test_operational_preflights_reject_omitted_predecessor_records(self) -> None:
        # Given: direct calls with no predecessor artifact or release record.
        from tests.test_step2_renderer import _operational_bundle as step2_bundle
        from tests.test_step3_renderer import _operational_bundle as step3_bundle

        step2_without_release = step2_bundle()
        step2_without_release.pop("predecessor_release")
        step3_without_release = step3_bundle()
        step3_without_release.pop("predecessor_release")
        cases = (
            ("1b", lambda: validate_step1b_preflight({}, [])),
            ("1c", lambda: validate_step1c_preflight({}, [])),
            ("2", lambda: validate_step2_preflight(step2_without_release)),
            ("3", lambda: validate_step3_preflight(step3_without_release)),
            ("3b", lambda: validate_step3b_preflight({})),
            ("4a", lambda: validate_step4a_preflight({})),
            ("4b", lambda: validate_step4b_preflight({})),
        )
        for step_id, preflight in cases:
            with self.subTest(step_id=step_id):
                # When: the operational entrypoint evaluates the incomplete bundle.
                result = preflight()
                # Then: a stable structured predecessor error blocks the gate.
                self.assertFalse(result["valid"])
                self.assertIn("ERROR_PREFLIGHT_PREDECESSOR_RELEASE_INVALID", {error["code"] for error in result["errors"]})

    def test_step2_rejects_tampered_raw_provider_evidence_with_stale_hash(self) -> None:
        # Given: a complete non-AHD Step 2 bundle with gateway-bound provider evidence
        candidate = _bind_candidate(copy.deepcopy(_fixture("tests/fixtures/step2/non-ahd-solar-fr-ca.json")["candidate"]))
        candidate["evidence_ids"] = [row["evidence_id"] for pillar in candidate["pillars"] for row in pillar["rows"]]
        candidate["language"] = "de"
        candidate["geo"] = {"country_code": "DE", "provider_location_code": 276}
        artifact, release = _predecessor("1c", "GATE-1C")
        bundle = {
            "candidate": candidate,
            "project": _project(),
            "predecessor_artifact": artifact,
            "predecessor_release": release,
            "provider_evidence_records": _provider_records(candidate),
        }
        bundle["provider_evidence_records"][0]["response"]["raw_response"] = {"keyword": "tampered evidence"}
        # When: the public operational preflight verifies the full bundle
        result = validate_step2_preflight(bundle)
        # Then: stale declared evidence cannot bind a verified row
        self.assertFalse(result["valid"])

    def test_operational_preflights_accept_complete_non_ahd_lineage_bundles(self) -> None:
        # Given: non-AHD candidates bound to valid Project V2, artifact, and release records.
        architecture = _bind_candidate(copy.deepcopy(_fixture("tests/fixtures/step1b/non-ahd-outdoor-architecture.json")))
        design = _bind_candidate(copy.deepcopy(_fixture("tests/fixtures/step1c/non-ahd-outdoor-design-system.json")))
        template = _bind_candidate(copy.deepcopy(_fixture("tests/fixtures/step1c/non-ahd-outdoor-template.json")))
        template["source_artifact_ids"] = ["artifact-predecessor-0001", design["artifact_id"]]
        step2 = _bind_candidate(copy.deepcopy(_fixture("tests/fixtures/step2/non-ahd-solar-fr-ca.json")["candidate"]))
        step2["evidence_ids"] = [row["evidence_id"] for pillar in step2["pillars"] for row in pillar["rows"]]
        step2["language"] = "de"
        step2["geo"] = {"country_code": "DE", "provider_location_code": 276}
        provider_records = _provider_records(step2)
        step3_fixture = _fixture("tests/fixtures/step3/non-ahd-solar-fr-ca.json")
        step3 = _bind_candidate(copy.deepcopy(step3_fixture["candidate"]))
        step3.pop("input_sha256", None)
        step3.pop("output_sha256", None)
        step3.update(derive_step3_plan_fields(step2))
        step3["evidence_ids"] = step2["evidence_ids"]
        schema = _fixture("standards/outputs/step-3-plan.schema.json")
        self.assertEqual([], [error.message for error in Draft202012Validator(schema).iter_errors(step3)])
        step3b_bundle = copy.deepcopy(_fixture("tests/fixtures/step3b/non-ahd-product-bundle.json"))
        _bind_candidate(step3b_bundle["adjustment"])
        step3b_bundle["adjustment"].pop("deployment_id", None)
        step3b_bundle["adjustment"]["source_artifact_ids"] = ["artifact-predecessor-0001"]
        step3b_bundle["adjustment"]["source_plan"].update({"artifact_id": "artifact-predecessor-0001", "revision": 1, "content_sha256": "b" * 64})
        step4a_bundle = copy.deepcopy(_fixture("tests/fixtures/step4a/non-ahd-b2b-bundle.json"))
        _bind_candidate(step4a_bundle["briefing"])
        step4a_bundle["briefing"]["deployment_id"] = "deployment-national-b2b-de"
        step4a_bundle["claim_ledger"]["project_id"] = "project-national-b2b"
        jsonld = {"@context": "https://schema.org", "@graph": [{"@type": "Product", "name": "Non-AHD B2B briefing"}]}
        graph_bytes = json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        step4a_bundle["briefing"]["jsonld"] = {"level": "basic", "graph": jsonld, "graph_hash": hashlib.sha256(graph_bytes).hexdigest()}
        step4a_bundle["briefing"]["claim_bindings"] = [{"claim_id": claim["claim_id"], "graph_node_id": "https://example.invalid/briefing#product"} for claim in step4a_bundle["claim_ledger"]["claims"]]
        step4a_bundle["briefing"]["jsonld"]["graph"]["@graph"][0]["@id"] = "https://example.invalid/briefing#product"
        graph_bytes = json.dumps(step4a_bundle["briefing"]["jsonld"]["graph"], ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        step4a_bundle["briefing"]["jsonld"]["graph_hash"] = hashlib.sha256(graph_bytes).hexdigest()
        step4b_bundle = copy.deepcopy(_fixture("tests/fixtures/step4b/non-ahd-product-bundle.json"))
        _bind_candidate(step4b_bundle["page_spec"])
        step4b_bundle["page_spec"]["language"] = "de"
        step4b_bundle["page_spec"]["locale"] = "de-DE"
        step4b_bundle["page_spec"]["service_area"]["areas"] = ["Germany"]
        step4b_bundle["staging_evidence"]["project_id"] = "project-national-b2b"
        step4b_bundle["staging_evidence"]["deployment_id"] = "deployment-national-b2b-de"
        graph4b = {"@context": "https://schema.org", "@graph": [{"@id": "https://example.invalid/page#product", "@type": "Product", "name": "Verified page"}]}
        step4b_bundle["page_spec"]["jsonld"] = {"level": "basic", "graph": graph4b, "graph_hash": hashlib.sha256(json.dumps(graph4b, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()}
        page_payload = dict(step4b_bundle["page_spec"])
        page_payload.pop("content_sha256", None)
        content_hash = hashlib.sha256(json.dumps(page_payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
        step4b_bundle["page_spec"]["content_sha256"] = content_hash
        step4b_bundle["staging_evidence"]["content_sha256"] = content_hash

        cases = (
            ("1b", "1", "GATE-1", {"candidate": architecture, "approved_content_ids": [item["content_id"] for item in architecture["content_decisions"]]}, lambda bundle: validate_step1b_preflight(bundle)),
            ("1c", "1b", "GATE-1B", {"design": design, "templates": [template]}, lambda bundle: validate_step1c_preflight(bundle)),
            ("2", "1c", "GATE-1C", {"candidate": step2}, validate_step2_preflight),
            ("3", "2", "GATE-2", {"candidate": step3, "execution_identity": {"project_id": step3["project_id"], "run_id": step3["run_id"], "step_id": step3["step_id"], "target_revision": step3["revision"]}}, validate_step3_preflight),
            ("3b", "3", "GATE-3", step3b_bundle, validate_step3b_preflight),
            ("4a", "3", "GATE-3", step4a_bundle, validate_step4a_preflight),
            ("4b", "4a", "GATE-4A", step4b_bundle, validate_step4b_preflight),
        )
        for current_step, predecessor_step, gate_id, bundle, preflight in cases:
            with self.subTest(step_id=current_step):
                artifact, release = _predecessor(predecessor_step, gate_id)
                if current_step == "3":
                    predecessor_content = json.dumps(step2, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
                    artifact["content_sha256"] = hashlib.sha256(predecessor_content.encode("utf-8")).hexdigest()
                    release["artifact_sha256"] = artifact["content_sha256"]
                    bundle["predecessor_content"] = predecessor_content
                if current_step == "2":
                    bundle["provider_evidence_records"] = provider_records
                bundle.update({"project": _project(), "predecessor_artifact": artifact, "predecessor_release": release})
                # When: the public operational preflight validates the complete bundle.
                result = preflight(bundle)
                # Then: the released predecessor supports the exact workflow transition.
                self.assertTrue(result["valid"], result["errors"])
