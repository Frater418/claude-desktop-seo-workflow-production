from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from services.step1c_preflight.validator import validate_step1c_candidate


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "step1c"


class Step1CContractTests(unittest.TestCase):
    def test_preflight_accepts_design_and_service_area_template(self) -> None:
        # Given: screenshot-derived tokens and a service-area-safe template.
        design = json.loads((FIXTURES / "positive-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "positive-template.json").read_text(encoding="utf-8"))

        # When: Step 1C validates both canonical artifacts.
        result = validate_step1c_candidate(design, [template])

        # Then: the candidate artifacts are accepted.
        self.assertTrue(result["valid"], result["errors"])

    def test_preflight_accepts_contrasting_non_ahd_design_and_template(self) -> None:
        # Given: outdoor retail design tokens sourced only from fixture screenshot and brand evidence.
        design = json.loads((FIXTURES / "non-ahd-outdoor-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "non-ahd-outdoor-template.json").read_text(encoding="utf-8"))

        # When: Step 1C validates the physical-location template with its fixture-derived design.
        result = validate_step1c_candidate(design, [template])

        # Then: the generic design and template contracts accept the contrasting valid evidence model.
        self.assertTrue(result["valid"], result["errors"])

    def test_non_ahd_design_uses_only_its_fixture_project_evidence(self) -> None:
        # Given: the contrasting fixture design system.
        design = json.loads((FIXTURES / "non-ahd-outdoor-design-system.json").read_text(encoding="utf-8"))

        # When: project evidence is collected from its design decision and accessibility data.
        declared_evidence = set(design["evidence_ids"])
        referenced_evidence = set(design["decision_records"][0]["evidence_ids"]) | set(design["accessibility"]["contrast_evidence_ids"])

        # Then: every design input is the fixture project's screenshot or brand evidence.
        self.assertEqual(declared_evidence, referenced_evidence)

    def test_preflight_rejects_address_claim_for_service_area_only(self) -> None:
        # Given: a template that claims a physical address from service-area evidence.
        design = json.loads((FIXTURES / "positive-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "positive-template.json").read_text(encoding="utf-8"))
        template["location_context"]["physical_address"] = "Example Street 1"

        # When: Step 1C validates the template.
        result = validate_step1c_candidate(design, [template])

        # Then: it rejects unsupported physical-location claims.
        self.assertIn("ERROR_STEP1C_LOCATION_CLAIM_INVALID", {item["code"] for item in result["errors"]})

    def test_preflight_rejects_template_without_accessibility_or_jsonld_references(self) -> None:
        # Given: a template that omits required machine-readable safety fields.
        design = json.loads((FIXTURES / "positive-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "positive-template.json").read_text(encoding="utf-8"))
        template["accessibility"] = copy.deepcopy(template["accessibility"])
        template["accessibility"]["landmarks"] = []
        template["jsonld_references"] = []

        # When: Step 1C validates the template.
        result = validate_step1c_candidate(design, [template])

        # Then: it rejects incomplete accessibility and JSON-LD references.
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("ERROR_STEP1C_ACCESSIBILITY_INVALID", codes)
        self.assertIn("ERROR_STEP1C_JSONLD_REFERENCE_INVALID", codes)


if __name__ == "__main__":
    unittest.main()
