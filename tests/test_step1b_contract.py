from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from services.step1b_preflight import render_architecture_html, render_architecture_markdown
from services.step1b_preflight.validator import validate_step1b_candidate


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "step1b" / "positive-architecture.json"


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
            {"content_id": "pillar-support", "decision": "new", "url": "/support/", "canonical_url": "https://example.test/support/", "navigation": "primary"}
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


if __name__ == "__main__":
    unittest.main()
