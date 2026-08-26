from __future__ import annotations

import json
import hashlib
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from services.step4b_preflight.validator import page_content_sha256, staging_evidence_sha256, validate_step4b_candidate, validate_step4b_preflight


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "step4b"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def bind_hashes(bundle: dict) -> None:
    page = bundle["page_spec"]
    graph = page["jsonld"]["graph"]
    canonical_graph = json.dumps(graph, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    page["jsonld"]["graph_hash"] = hashlib.sha256(canonical_graph.encode("utf-8")).hexdigest()
    content_hash = page_content_sha256(page)
    page["content_sha256"] = content_hash
    staging = bundle["staging_evidence"]
    staging["content_sha256"] = content_hash
    for check in staging["checks"]:
        check["content_sha256"] = content_hash
    staging["staging_sha256"] = staging_evidence_sha256(staging)


class Step4BContractTests(unittest.TestCase):
    def test_preflight_accepts_non_ahd_product_candidate_when_evidence_is_complete(self) -> None:
        # Given: a non-AHD product page and staging evidence fixture.
        bundle = load_fixture("non-ahd-product-bundle.json")

        # When: the Step 4b preflight validates the candidate.
        result = validate_step4b_candidate(bundle)

        # Then: the generic candidate is accepted without a market-specific rule.
        self.assertTrue(result["valid"], result["errors"])

    def test_rejects_page_accessibility_and_visual_ids_not_bound_to_staging_checks(self) -> None:
        bundle = load_fixture("non-ahd-product-bundle.json")
        cases = (
            ("accessibility", "axe_evidence_id"),
            ("responsive", "visual_evidence_id"),
        )
        for section, field in cases:
            with self.subTest(field=field):
                changed = deepcopy(bundle)
                changed["page_spec"][section][field] = "evidence-unbound-0001"
                bind_hashes(changed)

                result = validate_step4b_candidate(changed)

                self.assertFalse(result["valid"])
                self.assertIn("ERROR_STEP4B_STAGING_PAGE_EVIDENCE_MISMATCH", {error["code"] for error in result["errors"]})

    def test_pq0_4b_001_accepts_closed_sections_and_rejects_legacy_html(self) -> None:
        # Given: a self-contained local baseline with every approved semantic section.
        bundle = load_fixture("pq0-4b-001-positive.json")
        self.assertTrue(validate_step4b_candidate(bundle)["valid"])

        # When: a legacy freeform HTML field is added to the otherwise valid candidate.
        legacy_bundle = deepcopy(bundle)
        legacy_bundle["page_spec"]["html"] = "<section>Legacy authority</section>"
        content_hash = page_content_sha256(legacy_bundle["page_spec"])
        legacy_bundle["page_spec"]["content_sha256"] = content_hash
        legacy_bundle["staging_evidence"]["content_sha256"] = content_hash
        result = validate_step4b_candidate(legacy_bundle)

        # Then: the closed Page Spec schema rejects independently editable markup.
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_STEP4B_PAGE_INVALID", {error["code"] for error in result["errors"]})

    def test_pq0_4b_001_rejects_invalid_raw_section_fixture(self) -> None:
        # Given: the independently valid canonical baseline.
        self.assertTrue(validate_step4b_candidate(load_fixture("pq0-4b-001-positive.json"))["valid"])

        # When: the raw fixture violates the closed section contract.
        result = validate_step4b_candidate(load_fixture("pq0-4b-001-negative.json"))

        # Then: section structure has a stable preflight error family.
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_STEP4B_SECTION_STRUCTURE_INVALID", {error["code"] for error in result["errors"]})

    def test_pq0_4b_002_accepts_canonical_physical_location_conversion(self) -> None:
        # Given: a self-contained physical-location page bound to Project V2.
        bundle = load_fixture("pq0-4b-002-positive.json")

        # When: the candidate preflight runs without fixture mutation.
        result = validate_step4b_candidate(bundle)

        # Then: its typed conversion and verified location authorities resolve.
        self.assertTrue(result["valid"], result["errors"])

    def test_pq0_4b_002_rejects_unresolved_conversion_reference(self) -> None:
        # Given: the independently valid canonical baseline.
        self.assertTrue(validate_step4b_candidate(load_fixture("pq0-4b-002-positive.json"))["valid"])

        # When: a raw candidate references a CTA outside its authoritative registry.
        result = validate_step4b_candidate(load_fixture("pq0-4b-002-negative.json"))

        # Then: conversion structure fails before later rendering work.
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_STEP4B_CONVERSION_STRUCTURE_INVALID", {error["code"] for error in result["errors"]})

    def test_pq0_4b_005_requires_visible_geo_microdata(self) -> None:
        # Given: a raw candidate that declares the approved visible GEO metadata.
        bundle = load_fixture("pq0-4b-005-positive.json")
        self.assertTrue(validate_step4b_candidate(bundle)["valid"])

        # When: the definition loses only its required Microdata declaration.
        mutated = deepcopy(bundle)
        definition = next(section for section in mutated["page_spec"]["sections"] if section["role"] == "definition")
        definition.pop("microdata")
        content_hash = page_content_sha256(mutated["page_spec"])
        mutated["page_spec"]["content_sha256"] = content_hash
        mutated["staging_evidence"]["content_sha256"] = content_hash
        result = validate_step4b_candidate(mutated)

        # Then: JSON-LD is not accepted as a substitute for visible Microdata.
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_STEP4B_GEO_MARKUP_INVALID", {error["code"] for error in result["errors"]})
        wrong_class = deepcopy(bundle)
        definition = next(section for section in wrong_class["page_spec"]["sections"] if section["role"] == "definition")
        definition["component_classes"] = []
        content_hash = page_content_sha256(wrong_class["page_spec"])
        wrong_class["page_spec"]["content_sha256"] = content_hash
        wrong_class["staging_evidence"]["content_sha256"] = content_hash
        result = validate_step4b_candidate(wrong_class)
        self.assertIn("ERROR_STEP4B_GEO_MARKUP_INVALID", {error["code"] for error in result["errors"]})

    def test_pq0_4b_006_requires_exact_section_graph_correspondence(self) -> None:
        # Given: all nine visible semantic sections bind exactly once to graph nodes.
        bundle = load_fixture("pq0-4b-006-positive.json")
        self.assertTrue(validate_step4b_candidate(bundle)["valid"])

        # When: one additional graph node is introduced without a visible section.
        result = validate_step4b_candidate(load_fixture("pq0-4b-006-negative.json"))

        # Then: the candidate rejects graph-node overreach with a stable code.
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_STEP4B_SECTION_JSONLD_MISMATCH", {error["code"] for error in result["errors"]})
        duplicate = deepcopy(bundle)
        sections = duplicate["page_spec"]["sections"]
        sections[1]["schema_node_id"] = sections[0]["schema_node_id"]
        content_hash = page_content_sha256(duplicate["page_spec"])
        duplicate["page_spec"]["content_sha256"] = content_hash
        duplicate["staging_evidence"]["content_sha256"] = content_hash
        result = validate_step4b_candidate(duplicate)
        self.assertIn("ERROR_STEP4B_SECTION_JSONLD_MISMATCH", {error["code"] for error in result["errors"]})

    def test_pq0_4b_006_rejects_microdata_type_that_differs_from_its_graph_node(self) -> None:
        # Given: the representative page binds each GEO section to one graph node.
        bundle = load_fixture("pq0-4b-006-positive.json")
        self.assertTrue(validate_step4b_candidate(bundle)["valid"])
        definition = next(section for section in bundle["page_spec"]["sections"] if section["role"] == "definition")

        # When: its visible Microdata type differs from the same-ID graph node type.
        definition["microdata"]["itemtype"] = "https://schema.org/Thing"
        bind_hashes(bundle)
        result = validate_step4b_candidate(bundle)

        # Then: the candidate rejects the conflicting type correspondence.
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_STEP4B_SECTION_JSONLD_MISMATCH", {error["code"] for error in result["errors"]})

    def test_page_spec_rejects_empty_consent_bound_tracking_slots(self) -> None:
        # Given: a valid page candidate with tracking slots bound to consent categories.
        bundle = load_fixture("pq0-4b-001-positive.json")

        # When: all typed, inert tracking placeholders are removed.
        bundle["page_spec"]["tracking_slots"] = []
        bind_hashes(bundle)
        result = validate_step4b_candidate(bundle)

        # Then: the closed Page Spec requires at least one consent-bound placeholder.
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_STEP4B_PAGE_INVALID", {error["code"] for error in result["errors"]})

    def test_pq0_4b_004_binds_exact_immutable_staging_evidence(self) -> None:
        # Given: a raw candidate with four local simulated immutable reports.
        bundle = load_fixture("pq0-4b-004-positive.json")
        self.assertTrue(validate_step4b_candidate(bundle)["valid"])
        for check in bundle["staging_evidence"]["checks"]:
            source = check["provenance"]["source"]
            self.assertEqual("local_simulated", check["provenance"]["classification"])
            self.assertTrue(source.startswith("pq4-local-fixture:"))
            self.assertEqual(hashlib.sha256(source.removeprefix("pq4-local-fixture:").encode("utf-8")).hexdigest(), check["report_sha256"])

        # When: each evidence invariant is violated independently.
        mutations = (
            ("duplicate tool", lambda candidate: candidate["staging_evidence"]["checks"].__setitem__(-1, {**candidate["staging_evidence"]["checks"][-1], "tool": "axe"}), "ERROR_STEP4B_STAGING_TOOL_COVERAGE"),
            ("missing tool", lambda candidate: candidate["staging_evidence"]["checks"].pop(), "ERROR_STEP4B_STAGING_TOOL_COVERAGE"),
            ("mismatched page hash", lambda candidate: candidate["page_spec"].__setitem__("content_sha256", "f" * 64), "ERROR_STEP4B_STAGING_CONTENT_BINDING"),
            ("stale staging hash", lambda candidate: candidate["staging_evidence"]["decision_records"].append({}), "ERROR_STEP4B_STAGING_HASH_MISMATCH"),
            ("missing provenance", lambda candidate: candidate["staging_evidence"]["checks"][0].pop("provenance"), "ERROR_STEP4B_STAGING_PROVENANCE_INVALID"),
            ("invalid provenance", lambda candidate: candidate["staging_evidence"]["checks"][0]["provenance"].__setitem__("source", " "), "ERROR_STEP4B_STAGING_PROVENANCE_INVALID"),
            ("legacy status", lambda candidate: candidate["staging_evidence"]["checks"][0].__setitem__("status", "passed"), "ERROR_STEP4B_STAGING_INVALID"),
        )
        for name, mutate, expected_code in mutations:
            with self.subTest(name=name):
                candidate = deepcopy(bundle)
                mutate(candidate)
                if name != "stale staging hash":
                    candidate["staging_evidence"]["staging_sha256"] = staging_evidence_sha256(candidate["staging_evidence"])
                result = validate_step4b_candidate(candidate)

                # Then: semantic failures identify the rejected invariant.
                self.assertFalse(result["valid"])
                self.assertIn(expected_code, {error["code"] for error in result["errors"]})

    def test_pq0_4b_raw_matrix_validates_without_fixture_mutation(self) -> None:
        for fixture_name in (
            "pq0-4b-001-positive.json",
            "pq0-4b-002-positive.json",
            "pq0-4b-004-positive.json",
            "pq0-4b-005-positive.json",
            "pq0-4b-006-positive.json",
        ):
            with self.subTest(fixture_name=fixture_name):
                result = validate_step4b_candidate(load_fixture(fixture_name))
                self.assertTrue(result["valid"], result["errors"])
        for fixture_name, code in (
            ("pq0-4b-005-negative.json", "ERROR_STEP4B_GEO_MARKUP_INVALID"),
            ("pq0-4b-006-negative.json", "ERROR_STEP4B_SECTION_JSONLD_MISMATCH"),
            ("pq0-4b-004-negative.json", "ERROR_STEP4B_STAGING_TOOL_COVERAGE"),
        ):
            with self.subTest(fixture_name=fixture_name):
                result = validate_step4b_candidate(load_fixture(fixture_name))
                self.assertIn(code, {error["code"] for error in result["errors"]})

    def test_positive_page_and_staging_evidence_validate(self) -> None:
        for schema_name, fixture_name in (
            ("step-4b-page-spec.schema.json", "positive-page-spec.json"),
            ("staging-evidence.schema.json", "positive-staging-evidence.json"),
        ):
            schema = json.loads((ROOT / "standards" / "outputs" / schema_name).read_text(encoding="utf-8"))
            fixture = load_fixture(fixture_name)
            page = fixture["page_spec"] if "page_spec" in fixture else fixture
            errors = list(Draft202012Validator(schema).iter_errors(page))
            self.assertEqual([], errors, [error.message for error in errors])

    def test_preflight_accepts_safe_service_area_candidate(self) -> None:
        result = validate_step4b_candidate(load_fixture("positive-bundle.json"))
        self.assertTrue(result["valid"], result["errors"])

    def test_preflight_rejects_service_area_address_claim(self) -> None:
        result = validate_step4b_preflight(load_fixture("unsafe-service-area-bundle.json"))
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_STEP4B_SERVICE_AREA_UNSAFE", {error["code"] for error in result["errors"]})


if __name__ == "__main__":
    unittest.main()
