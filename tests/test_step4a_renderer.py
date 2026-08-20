from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path

from services.step4a_preflight.render import render_step4a


ROOT = Path(__file__).resolve().parents[1]


class Step4aRendererTests(unittest.TestCase):
    def test_briefing_is_deterministic_and_claims_and_evidence_are_canonical(self) -> None:
        bundle = json.loads((ROOT / "tests" / "fixtures" / "step4a" / "positive-bundle.json").read_text(encoding="utf-8"))
        graph = {"@context": "https://schema.org", "@graph": [{"@id": "https://example.invalid/briefing#product", "@type": "Product", "name": "Verified briefing"}]}
        canonical = json.dumps(graph, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        bundle["briefing"]["jsonld"] = {"level": "basic", "graph": graph, "graph_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}
        bundle["briefing"]["claim_bindings"] = [{"claim_id": claim["claim_id"], "graph_node_id": "https://example.invalid/briefing#product"} for claim in bundle["claim_ledger"]["claims"]]
        first = render_step4a(bundle)
        self.assertEqual(first, render_step4a(bundle))
        claim = bundle["claim_ledger"]["claims"][0]
        self.assertIn("---\n", first)
        self.assertIn(claim["text"], first)
        self.assertIn(claim["evidence_ids"][0], first)
        self.assertIn('"@context": "https://schema.org"', first)
