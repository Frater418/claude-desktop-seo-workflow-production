from __future__ import annotations

import hashlib
import json
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker
from services.operator_api.artifact_revision_types import build_artifact_record
from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet
from services.operator_api.step_validation import GateContext, StepValidationError, StepValidationService, _bind_provider_documents
from tests.support.neutral_step4a import build_neutral_step4a_fixture
from tests.support.neutral_step4b import build_neutral_step4b_fixture


ROOT = Path(__file__).resolve().parents[1]


def _canonical(value: dict[str, object]) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _project() -> dict[str, object]:
    project = json.loads((ROOT / "tests/fixtures/domain/real-customer-matrix/national-b2b.json").read_text(encoding="utf-8"))
    project["project_id"] = "project-neutral"
    project["tenant"]["tenant_id"] = "tenant-neutral"
    return project


def _manifest() -> dict[str, object]:
    return json.loads((ROOT / "tests/fixtures/operator/neutral-step0-manifest.json").read_text(encoding="utf-8"))


def _bundle() -> dict[str, object]:
    project = _project()
    return {"project": project, "accepted_intake": {"source_sha256": "68cf4c5938b8e44ba95650155ba8706b55627fe8017fbbb7d9ea1fb524b82526", "reviewed": {"project_name": "National B2B", "project_v2": project}}}


def _output(content: bytes) -> ProviderOutput:
    return ProviderOutput(
        contract_id="https://heartweb.example/schema/manifest.schema.json",
        content_bytes=content,
        content_sha256=hashlib.sha256(content).hexdigest(),
        content_type="application/json",
        tenant_id="tenant-neutral", project_id="project-neutral", run_id="run-neutral-0001", step_id="0",
        idempotency_key="neutral-step-zero", parent_revision=1, target_revision=2,
        created_at=datetime(2026, 8, 20, 12, 0, tzinfo=UTC),
    )


def _step2_output(content: bytes) -> ProviderOutput:
    registry = json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8"))
    contract_id = next(entry["output_contracts"][0]["contract_id"] for entry in registry["entries"] if entry["step_id"] == "2" and entry["active"])
    return ProviderOutput(
        contract_id=contract_id,
        content_bytes=content,
        content_sha256=hashlib.sha256(content).hexdigest(),
        content_type="application/json",
        tenant_id="tenant-pq2-local",
        project_id="project-pq2-local-001",
        run_id="run-pq2-local-001",
        step_id="2",
        idempotency_key="pq2-canonical-boundary",
        parent_revision=1,
        target_revision=2,
        created_at=datetime(2026, 8, 20, 12, 20, tzinfo=UTC),
    )


def _context(content: bytes) -> GateContext:
    return GateContext.model_validate({"site_status": "non_existing_site", "configured_tools": [], "available_tools": [], "not_applicable_decisions": {}, "evidence_by_gate": {"qg-domain-contract": {"schema_id": "https://heartweb.example/schema/manifest.schema.json", "schema_version": "1.0.0", "artifact_sha256": hashlib.sha256(content).hexdigest(), "validator_result": "simulated:fixture-validated"}}})


