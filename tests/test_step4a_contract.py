from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from services.step4a_preflight.validator import validate_step4a_candidate, validate_step4a_preflight


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "step4a"


def load_fixture(name: str) -> dict:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    briefing = value.get("briefing", value)
    if isinstance(briefing, dict) and isinstance(briefing.get("jsonld"), dict):
        graph = {"@context": "https://schema.org", "@graph": [{"@id": "https://example.invalid/briefing#product", "@type": "Product", "name": "Verified briefing"}]}
        canonical = json.dumps(graph, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        briefing["jsonld"] = {"level": "basic", "graph": graph, "graph_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}
        ledger = value.get("claim_ledger")
        claims = ledger.get("claims", []) if isinstance(ledger, dict) else [{"claim_id": "claim-placeholder-0001"}]
        briefing["claim_bindings"] = [{"claim_id": claim["claim_id"], "graph_node_id": "https://example.invalid/briefing#product"} for claim in claims]
    return value


class Step4AContractTests(unittest.TestCase):
    def test_preflight_accepts_non_ahd_b2b_candidate_when_evidence_is_bound(self) -> None:
        # Given: a non-AHD B2B briefing and claim ledger fixture.
        bundle = load_fixture("non-ahd-b2b-bundle.json")

        # When: the Step 4a preflight validates the candidate.
        result = validate_step4a_candidate(bundle)

        # Then: the generic candidate is accepted without a market-specific rule.
        self.assertTrue(result["valid"], result["errors"])

    def test_positive_briefing_and_claim_ledger_validate(self) -> None:
        briefing = load_fixture("positive-briefing.json")
        ledger = load_fixture("positive-claim-ledger.json")
        for schema_name, instance in (
            ("step-4a-briefing.schema.json", briefing),
            ("claim-ledger.schema.json", ledger),
        ):
            schema = json.loads((ROOT / "standards" / "outputs" / schema_name).read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema).iter_errors(instance))
            self.assertEqual([], errors, [error.message for error in errors])

    def test_preflight_accepts_evidence_bound_ymyl_candidate(self) -> None:
        result = validate_step4a_candidate(load_fixture("positive-bundle.json"))
        self.assertTrue(result["valid"], result["errors"])

    def test_preflight_rejects_ymyl_claim_without_reviewer_policy(self) -> None:
        result = validate_step4a_preflight(load_fixture("missing-reviewer-policy-bundle.json"))
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_STEP4A_YMYL_CLAIM_INVALID", {error["code"] for error in result["errors"]})


if __name__ == "__main__":
    unittest.main()
