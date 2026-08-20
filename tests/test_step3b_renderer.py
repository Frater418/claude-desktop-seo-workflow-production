from __future__ import annotations

import json
import unittest
from pathlib import Path

from services.step3b_preflight.render import render_step3b


ROOT = Path(__file__).resolve().parents[1]


class Step3bRendererTests(unittest.TestCase):
    def test_adjustment_references_distinct_source_and_proposed_plans(self) -> None:
        bundle = json.loads((ROOT / "tests" / "fixtures" / "step3b" / "positive-bundle.json").read_text(encoding="utf-8"))
        first = render_step3b(bundle)
        self.assertEqual(first, render_step3b(bundle))
        self.assertIn(bundle["adjustment"]["source_plan"]["artifact_id"], first)
        self.assertIn(bundle["adjustment"]["proposed_plan"]["artifact_id"], first)
