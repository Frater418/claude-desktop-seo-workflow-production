from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from services.step4a_preflight.validator import validate_step4a_candidate, validate_step4a_preflight
from tests.support.step4a_fixtures import load_fixture as _load_fixture


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "step4a"


def load_fixture(name: str) -> dict:
    return _load_fixture(FIXTURES, name)


def evidence_container(*, body: str, section_id: str = "evidence-section-0001") -> dict[str, object]:
    return {
        "section_id": section_id,
        "heading": "Simulated evidence summary",
        "body": body,
        "evidence_ids": ["evidence-serp-0001"],
        "data_points": [
            {
                "label": "Simulated review status",
                "value": "local-only",
                "source_evidence_ids": ["evidence-serp-0001"],
            }
        ],
    }


def evidence_body(word_count: int = 130) -> str:
    return " ".join("word" for _ in range(word_count))


class Step4AContractTests(unittest.TestCase):
    def test_pq0_4a_001_rejects_hero_direct_answer_outside_computed_word_range(self) -> None:
        # Given: the complete simulated Step 4A baseline.
        bundle = load_fixture("positive-bundle.json")
        self.assertTrue(validate_step4a_candidate(bundle)["valid"])

        # When: the Hero Direct Answer has 49 normalized words.
        candidate = deepcopy(bundle)
        candidate["briefing"]["hero_direct_answer"]["text"] = " ".join("word" for _ in range(49))
        result = validate_step4a_candidate(candidate)

        # Then: the computed word-count contract rejects only the Hero field.
        self.assertIn("ERROR_STEP4A_HERO_WORD_COUNT_INVALID", {error["code"] for error in result["errors"]})

    def test_pq0_4a_004_rejects_invalid_semantic_triples_at_the_candidate_seam(self) -> None:
        # Given: the complete simulated Step 4A baseline.
        bundle = load_fixture("positive-bundle.json")
        self.assertTrue(validate_step4a_candidate(bundle)["valid"])

        # When: each candidate isolates one semantic-triple defect.
        scenarios = (
            ("cardinality", lambda candidate: candidate["briefing"]["semantic_triples"].pop()),
            ("duplicate", lambda candidate: candidate["briefing"]["semantic_triples"].append({**candidate["briefing"]["semantic_triples"][0], "triple_id": "triple-duplicate-0001"})),
            ("malformed", lambda candidate: candidate["briefing"]["semantic_triples"][0].update({"subject": "   "})),
            ("unresolved-evidence", lambda candidate: candidate["briefing"]["semantic_triples"][0].update({"evidence_ids": ["evidence-unknown-0001"]})),
        )

        # Then: every semantic defect has its own stable error code.
        expected_codes = {
            "cardinality": "ERROR_STEP4A_SEMANTIC_TRIPLE_CARDINALITY_INVALID",
            "duplicate": "ERROR_STEP4A_SEMANTIC_TRIPLE_DUPLICATE",
            "malformed": "ERROR_STEP4A_SEMANTIC_TRIPLE_TEXT_INVALID",
            "unresolved-evidence": "ERROR_STEP4A_SEMANTIC_TRIPLE_EVIDENCE_UNRESOLVED",
        }
        for name, mutate in scenarios:
            with self.subTest(name=name):
                candidate = deepcopy(bundle)
                mutate(candidate)
                result = validate_step4a_candidate(candidate)
                self.assertIn(expected_codes[name], {error["code"] for error in result["errors"]})

    def test_pq0_4a_005_rejects_invalid_evidence_bodies_sections_and_references_at_the_candidate_seam(self) -> None:
        # Given: the complete simulated Step 4A baseline.
        bundle = load_fixture("pq0-4a-005-positive.json")
        self.assertTrue(validate_step4a_candidate(bundle)["valid"])
        fixture_result = validate_step4a_candidate(load_fixture("pq0-4a-005-negative.json"))
        self.assertIn("ERROR_STEP4A_EVIDENCE_BODY_WORD_COUNT_INVALID", {error["code"] for error in fixture_result["errors"]})

        # When: each candidate isolates one required evidence-container defect.
        scenarios = (
            ("body-word-count", lambda candidate: candidate["briefing"].update({"evidence_containers": [evidence_container(body=evidence_body(129))]})),
            ("duplicate-section", lambda candidate: candidate["briefing"].update({"evidence_containers": [evidence_container(body=evidence_body()), evidence_container(body=evidence_body(), section_id="evidence-section-0001")] })),
            ("unresolved-container-evidence", lambda candidate: candidate["briefing"].update({"evidence_containers": [{**evidence_container(body=evidence_body()), "evidence_ids": ["evidence-unknown-0001"]}]})),
            ("unresolved-data-point-evidence", lambda candidate: candidate["briefing"].update({"evidence_containers": [{**evidence_container(body=evidence_body()), "data_points": [{"label": "Simulated review status", "value": "local-only", "source_evidence_ids": ["evidence-unknown-0001"]}]}]})),
            ("out-of-container-data-point-evidence", lambda candidate: candidate["briefing"].update({"evidence_containers": [{**evidence_container(body=evidence_body()), "data_points": [{"label": "Simulated review status", "value": "local-only", "source_evidence_ids": ["evidence-medical-0001"]}]}]})),
        )

        # Then: every semantic defect has its own stable error code.
        expected_codes = {
            "body-word-count": "ERROR_STEP4A_EVIDENCE_BODY_WORD_COUNT_INVALID",
            "duplicate-section": "ERROR_STEP4A_EVIDENCE_SECTION_ID_DUPLICATE",
            "unresolved-container-evidence": "ERROR_STEP4A_EVIDENCE_UNRESOLVED",
            "unresolved-data-point-evidence": "ERROR_STEP4A_EVIDENCE_UNRESOLVED",
            "out-of-container-data-point-evidence": "ERROR_STEP4A_EVIDENCE_UNRESOLVED",
        }
        for name, mutate in scenarios:
            with self.subTest(name=name):
                candidate = deepcopy(bundle)
                self.assertTrue(validate_step4a_candidate(candidate)["valid"])
                mutate(candidate)
                result = validate_step4a_candidate(candidate)
                self.assertIn(expected_codes[name], {error["code"] for error in result["errors"]})

    def test_pq0_4a_006_rejects_missing_or_conflicting_forms_and_inconsistent_tables_at_the_candidate_seam(self) -> None:
        # Given: the complete simulated Step 4A baseline.
        bundle = load_fixture("pq0-4a-006-positive.json")
        self.assertTrue(validate_step4a_candidate(bundle)["valid"])
        fixture_result = validate_step4a_candidate(load_fixture("pq0-4a-006-negative.json"))
        self.assertIn("ERROR_STEP4A_EVIDENCE_FORM_INVALID", {error["code"] for error in fixture_result["errors"]})

        # When: each candidate isolates one evidence form defect.
        scenarios = (
            ("missing-form", lambda candidate: candidate["briefing"].update({"evidence_containers": [{key: value for key, value in evidence_container(body=evidence_body()).items() if key != "data_points"}]})),
            ("both-forms", lambda candidate: candidate["briefing"].update({"evidence_containers": [{**evidence_container(body=evidence_body()), "table": {"caption": "Simulated comparison", "columns": ["Status", "Scope"], "rows": [["Local", "Simulated"]]}}]})),
            ("table-width", lambda candidate: candidate["briefing"].update({"evidence_containers": [{key: value for key, value in evidence_container(body=evidence_body()).items() if key != "data_points"} | {"table": {"caption": "Simulated comparison", "columns": ["Status", "Scope"], "rows": [["Local"]]}}]})),
        )

        # Then: form selection and table-width rules report stable codes.
        expected_codes = {
            "missing-form": "ERROR_STEP4A_EVIDENCE_FORM_INVALID",
            "both-forms": "ERROR_STEP4A_EVIDENCE_FORM_INVALID",
            "table-width": "ERROR_STEP4A_EVIDENCE_TABLE_WIDTH_INVALID",
        }
        for name, mutate in scenarios:
            with self.subTest(name=name):
                candidate = deepcopy(bundle)
                self.assertTrue(validate_step4a_candidate(candidate)["valid"])
                mutate(candidate)
                result = validate_step4a_candidate(candidate)
                self.assertIn(expected_codes[name], {error["code"] for error in result["errors"]})

    def test_pq0_4a_007_requires_a_complete_copywriter_briefing_at_the_candidate_seam(self) -> None:
        # Given: a complete typed Copywriter briefing baseline.
        bundle = load_fixture("pq0-4a-007-positive.json")
        self.assertTrue(validate_step4a_candidate(bundle)["valid"])
        fixture_result = validate_step4a_candidate(load_fixture("pq0-4a-007-negative.json"))
        self.assertIn("ERROR_STEP4A_BRIEFING_GUIDANCE_INCOMPLETE", {error["code"] for error in fixture_result["errors"]})

        # When: one required briefing field is incomplete.
        candidate = deepcopy(bundle)
        candidate["briefing"]["briefing_sections"]["definitive_language_guidance"]["prohibited_patterns"] = []
        result = validate_step4a_candidate(candidate)

        # Then: the Copywriter handoff reports its dedicated stable code.
        self.assertIn("ERROR_STEP4A_BRIEFING_GUIDANCE_INCOMPLETE", {error["code"] for error in result["errors"]})

    def test_pq0_4a_008_requires_exact_enhanced_geo_entity_correspondence_at_the_candidate_seam(self) -> None:
        # Given: an enhanced GEO baseline using the strict validator's /wiki/ Wikidata authority.
        bundle = load_fixture("pq0-4a-008-positive.json")
        self.assertTrue(validate_step4a_candidate(bundle)["valid"])
        fixture_result = validate_step4a_candidate(load_fixture("pq0-4a-008-negative.json"))
        self.assertIn("ERROR_STEP4A_WIKIDATA_URI_INVALID", {error["code"] for error in fixture_result["errors"]})

        # When: each candidate isolates one entity-binding defect.
        scenarios = (
            ("invalid-wikidata", lambda candidate: candidate["briefing"]["entity_bindings"]["about"][0].update({"wikidata_uri": "https://www.wikidata.org/entity/Q1"})),
            ("overlap", lambda candidate: candidate["briefing"]["entity_bindings"]["mentions"].__setitem__(0, deepcopy(candidate["briefing"]["entity_bindings"]["about"][0]))),
            ("unresolved-node", lambda candidate: candidate["briefing"]["entity_bindings"]["mentions"][0].update({"graph_node_id": "https://example.invalid/briefing#missing"})),
            ("correspondence", lambda candidate: candidate["briefing"]["jsonld"]["graph"]["@graph"][0].update({"mentions": []})),
        )
        expected_codes = {
            "invalid-wikidata": "ERROR_STEP4A_WIKIDATA_URI_INVALID",
            "overlap": "ERROR_STEP4A_ENTITY_OVERLAP_OR_DUPLICATE",
            "unresolved-node": "ERROR_STEP4A_ENTITY_NODE_UNRESOLVED",
            "correspondence": "ERROR_STEP4A_JSONLD_CORRESPONDENCE_MISMATCH",
        }
        for name, mutate in scenarios:
            with self.subTest(name=name):
                candidate = deepcopy(bundle)
                mutate(candidate)
                result = validate_step4a_candidate(candidate)
                self.assertIn(expected_codes[name], {error["code"] for error in result["errors"]})

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

    def test_matrix_positive_fixtures_are_raw_schema_and_candidate_valid(self) -> None:
        for identifier in ("001", "004", "005", "006", "007", "008"):
            with self.subTest(identifier=identifier):
                bundle = json.loads((FIXTURES / f"pq0-4a-{identifier}-positive.json").read_text(encoding="utf-8"))
                for schema_name, value in (("step-4a-briefing.schema.json", bundle["briefing"]), ("claim-ledger.schema.json", bundle["claim_ledger"])):
                    schema = json.loads((ROOT / "standards" / "outputs" / schema_name).read_text(encoding="utf-8"))
                    self.assertEqual([], list(Draft202012Validator(schema).iter_errors(value)))
                self.assertTrue(validate_step4a_candidate(bundle)["valid"])

    def test_matrix_negative_fixtures_are_raw_and_isolate_stable_codes(self) -> None:
        expected_codes = {"001": "ERROR_STEP4A_HERO_WORD_COUNT_INVALID", "004": "ERROR_STEP4A_SEMANTIC_TRIPLE_CARDINALITY_INVALID", "005": "ERROR_STEP4A_EVIDENCE_BODY_WORD_COUNT_INVALID", "006": "ERROR_STEP4A_EVIDENCE_FORM_INVALID", "007": "ERROR_STEP4A_BRIEFING_GUIDANCE_INCOMPLETE", "008": "ERROR_STEP4A_WIKIDATA_URI_INVALID"}
        for identifier, expected_code in expected_codes.items():
            with self.subTest(identifier=identifier):
                bundle = json.loads((FIXTURES / f"pq0-4a-{identifier}-negative.json").read_text(encoding="utf-8"))
                self.assertIn(expected_code, {error["code"] for error in validate_step4a_candidate(bundle)["errors"]})


if __name__ == "__main__":
    unittest.main()
