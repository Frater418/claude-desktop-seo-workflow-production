"""Tests for the deterministic Step 1 Markdown renderer.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from services.step1_preflight.render import render_topic_inventory


class Step1RendererTests(unittest.TestCase):
    def test_renderer_is_deterministic_and_complete(self):
        root = Path(__file__).resolve().parents[1]
        inventory = json.loads((root / "tests" / "fixtures" / "step1" / "positive-inventory.json").read_text(encoding="utf-8"))
        first = render_topic_inventory(inventory)
        second = render_topic_inventory(inventory)
        self.assertEqual(first, second)
        expected_clusters = sum(len(pillar["cluster_candidates"]) for pillar in inventory["pillars"])
        rendered_cluster_ids = sum(first.count(cluster["cluster_id"]) for pillar in inventory["pillars"] for cluster in pillar["cluster_candidates"])
        self.assertEqual(expected_clusters, rendered_cluster_ids)
        self.assertIn("awaiting external GATE-1 review", first)
        self.assertNotIn(chr(0x2014), first)
        self.assertNotIn(chr(0x2013), first)


if __name__ == "__main__":
    unittest.main()
