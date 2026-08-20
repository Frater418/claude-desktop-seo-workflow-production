from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from services.step3b_preflight.validator import validate_step3b_candidate, validate_step3b_preflight


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "step3b"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class Step3BContractTests(unittest.TestCase):
    def test_preflight_accepts_non_ahd_revision_when_source_plan_is_immutable(self) -> None:
        # Given: a non-AHD product roadmap adjustment fixture.
        bundle = load_fixture("non-ahd-product-bundle.json")

        # When: the Step 3b preflight validates the candidate.
        result = validate_step3b_candidate(bundle["adjustment"])

        # Then: the generic candidate is accepted without a market-specific rule.
        self.assertTrue(result["valid"], result["errors"])

    def test_positive_adjustment_validates(self) -> None:
        schema = json.loads((ROOT / "standards" / "outputs" / "step-3b-adjustment.schema.json").read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema).iter_errors(load_fixture("positive-adjustment.json")))
        self.assertEqual([], errors, [error.message for error in errors])

    def test_preflight_accepts_immutable_adjustment_candidate(self) -> None:
        result = validate_step3b_candidate(load_fixture("positive-bundle.json")["adjustment"])
        self.assertTrue(result["valid"], result["errors"])

    def test_preflight_rejects_original_plan_overwrite(self) -> None:
        result = validate_step3b_preflight(load_fixture("overwrite-plan-bundle.json"))
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_STEP3B_PLAN_IMMUTABILITY_INVALID", {error["code"] for error in result["errors"]})


if __name__ == "__main__":
    unittest.main()
