from __future__ import annotations

import unittest
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from services.step2_preflight.validator import validate_step2_candidate, validate_step2_preflight


ROOT = Path(__file__).resolve().parents[1]


def load_fixture() -> dict[str, object]:
    fixture = json.loads((ROOT / "tests/fixtures/step2/non-ahd-solar-fr-ca.json").read_text(encoding="utf-8"))
    fixture["candidate"]["candidate_status"] = "awaiting_gate"
    fixture["candidate"]["evidence_ids"] = [row["evidence_id"] for pillar in fixture["candidate"]["pillars"] for row in pillar["rows"]]
    fixture["candidate"]["language"] = "fr"
    fixture["candidate"]["geo"] = {"country_code": "CA", "provider_location_code": 1001}
    return fixture


class Step2ContractTests(unittest.TestCase):
    def test_accepts_contrasting_non_ahd_keyword_evidence(self) -> None:
        # Given: a non-AHD approved pillar with verified provider rows
        fixture = load_fixture()
        # When: Step 2 preflight evaluates the candidate
        result = validate_step2_candidate({"candidate": fixture["candidate"]})
        # Then: the candidate is ready for an awaiting-gate transition
        self.assertTrue(result["valid"])

    def test_accepts_contrasting_fixture_under_closed_output_contract(self) -> None:
        # Given: a non-AHD Step 2 output fixture and its closed schema
        fixture = load_fixture()
        schema = json.loads((ROOT / "standards/outputs/step-2-keyword-evidence.schema.json").read_text(encoding="utf-8"))
        # When: the schema validates the candidate
        errors = list(Draft202012Validator(schema).iter_errors(fixture["candidate"]))
        # Then: no market, language, pillar or provider specialization is needed
        self.assertEqual([], errors)

    def test_consolidates_incomplete_keyword_evidence_for_operator(self) -> None:
        # Given: an approved pillar below the mandatory evidence threshold
        fixture = load_fixture()
        bundle = {"candidate": fixture["candidate"]}
        bundle["candidate"]["pillars"][0]["rows"] = bundle["candidate"]["pillars"][0]["rows"][:-1]
        # When: Step 2 preflight evaluates the candidate
        result = validate_step2_candidate(bundle)
        # Then: the prompt surface exposes one actionable operator error
        self.assertFalse(result["valid"])
        self.assertEqual(1, len(result["errors"]))
        self.assertEqual("ERROR_STEP2_PREFLIGHT", result["errors"][0]["code"])
