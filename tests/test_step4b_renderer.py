from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path

from services.step4b_preflight.render import render_step4b


ROOT = Path(__file__).resolve().parents[1]


class Step4bRendererTests(unittest.TestCase):
    def test_html_is_deterministic_standalone_and_service_area_safe(self) -> None:
        bundle = json.loads((ROOT / "tests" / "fixtures" / "step4b" / "positive-bundle.json").read_text(encoding="utf-8"))
        bundle["page_spec"].update({"language": "de", "locale": "de-DE", "project_id": "project-national-b2b", "deployment_id": "dep-national-b2b-de"})
        bundle["page_spec"]["service_area"]["areas"] = ["Germany"]
        bundle["project"] = json.loads((ROOT / "tests" / "fixtures" / "domain" / "real-customer-matrix" / "national-b2b.json").read_text(encoding="utf-8"))
        graph = {"@context": "https://schema.org", "@graph": [{"@id": "https://example.invalid/page#product", "@type": "Product", "name": "Verified page"}]}
        bundle["page_spec"]["jsonld"] = {"level": "basic", "graph": graph, "graph_hash": hashlib.sha256(json.dumps(graph, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()}
        payload = dict(bundle["page_spec"])
        payload.pop("content_sha256", None)
        content_hash = hashlib.sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
        bundle["page_spec"]["content_sha256"] = content_hash
        bundle["staging_evidence"]["content_sha256"] = content_hash
        first = render_step4b(bundle)
        self.assertEqual(first, render_step4b(bundle))
        self.assertIn(bundle["page_spec"]["meta"]["title"], first)
        self.assertIn(bundle["page_spec"]["canonical_url"], first)
        self.assertIn(bundle["page_spec"]["service_area"]["areas"][0], first)
        self.assertNotIn("cdn", first.lower())
        self.assertNotIn("address", first.lower())
