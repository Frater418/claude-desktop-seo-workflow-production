from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from services.step1b_preflight import render_architecture_html, render_architecture_markdown
from services.step1b_preflight.validator import validate_step1b_candidate


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "step1b" / "positive-architecture.json"
FIXTURES = FIXTURE.parent


class Step1BContractTests(unittest.TestCase):
    def test_preflight_accepts_complete_candidate(self) -> None:
        # Given: a canonical architecture with one approved pillar and cluster.
        architecture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        approved_content_ids = [item["content_id"] for item in architecture["content_decisions"]]

        # When: Step 1B validates the architecture.
        result = validate_step1b_candidate(architecture, approved_content_ids)

        # Then: its closed candidate contract and link graph are accepted.
        self.assertTrue(result["valid"], result["errors"])

    def test_preflight_rejects_missing_content_decision(self) -> None:
        # Given: an approved cluster without an architecture decision.
        architecture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        approved_content_ids = [item["content_id"] for item in architecture["content_decisions"]]
        architecture["content_decisions"] = architecture["content_decisions"][:1]

        # When: Step 1B validates the architecture.
        result = validate_step1b_candidate(architecture, approved_content_ids)

        # Then: it rejects incomplete decision coverage.
        self.assertIn("ERROR_STEP1B_DECISION_COVERAGE_INVALID", {item["code"] for item in result["errors"]})

    def test_preflight_rejects_conflicting_or_orphan_links(self) -> None:
        # Given: duplicate URL claims and a link to content outside the approved set.
        architecture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        approved_content_ids = [item["content_id"] for item in architecture["content_decisions"]]
        conflicting = copy.deepcopy(architecture["content_decisions"][0])
        conflicting["content_id"] = architecture["content_decisions"][1]["content_id"]
        architecture["content_decisions"][1] = conflicting
        architecture["link_graph"][0]["to_content_id"] = f"{approved_content_ids[-1]}-missing"

        # When: Step 1B validates the architecture.
        result = validate_step1b_candidate(architecture, approved_content_ids)

        # Then: conflicting and orphan topology is rejected.
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("ERROR_STEP1B_URL_CONFLICT", codes)
        self.assertIn("ERROR_STEP1B_LINK_GRAPH_INVALID", codes)

    def test_preflight_rejects_unconnected_multiple_pillars(self) -> None:
        architecture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        architecture["content_decisions"].append(
            {"content_id": "pillar-support", "decision": "new", "url": "/support/", "canonical_url": "https://example.test/support/", "navigation": "primary", "page_type": "pillar_page", "display_label": "Support", "presentation_status": "confirmed"}
        )

        result = validate_step1b_candidate(architecture, ["pillar-care", "pillar-support", "cluster-care-guide"])

        self.assertIn("ERROR_STEP1B_LINK_GRAPH_INVALID", {item["code"] for item in result["errors"]})

    def test_preflight_accepts_contrasting_non_ahd_architecture(self) -> None:
        # Given: a non-AHD product-site architecture with two horizontal pillars.
        architecture = json.loads((FIXTURE.parent / "non-ahd-outdoor-architecture.json").read_text(encoding="utf-8"))
        approved_content_ids = [item["content_id"] for item in architecture["content_decisions"]]

        # When: Step 1B validates the canonical candidate.
        result = validate_step1b_candidate(architecture, approved_content_ids)

        # Then: the generic contract accepts its unrelated market and navigation model.
        self.assertTrue(result["valid"], result["errors"])

    def test_renderers_are_deterministic_views_of_canonical_json(self) -> None:
        # Given: one canonical architecture tree.
        architecture = json.loads(FIXTURE.read_text(encoding="utf-8"))

        # When: both derived views render twice.
        markdown = render_architecture_markdown(architecture)
        html = render_architecture_html(architecture)

        # Then: they are deterministic and represent the same decision data.
        self.assertEqual(markdown, render_architecture_markdown(architecture))
        self.assertEqual(html, render_architecture_html(architecture))
        self.assertIn(architecture["content_decisions"][0]["content_id"], markdown)
        self.assertIn(architecture["content_decisions"][1]["content_id"], html)

    def test_pq0_1b_001(self) -> None:
        # Given: a professional hierarchy with typed page classes and explicit parentage.
        architecture = json.loads((FIXTURES / "pq0-1b-001-positive.json").read_text(encoding="utf-8"))
        invalid_architecture = json.loads((FIXTURES / "pq0-1b-001-negative.json").read_text(encoding="utf-8"))
        approved_content_ids = [item["content_id"] for item in architecture["content_decisions"]]

        # When: the public validator and derived views process the canonical architecture.
        result = validate_step1b_candidate(architecture, approved_content_ids)

        # Then: it accepts a readable tree without inferring page type or parentage from IDs.
        self.assertTrue(result["valid"], result["errors"])
        markdown = render_architecture_markdown(architecture)
        html = render_architecture_html(architecture)
        self.assertEqual(markdown, render_architecture_markdown(architecture))
        self.assertEqual(html, render_architecture_html(architecture))
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertIn("## Architecture Tree", markdown)
        self.assertIn("Care Services", markdown)
        self.assertIn("Pillar Page", markdown)
        self.assertIn("https://example.test/care/legacy/", markdown)
        self.assertIn("https://example.test/care/guide/", markdown)
        self.assertIn("primary", markdown)
        self.assertIn("redirect", markdown)
        self.assertIn("architecture-tree", html)
        self.assertIn("page-type-legend", html)
        self.assertIn('data-page-type="pillar_page"', html)
        self.assertIn('data-canonical-url="https://example.test/care/legacy/"', html)
        self.assertIn('data-navigation="primary"', html)
        self.assertIn('data-redirect-to-url="https://example.test/care/guide/"', html)
        self.assertIn("https://example.test/care/guide/", html)
        invalid_result = validate_step1b_candidate(invalid_architecture, approved_content_ids)
        self.assertFalse(invalid_result["valid"])
        self.assertTrue(any(error["path"] == ["content_decisions", 0] for error in invalid_result["errors"]), invalid_result["errors"])
        with self.assertRaises(ValueError):
            render_architecture_markdown(invalid_architecture)
        with self.assertRaises(ValueError):
            render_architecture_html(invalid_architecture)

    def test_preflight_rejects_invalid_typed_presentation_references(self) -> None:
        architecture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        architecture["content_decisions"][1]["parent_content_id"] = "cluster-care-guide"
        architecture["open_confirmations"] = [{"confirmation_id": "confirmation-care-guide", "question": "Confirm the care guide.", "status": "open", "content_ids": ["pillar-care"]}]

        result = validate_step1b_candidate(architecture, [item["content_id"] for item in architecture["content_decisions"]])

        codes = {item["code"] for item in result["errors"]}
        self.assertIn("ERROR_STEP1B_HIERARCHY_INVALID", codes)
        self.assertIn("ERROR_STEP1B_OPEN_CONFIRMATION_INVALID", codes)

    def test_pq0_1b_002(self) -> None:
        # Given: an architecture with an explicit release confirmation still open.
        architecture = json.loads((FIXTURES / "pq0-1b-002-positive.json").read_text(encoding="utf-8"))
        invalid_architecture = json.loads((FIXTURES / "pq0-1b-002-negative.json").read_text(encoding="utf-8"))
        approved_content_ids = [item["content_id"] for item in architecture["content_decisions"]]

        # When: the public validator and derived views process the confirmation state.
        result = validate_step1b_candidate(architecture, approved_content_ids)

        # Then: they preserve the open confirmation and reject an open status without its requirement.
        self.assertTrue(result["valid"], result["errors"])
        markdown = render_architecture_markdown(architecture)
        html = render_architecture_html(architecture)
        self.assertEqual(markdown, render_architecture_markdown(architecture))
        self.assertEqual(html, render_architecture_html(architecture))
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertIn("## Open Confirmations", markdown)
        self.assertIn("confirmation-care-redirect", markdown)
        self.assertIn("Confirm the legacy care redirect target before release.", markdown)
        self.assertIn("Pillar Page", markdown)
        self.assertIn("Primary topic hub", markdown)
        self.assertIn("open-confirmations", html)
        self.assertIn('data-presentation-status="open"', html)
        self.assertIn("confirmation-care-redirect", html)
        self.assertIn("Pillar Page", html)
        self.assertIn("Primary topic hub", html)
        invalid_result = validate_step1b_candidate(invalid_architecture, approved_content_ids)
        self.assertFalse(invalid_result["valid"])
        self.assertTrue(any(error["path"] == ["open_confirmations"] for error in invalid_result["errors"]), invalid_result["errors"])
        with self.assertRaises(ValueError):
            render_architecture_markdown(invalid_architecture)
        with self.assertRaises(ValueError):
            render_architecture_html(invalid_architecture)


if __name__ == "__main__":
    unittest.main()
