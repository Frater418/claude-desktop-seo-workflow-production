from __future__ import annotations

import unittest
import json
import hashlib
from pathlib import Path

from jsonschema import Draft202012Validator
from services.step3_preflight.validator import validate_step3_candidate, validate_step3_preflight


ROOT = Path(__file__).resolve().parents[1]


def load_fixture() -> dict[str, object]:
    fixture = json.loads((ROOT / "tests/fixtures/step3/non-ahd-solar-fr-ca.json").read_text(encoding="utf-8"))
    fixture["candidate"]["candidate_status"] = "awaiting_gate"
    for value in (fixture["candidate"], fixture["preflight_bundle"]):
        output = {key: value[key] for key in ("weeks", "mandatory_item_ids", "backlog_item_ids", "vertical_links", "horizontal_links")}
        input_payload = {"rows": []}
        value.pop("input_sha256", None)
        value.pop("output_sha256", None)
        value["solver_input"] = json.dumps(input_payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        value["solver_output"] = json.dumps(output, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        value["solver_input_sha256"] = hashlib.sha256(value["solver_input"].encode("utf-8")).hexdigest()
        value["solver_output_sha256"] = hashlib.sha256(value["solver_output"].encode("utf-8")).hexdigest()
    return fixture


class Step3ContractTests(unittest.TestCase):
    def test_accepts_contrasting_non_ahd_deterministic_plan(self) -> None:
        # Given: a non-AHD capacity-bounded plan with both link graphs
        fixture = load_fixture()
        # When: Step 3 preflight evaluates the candidate
        result = validate_step3_candidate(fixture["candidate"])
        # Then: the deterministic plan is ready for an awaiting-gate transition
        self.assertTrue(result["valid"])

    def test_accepts_contrasting_fixture_under_closed_output_contract(self) -> None:
        # Given: a non-AHD Step 3 output fixture and its closed schema
        fixture = load_fixture()
        schema = json.loads((ROOT / "standards/outputs/step-3-plan.schema.json").read_text(encoding="utf-8"))
        # When: the schema validates the candidate
        errors = list(Draft202012Validator(schema).iter_errors(fixture["candidate"]))
        # Then: the plan has no market, language, capacity or link specialization
        self.assertEqual([], errors)

    def test_consolidates_invalid_plan_constraints_for_operator(self) -> None:
        # Given: a plan missing a week, mandatory work, and its horizontal graph
        fixture = load_fixture()
        bundle = fixture["preflight_bundle"]
        bundle["weeks"] = bundle["weeks"][:-1]
        bundle["mandatory_item_ids"] = []
        bundle["horizontal_links"] = []
        # When: Step 3 preflight evaluates the candidate
        result = validate_step3_candidate(bundle)
        # Then: the prompt surface exposes one actionable operator error
        self.assertFalse(result["valid"])
        self.assertEqual(1, len(result["errors"]))
        self.assertEqual("ERROR_STEP3_PREFLIGHT", result["errors"][0]["code"])
