from __future__ import annotations

import json
import unittest
from pathlib import Path

from services.step4a_preflight.render import render_step4a


ROOT = Path(__file__).resolve().parents[1]


class Step4aRendererTests(unittest.TestCase):
    def test_renderer_projects_complete_canonical_briefing_from_raw_fixture(self) -> None:
        # Given: the self-contained enhanced GEO candidate used by the PQ-0 matrix.
        bundle = json.loads((ROOT / "tests" / "fixtures" / "step4a" / "pq0-4a-008-positive.json").read_text(encoding="utf-8"))

        # When: the validated briefing is projected into Copywriter Markdown.
        first = render_step4a(bundle)

        # Then: the projection is deterministic and preserves valid Notion scalar frontmatter.
        self.assertEqual(first, render_step4a(bundle))
        lines = first.splitlines()
        closing_delimiter = lines.index("---", 1)
        frontmatter = {key: json.loads(value) for key, value in (line.split(": ", 1) for line in lines[1:closing_delimiter])}
        self.assertEqual(
            {
                "artifact_id": "artifact-briefing-0001",
                "claim_ledger_artifact_id": "artifact-ledger-0001",
                "derived": True,
                "project_id": "project-care-001",
                "projection_schema_version": "2.0.0",
            },
            frontmatter,
        )
        self.assertEqual(
            [
                "# Content Briefing",
                "## Briefing Overview",
                "## Hero Direct Answer",
                "## Editorial Outline",
                "## Semantic Triples",
                "## Simulated local evidence summary",
                "## Copywriter Guidance",
                "## Definitive Language Guidance",
                "## Entity Bindings",
                "## Claim Ledger",
                "## SERP Evidence",
                "## JSON-LD",
            ],
            [line for line in lines if line.startswith(("# ", "## "))],
        )
        briefing = bundle["briefing"]
        sections = briefing["briefing_sections"]
        self.assertIn(briefing["hero_direct_answer"]["text"], first)
        self.assertIn(f"- Audience: {sections['audience']}", first)
        self.assertIn(f"- Primary Keyword: {sections['primary_keyword']}", first)
        self.assertLess(first.index(f"- {sections['outline'][0]}"), first.index(f"- {sections['outline'][1]}"))
        self.assertIn("### `triple-care-0001`", first)
        self.assertIn("- Evidence IDs: `evidence-serp-0001`", first)
        self.assertIn("- Simulated review status: local-only", first)
        self.assertIn("- CTA: Invite a reviewed local consultation.", first)
        self.assertIn("- Preferred: Evidence indicates", first)
        self.assertIn("- Prohibited: Guaranteed outcome", first)
        self.assertIn("### About", first)
        self.assertIn("### Mentions", first)
        self.assertIn("| Simulated Care | https://www.wikidata.org/wiki/Q1 | https://example.invalid/entity#care |", first)
        self.assertIn("The simulated local briefing remains evidence-bound.", first)
        self.assertIn("request-serp-0001", first)
        self.assertIn('"@context": "https://schema.org"', first)