class StepValidationServiceTests(unittest.TestCase):
    def test_generates_schema_valid_validator_backed_step_zero_qgr_without_mutation(self) -> None:
        project = _project()
        content = _canonical(_manifest())
        output_set = ProviderOutputSet.from_registry(
            json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8")), primary=_output(content)
        )
        bundle = _bundle()

        result = StepValidationService.from_root(ROOT).validate(
            output_set, "a" * 64, bundle, _context(content)
        )

        self.assertEqual(1, len(result.artifact_records))
        self.assertEqual("passed", result.quality_gate_runs[0]["result"])
        self.assertEqual("simulated:fixture-validated", result.quality_gate_runs[0]["evidence"]["validator_result"])
        qgr_schema = json.loads((ROOT / "standards/runtime/quality-gate-run.schema.json").read_text(encoding="utf-8"))
        self.assertEqual([], list(Draft202012Validator(qgr_schema, format_checker=FormatChecker()).iter_errors(result.quality_gate_runs[0])))
        self.assertEqual({"project": project, "accepted_intake": {"source_sha256": "68cf4c5938b8e44ba95650155ba8706b55627fe8017fbbb7d9ea1fb524b82526", "reviewed": {"project_name": "National B2B", "project_v2": project}}}, bundle)

    def test_rejects_hash_correct_schema_invalid_provider_output_before_preflight(self) -> None:
        content = _canonical({"simulated": True})
        output_set = ProviderOutputSet.from_registry(
            json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8")), primary=_output(content)
        )

        with self.assertRaisesRegex(StepValidationError, "ERROR_OUTPUT_SCHEMA_INVALID"):
            StepValidationService.from_root(ROOT).validate(
                output_set, "a" * 64, {"project": _project()}, _context(content)
            )

    def test_rejects_noncanonical_step2_provider_bytes_before_artifact_records(self) -> None:
        # Given: one schema-valid Step 2 candidate in canonical and pretty-printed forms
        candidate = json.loads((ROOT / "tests/fixtures/step2/pq0-2-canonical-candidate.json").read_text(encoding="utf-8"))["candidate"]
        canonical = _canonical(candidate)
        noncanonical = json.dumps(candidate, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        registry = json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8"))
        canonical_outputs = ProviderOutputSet.from_registry(registry, primary=_step2_output(canonical))
        noncanonical_outputs = ProviderOutputSet.from_registry(registry, primary=_step2_output(noncanonical))
        service = StepValidationService.from_root(ROOT)
        gate_context = GateContext.model_validate({"evidence_by_gate": {}})
        bundle = {"candidate": candidate, "predecessor_artifact": {"artifact_id": "artifact-predecessor-0001"}}
        # When: canonical bytes cross the Step 2 output-contract boundary
        with patch.object(StepValidationService, "_validate_specialized"), patch.object(StepValidationService, "_machine_qgrs", return_value=()), patch("services.operator_api.step_validation._render", return_value={}):
            result = service.validate(canonical_outputs, "a" * 64, bundle, gate_context)
        # Then: the exact canonical document reaches artifact record construction
        self.assertEqual(canonical_outputs.primary.content_sha256, result.artifact_records[0].content_sha256)
        # When: semantically identical but noncanonical bytes cross the same boundary
        with patch.object(StepValidationService, "_validate_specialized"), patch.object(StepValidationService, "_machine_qgrs", return_value=()), patch("services.operator_api.step_validation._render", return_value={}), patch("services.operator_api.step_validation.build_artifact_record") as build_artifact_record:
            with self.assertRaisesRegex(StepValidationError, "ERROR_OUTPUT_CONTRACT_INVALID"):
                service.validate(noncanonical_outputs, "a" * 64, bundle, gate_context)
        # Then: malformed contract bytes stop before artifact record construction
        build_artifact_record.assert_not_called()

    def test_rejects_missing_or_unknown_machine_gate_evidence(self) -> None:
        content = _canonical(_manifest())
        output_set = ProviderOutputSet.from_registry(
            json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8")), primary=_output(content)
        )
        invalid = GateContext.model_validate({"site_status": "non_existing_site", "configured_tools": [], "available_tools": [], "not_applicable_decisions": {}, "evidence_by_gate": {"qg-domain-contract": {"schema_id": "https://heartweb.example/schema/manifest.schema.json", "schema_version": "1.0.0", "artifact_sha256": hashlib.sha256(content).hexdigest(), "unknown": "fixture"}}})

        with self.assertRaisesRegex(StepValidationError, "ERROR_QUALITY_GATE_EVIDENCE_INVALID"):
            StepValidationService.from_root(ROOT).validate(output_set, "a" * 64, _bundle(), invalid)

    def test_rejects_3b_as_non_initial_route(self) -> None:
        content = _canonical(_manifest())
        primary = _output(content).model_copy(update={"step_id": "3b"})
        output_set = ProviderOutputSet.model_validate({"primary": primary, "supporting": ()}, context={"expected_contract_ids": (primary.contract_id,)})

        with self.assertRaisesRegex(StepValidationError, "ERROR_INITIAL_ROUTE_STEP_INVALID"):
            StepValidationService.from_root(ROOT).validate(output_set, "a" * 64, {}, {})

    def test_rejects_specialized_candidate_that_differs_from_validated_provider_document(self) -> None:
        # Given: independently valid-looking specialized and provider documents
        provider = {"inventory_id": "inventory-provider", "items": []}
        bundle = {"inventory": {"inventory_id": "inventory-edited", "items": []}}
        # When: specialized validation binds the parsed provider document
        # Then: a caller cannot pair unrelated candidate content with validated bytes
        with self.assertRaisesRegex(StepValidationError, "ERROR_OUTPUT_CONTRACT_INVALID"):
            _bind_provider_documents("1", bundle, (provider,))

    def test_binds_exact_provider_documents_for_every_specialized_step(self) -> None:
        mappings = {
            "1": ({"inventory": {"value": "edited"}}, ({"value": "provider"},)),
            "1b": ({"candidate": {"value": "edited"}}, ({"value": "provider"},)),
            "1c": ({"design": {"value": "provider"}, "templates": [{"value": "edited"}]}, ({"value": "provider"}, {"value": "provider"})),
            "2": ({"candidate": {"value": "edited"}}, ({"value": "provider"},)),
            "3": ({"candidate": {"value": "edited"}}, ({"value": "provider"},)),
            "4a": ({"briefing": {"value": "edited"}, "claim_ledger": {"value": "provider"}}, ({"value": "provider"}, {"value": "provider"})),
            "4b": ({"page_spec": {"value": "edited"}, "staging_evidence": {"value": "provider"}}, ({"value": "provider"}, {"value": "provider"})),
        }
        for step_id, (bundle, documents) in mappings.items():
            with self.subTest(step_id=step_id), self.assertRaisesRegex(StepValidationError, "ERROR_OUTPUT_CONTRACT_INVALID"):
                _bind_provider_documents(step_id, bundle, documents)

    def test_passes_trusted_provider_execution_identity_to_specialized_preflight(self) -> None:
        # Given: a valid provider-backed Step 0 output and service bundle
        content = _canonical(_manifest())
        output = _output(content)
        output_set = ProviderOutputSet.from_registry(
            json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8")), primary=output
        )
        # When: validation invokes specialized preflight
        with patch("services.operator_api.step_validation._validator", return_value={"valid": True, "errors": []}) as validator:
            StepValidationService.from_root(ROOT).validate(output_set, "a" * 64, _bundle(), _context(content))
        # Then: preflight receives identity derived from ProviderOutput, not the bundle
        self.assertEqual(
            {"project_id": output.project_id, "run_id": output.run_id, "step_id": output.step_id, "target_revision": output.target_revision},
            validator.call_args.args[1]["execution_identity"],
        )

    def test_step4a_generates_only_local_claims_and_schema_qgr_from_exact_evidence(self) -> None:
        fixture = build_neutral_step4a_fixture(
            ROOT,
            _project(),
            {"artifact_id": "artifact-step3-0001"},
            {"release_id": "release-step3-0001"},
            {"quality_gate_run_id": "qgr-step3-0001"},
            {"run_id": "run-neutral-step4a-0001", "revision": 1},
        )

        artifact = build_artifact_record(fixture.output_set.primary, "a" * 64, ())
        result = StepValidationService.from_root(ROOT)._machine_qgrs("4a", artifact, fixture.gate_context)

        qgr_by_gate = {record["quality_gate_id"]: record for record in result}
        local = qgr_by_gate["qg-step4a-claims-and-schema"]
        self.assertEqual(
            {
                "claim_ledger": "simulated-neutral",
                "validator_levels": "basic",
                "schema_hash": fixture.bundle["briefing"]["jsonld"]["graph_hash"],
                "review_decision": "simulated-approved",
            },
            local["evidence"],
        )
        self.assertNotIn("qg-step4a-external-rich-results", qgr_by_gate)

    def test_step4b_submit_for_gate_generates_no_external_staging_qgr(self) -> None:
        fixture = build_neutral_step4b_fixture(
            ROOT,
            _project(),
            {"artifact_id": "artifact-step3-0001"},
            {"release_id": "release-step3-0001"},
            {"quality_gate_run_id": "qgr-step3-0001"},
            {"run_id": "run-neutral-step4b-0001", "revision": 1},
        )

        artifact = build_artifact_record(fixture.output_set.primary, "a" * 64, ())
        result = StepValidationService.from_root(ROOT)._machine_qgrs("4b", artifact, fixture.gate_context)

        self.assertEqual({"qg-domain-contract"}, {record["quality_gate_id"] for record in result})
        self.assertFalse(any(record["quality_gate_id"] == "qg-step4b-staging-technical" for record in result))

if __name__ == "__main__":
    unittest.main()
