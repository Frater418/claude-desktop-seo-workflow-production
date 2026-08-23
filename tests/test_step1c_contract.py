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


class Step1CDeltaContractTests(unittest.TestCase):
    def test_pq0_1c_canonical_design_and_template_are_accepted(self) -> None:
        # Given: the complete M08 Step 1C template and approved local brand evidence.
        design = json.loads((FIXTURES / "pq0-1c-canonical-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))

        # When: the public Step 1C validator evaluates the canonical artifacts.
        result = validate_step1c_candidate(design, [template])

        # Then: all PQ0 structure is accepted as one self-contained pillar contract.
        self.assertTrue(result["valid"], result["errors"])

    def test_pq0_1c_required_content_blocks_are_rejected_when_missing(self) -> None:
        # Given: one negative mutation for every mandatory M08 content block.
        design = json.loads((FIXTURES / "pq0-1c-canonical-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))
        cases = json.loads((FIXTURES / "pq0-1c-missing-content-blocks.json").read_text(encoding="utf-8"))["missing_content_blocks"]

        for case in cases:
            with self.subTest(requirement_id=case["requirement_id"], block=case["block"]):
                # When: the named canonical content block is absent.
                candidate = copy.deepcopy(template)
                candidate["content"].pop(case["block"])
                result = validate_step1c_candidate(design, [candidate])

                # Then: the validator identifies the missing typed content block itself.
                self.assertTrue(
                    any(
                        error["code"] == "ERROR_STEP1C_TEMPLATE_INVALID"
                        and error["path"] == ["templates", 0, "content"]
                        and f"'{case['block']}' is a required property" in error["message"]
                        for error in result["errors"]
                    ),
                    result["errors"],
                )

    def test_pq0_1c_003_rejects_brand_evidence_outside_declared_design_evidence(self) -> None:
        # Given: an approved brand object that names evidence absent from the design artifact.
        design = json.loads((FIXTURES / "pq0-1c-brand-evidence-outside-design.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))

        # When: the public Step 1C validator evaluates the evidence boundary.
        result = validate_step1c_candidate(design, [template])

        # Then: brand direction cannot introduce evidence beyond the declared local design set.
        self.assertIn("ERROR_STEP1C_DESIGN_BRAND_EVIDENCE_INVALID", {error["code"] for error in result["errors"]})

    def test_pq0_1c_007_and_011_reject_detached_canonical_link_references(self) -> None:
        # Given: grouped-cluster and cross-pillar references that are absent from template links.
        design = json.loads((FIXTURES / "pq0-1c-canonical-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))
        link_cases = (
            ("PQ0-1C-007", ("grouped_cluster_links", "groups", 0, "links", 0), "cluster-detached-link-0001"),
            ("PQ0-1C-011", ("cross_pillar_links", "links", 0), "pillar-detached-link-0001"),
        )

        for requirement_id, path, detached_target in link_cases:
            with self.subTest(requirement_id=requirement_id):
                # When: the content block replaces a declared target with a detached canonical ID.
                candidate = copy.deepcopy(template)
                content_link = candidate["content"]
                for segment in path:
                    content_link = content_link[segment]
                content_link["target_content_id"] = detached_target
                result = validate_step1c_candidate(design, [candidate])

                # Then: the content reference must bind to a declared target and relationship.
                self.assertIn("ERROR_STEP1C_TEMPLATE_LINK_REFERENCE_INVALID", {error["code"] for error in result["errors"]})

    def test_pq0_1c_evidence_bound_content_rejects_unknown_template_evidence(self) -> None:
        # Given: evidence-bearing content blocks that each replace local evidence with an unknown ID.
        design = json.loads((FIXTURES / "pq0-1c-canonical-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))
        evidence_cases = (
            ("PQ0-1C-002", ("quick_facts", "facts", 0)),
            ("PQ0-1C-006", ("heartpiece",)),
            ("PQ0-1C-009", ("social_proof", "entries", 0)),
            ("PQ0-1C-010", ("faq", "items", 0)),
        )

        for requirement_id, path in evidence_cases:
            with self.subTest(requirement_id=requirement_id):
                # When: a content block claims evidence not declared by the template.
                candidate = copy.deepcopy(template)
                content_block = candidate["content"]
                for segment in path:
                    content_block = content_block[segment]
                content_block["evidence_ids"] = ["evidence-unknown-content-0001"]
                result = validate_step1c_candidate(design, [candidate])

                # Then: content evidence stays within the canonical template evidence set.
                self.assertIn("ERROR_STEP1C_TEMPLATE_CONTENT_EVIDENCE_INVALID", {error["code"] for error in result["errors"]})

    def test_pq0_1c_010_rejects_faq_without_declared_jsonld_reference(self) -> None:
        # Given: a visible FAQ that names a JSON-LD reference absent from the template.
        design = json.loads((FIXTURES / "pq0-1c-canonical-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))
        template["content"]["faq"]["items"][0]["jsonld_reference_id"] = "jsonld-unknown-faq-0001"

        # When: the public Step 1C validator evaluates the FAQ binding.
        result = validate_step1c_candidate(design, [template])

        # Then: visible FAQ content must bind to the declared FAQPage JSON-LD reference.
        self.assertIn("ERROR_STEP1C_TEMPLATE_JSONLD_BINDING_INVALID", {error["code"] for error in result["errors"]})

    def test_pq0_1c_001_and_012_reject_detached_cta_targets(self) -> None:
        # Given: hero and final CTAs that no longer reference declared vertical links.
        design = json.loads((FIXTURES / "pq0-1c-canonical-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))
        cta_cases = (
            ("PQ0-1C-001", "hero"),
            ("PQ0-1C-012", "final_cta"),
        )

        for requirement_id, block in cta_cases:
            with self.subTest(requirement_id=requirement_id):
                # When: a CTA replaces its canonical target with an arbitrary content ID.
                candidate = copy.deepcopy(template)
                candidate_cta = candidate["content"][block]["primary_cta"]
                candidate_cta["target_content_id"] = "cluster-detached-cta-0001"
                result = validate_step1c_candidate(design, [candidate])

                # Then: every CTA remains bound to a declared vertical relationship.
                self.assertIn("ERROR_STEP1C_TEMPLATE_LINK_REFERENCE_INVALID", {error["code"] for error in result["errors"]})

    def test_preflight_rejects_duplicate_or_conflicting_root_link_routes(self) -> None:
        # Given: a duplicate root target relationship with a different canonical route.
        design = json.loads((FIXTURES / "pq0-1c-canonical-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))
        duplicate = copy.deepcopy(template["links"][0])
        duplicate["href"] = "/guides/kayak-selection-alternate"
        template["links"].append(duplicate)

        # When: the public validator evaluates the root link registry.
        result = validate_step1c_candidate(design, [template])

        # Then: routes cannot conflict for a canonical target relationship.
        self.assertIn("ERROR_STEP1C_TEMPLATE_LINK_REGISTRY_INVALID", {error["code"] for error in result["errors"]})

    def test_preflight_rejects_unsafe_root_link_routes(self) -> None:
        # Given: root links containing network-path, separator, whitespace, and empty forms.
        design = json.loads((FIXTURES / "pq0-1c-canonical-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))

        for href in ("//externalhost/path", "/care//guide/", "/care\n", "/care\t", "/care guide", ""):
            with self.subTest(href=href):
                # When: the public validator receives an unsafe canonical route.
                candidate = copy.deepcopy(template)
                candidate["links"][0]["href"] = href
                result = validate_step1c_candidate(design, [candidate])

                # Then: the schema boundary rejects the route before rendering.
                self.assertIn("ERROR_STEP1C_TEMPLATE_INVALID", {error["code"] for error in result["errors"]})


if __name__ == "__main__":
    unittest.main()
