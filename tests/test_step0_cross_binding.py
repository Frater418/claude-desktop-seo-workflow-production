from __future__ import annotations

import hashlib
import json
import unittest
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet
from services.operator_api.step_validation import GateContext, StepValidationError, StepValidationService


ROOT = Path(__file__).resolve().parents[1]
TENANT = "tenant-neutral"
PROJECT = "project-neutral"
RUN = "run-neutral-0001"
INTAKE_SHA256 = "68cf4c5938b8e44ba95650155ba8706b55627fe8017fbbb7d9ea1fb524b82526"


def project() -> dict[str, object]:
    value = json.loads((ROOT / "tests/fixtures/domain/real-customer-matrix/national-b2b.json").read_text(encoding="utf-8"))
    value["project_id"] = PROJECT
    value["tenant"]["tenant_id"] = TENANT
    return value


def neutral_manifest() -> dict[str, object]:
    value = json.loads((ROOT / "tests/fixtures/operator/neutral-step0-manifest.json").read_text(encoding="utf-8"))
    value["project_name"] = "National B2B"
    source_binding = value["source_binding"]
    source_binding["project_v2_sha256"] = hashlib.sha256(json.dumps(project(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    source_binding["intake_source_sha256"] = INTAKE_SHA256
    return value


def output_for(manifest: dict[str, object]) -> ProviderOutputSet:
    registry = json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8"))
    contract = next(entry["output_contracts"][0]["contract_id"] for entry in registry["entries"] if entry["step_id"] == "0")
    content = json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode()
    output = ProviderOutput(
        contract_id=contract,
        content_bytes=content,
        content_sha256=hashlib.sha256(content).hexdigest(),
        content_type="application/json",
        tenant_id=TENANT,
        project_id=PROJECT,
        run_id=RUN,
        step_id="0",
        idempotency_key="idem-step0-cross-binding-0001",
        parent_revision=1,
        target_revision=2,
        created_at=datetime(2026, 8, 20, 12, tzinfo=UTC),
    )
    return ProviderOutputSet.from_registry(registry, primary=output)


def accepted_intake() -> dict[str, object]:
    return {
        "source_sha256": INTAKE_SHA256,
        "reviewed": {
            "project_name": "National B2B",
            "project_v2": project(),
        },
    }


class Step0CrossBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = GateContext.model_validate({"site_status": "non_existing_site", "configured_tools": [], "available_tools": [], "not_applicable_decisions": {}, "evidence_by_gate": {"qg-domain-contract": {"schema_id": "https://heartweb.example/schema/manifest.schema.json", "schema_version": "1.0.0", "artifact_sha256": output_for(neutral_manifest()).primary.content_sha256, "validator_result": "simulated"}}})
        self.bundle = {"project": project(), "accepted_intake": accepted_intake()}

    def validate(self, manifest: dict[str, object]) -> None:
        StepValidationService.from_root(ROOT).validate(output_for(manifest), "a" * 64, self.bundle, self.context)

    def test_accepts_neutral_manifest_bound_to_canonical_project_and_intake(self) -> None:
        # Given: a neutral legacy manifest with canonical source bindings
        manifest = neutral_manifest()

        # When: Step 0 validates the authoritative Project V2 and accepted intake
        self.validate(manifest)

        # Then: the consistently rebadged manifest is accepted

    def test_rejects_rebadged_manifest_with_mismatched_business_scope(self) -> None:
        # Given: every existing binding is rebadged but the content scope remains simCura's
        manifest = neutral_manifest()
        manifest["content_focus"] = "Ambulante Pflege und Verhinderungspflege"

        # When: Step 0 validates cross-customer business semantics
        with self.assertRaisesRegex(StepValidationError, "ERROR_STEP0_CROSS_BINDING_INVALID"):
            self.validate(manifest)

        # Then: rebadging identity cannot admit another customer's content scope

    def test_rejects_rebadged_manifest_with_mismatched_domain(self) -> None:
        # Given: a valid source binding with another customer's deployment domain
        manifest = neutral_manifest()
        manifest["domain"] = "https://simcura-pflege.de"

        # When: Step 0 validates the deployment identity
        with self.assertRaisesRegex(StepValidationError, "ERROR_STEP0_CROSS_BINDING_INVALID"):
            self.validate(manifest)

        # Then: the foreign domain is rejected

    def test_rejects_rebadged_manifest_with_mismatched_customer_name(self) -> None:
        # Given: a valid source binding with another customer's project name
        manifest = neutral_manifest()
        manifest["project_name"] = "simCura Pflegedienst Frankfurt"

        # When: Step 0 validates the customer identity
        with self.assertRaisesRegex(StepValidationError, "ERROR_STEP0_CROSS_BINDING_INVALID"):
            self.validate(manifest)

        # Then: the foreign customer name is rejected

    def test_rejects_intake_with_mismatched_reviewed_project_name(self) -> None:
        # Given: the accepted intake claims a customer other than the canonical Project V2 customer
        intake = deepcopy(accepted_intake())
        intake["reviewed"]["project_name"] = "simCura Pflegedienst Frankfurt"
        self.bundle["accepted_intake"] = intake

        # When: Step 0 validates the accepted intake's persisted review
        with self.assertRaisesRegex(StepValidationError, "ERROR_STEP0_CROSS_BINDING_INVALID"):
            self.validate(neutral_manifest())

        # Then: a rebadged reviewed customer cannot cross-bind the canonical project

    def test_rejects_intake_with_mismatched_reviewed_project_v2(self) -> None:
        # Given: the accepted intake embeds a Project V2 from another customer
        intake = deepcopy(accepted_intake())
        intake["reviewed"]["project_v2"] = json.loads(
            (ROOT / "tests/fixtures/domain/real-customer-matrix/regional-care.json").read_text(encoding="utf-8")
        )
        self.bundle["accepted_intake"] = intake

        # When: Step 0 validates the accepted intake's persisted Project V2
        with self.assertRaisesRegex(StepValidationError, "ERROR_STEP0_CROSS_BINDING_INVALID"):
            self.validate(neutral_manifest())

        # Then: a different embedded Project V2 cannot be accepted

    def test_rejects_intake_missing_reviewed_project_fields(self) -> None:
        # Given: an accepted intake omits either required nested reviewed binding field
        for field in ("project_name", "project_v2"):
            with self.subTest(field=field):
                intake = deepcopy(accepted_intake())
                del intake["reviewed"][field]
                self.bundle["accepted_intake"] = intake

                # When: Step 0 validates the persisted reviewed intake shape
                with self.assertRaisesRegex(StepValidationError, "ERROR_STEP0_CROSS_BINDING_INVALID"):
                    self.validate(neutral_manifest())

                # Then: absent nested semantic bindings fail closed


if __name__ == "__main__":
    unittest.main()
