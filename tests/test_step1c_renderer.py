from __future__ import annotations

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from services.step1c_preflight.render import render_step1c, write_step1c


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "step1c"


class Step1cRendererTests(unittest.TestCase):
    def test_renderer_is_deterministic_and_uses_customer_tokens_without_cdn(self) -> None:
        design = json.loads((FIXTURES / "non-ahd-outdoor-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "non-ahd-outdoor-template.json").read_text(encoding="utf-8"))
        first = render_step1c({"design": design, "templates": [template]})
        second = render_step1c({"design": design, "templates": [template]})
        self.assertEqual(first, second)
        self.assertIn(design["tokens"]["color_primary"], first["css"])
        self.assertIn(template["content_id"], first["html"])
        self.assertNotIn("cdn", first["html"].lower())

    def test_invalid_input_does_not_write_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "derived.json"
            with self.assertRaises(ValueError):
                write_step1c({"design": {}, "templates": []}, output)
            self.assertFalse(output.exists())

    def test_writer_derives_template_output_from_template_id(self) -> None:
        # Given: a valid template whose content identity differs from its template identity
        design = json.loads((FIXTURES / "non-ahd-outdoor-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "non-ahd-outdoor-template.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            # When: the canonical Step 1C views are written
            _, templates = write_step1c({"design": design, "templates": [template]}, Path(directory))
            # Then: the derived filename is keyed by canonical template_id
            self.assertEqual(
                Path(directory) / "v2/outputs/step1c/templates/template-outdoor-kayaks-0001.v1.html",
                templates[0],
            )


class Step1CDeltaRendererTests(unittest.TestCase):
    def test_renderer_uses_relative_routes_for_canonical_content_links(self) -> None:
        # Given: the canonical template with declared root link targets.
        design = json.loads((FIXTURES / "pq0-1c-canonical-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))

        # When: the public renderer emits the complete pillar page.
        html = render_step1c({"design": design, "templates": [template]})["html"]

        # Then: canonical content links cannot remain dangling target fragments.
        self.assertNotIn('href="#cluster-', html)
        self.assertNotIn('href="#pillar-', html)
        declared_routes = {link["href"] for link in template["links"]}
        rendered_hrefs = set(re.findall(r'href="([^"]+)"', html))
        self.assertTrue(declared_routes <= rendered_hrefs)
        self.assertTrue(all(href == "#main" or href in declared_routes for href in rendered_hrefs))

    def test_renderer_keeps_faq_answers_initially_visible(self) -> None:
        # Given: the canonical template with a visible FAQ answer.
        design = json.loads((FIXTURES / "pq0-1c-canonical-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))

        # When: the public renderer emits the FAQ disclosure.
        html = render_step1c({"design": design, "templates": [template]})["html"]

        # Then: the semantic disclosure starts open so its answer is visible.
        self.assertIn("<details open ", html)

    def test_pq0_1c_001_002_005_006_008_009_010_012_renders_fixture_content_semantically(self) -> None:
        # Given: a complete typed content object with all visible copy in fixture data.
        design = json.loads((FIXTURES / "pq0-1c-canonical-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))

        # When: the public renderer receives the validated canonical artifacts.
        first = render_step1c({"design": design, "templates": [template]})
        second = render_step1c({"design": design, "templates": [template]})

        # Then: every required block has deterministic semantic HTML and fixture-owned copy.
        html = first["html"]
        content = template["content"]
        self.assertEqual(first, second)
        self.assertIn('<header class="pillar-hero">', html)
        self.assertIn('<section aria-labelledby="quick-facts-heading">', html)
        self.assertIn('<dl class="facts-grid">', html)
        self.assertIn('<article aria-labelledby="editorial-heading" data-evidence-ids=', html)
        self.assertIn('<section aria-labelledby="heartpiece-heading" data-evidence-ids=', html)
        self.assertIn('<section aria-labelledby="process-heading">', html)
        self.assertIn("<ol>", html)
        self.assertIn('<section aria-labelledby="social-proof-heading">', html)
        self.assertIn("<blockquote data-evidence-ids=", html)
        self.assertIn('<section aria-labelledby="faq-heading">', html)
        self.assertIn("<details open data-evidence-ids=", html)
        self.assertIn('<footer class="pillar-final-cta">', html)

        visible_copy = [
            content["hero"]["heading"],
            content["hero"]["summary"],
            content["hero"]["primary_cta"]["label"],
            content["quick_facts"]["heading"],
            content["editorial"]["heading"],
            content["heartpiece"]["heading"],
            content["heartpiece"]["body"],
            content["grouped_cluster_links"]["heading"],
            content["process"]["heading"],
            content["social_proof"]["heading"],
            content["faq"]["heading"],
            content["cross_pillar_links"]["heading"],
            content["final_cta"]["heading"],
            content["final_cta"]["summary"],
            content["final_cta"]["primary_cta"]["label"],
        ]
        visible_copy.extend(fact["label"] for fact in content["quick_facts"]["facts"])
        visible_copy.extend(fact["value"] for fact in content["quick_facts"]["facts"])
        visible_copy.extend(content["editorial"]["paragraphs"])
        visible_copy.extend(group["label"] for group in content["grouped_cluster_links"]["groups"])
        visible_copy.extend(link["label"] for group in content["grouped_cluster_links"]["groups"] for link in group["links"])
        visible_copy.extend(step["title"] for step in content["process"]["steps"])
        visible_copy.extend(step["description"] for step in content["process"]["steps"])
        visible_copy.extend(entry["quote"] for entry in content["social_proof"]["entries"])
        visible_copy.extend(entry["attribution"] for entry in content["social_proof"]["entries"])
        visible_copy.extend(item["question"] for item in content["faq"]["items"])
        visible_copy.extend(item["answer"] for item in content["faq"]["items"])
        visible_copy.extend(link["label"] for link in content["cross_pillar_links"]["links"])
        for value in visible_copy:
            self.assertIn(value, html)

        variant = copy.deepcopy(template)
        variant["content"]["hero"]["heading"] = "Fixture variant hero heading"
        variant["content"]["hero"]["summary"] = "Fixture variant hero summary"
        variant["content"]["hero"]["primary_cta"]["label"] = "Fixture variant primary action"
        variant_html = render_step1c({"design": design, "templates": [variant]})["html"]
        self.assertIn(variant["content"]["hero"]["heading"], variant_html)
        self.assertIn(variant["content"]["hero"]["summary"], variant_html)
        self.assertIn(variant["content"]["hero"]["primary_cta"]["label"], variant_html)
        self.assertNotIn(content["hero"]["heading"], variant_html)

    def test_pq0_1c_003_007_011_uses_brand_tokens_and_canonical_links_without_external_runtime(self) -> None:
        # Given: bounded brand evidence and content references bound to declared relationships.
        design = json.loads((FIXTURES / "pq0-1c-canonical-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))

        # When: the public renderer receives the validated canonical artifacts.
        rendered = render_step1c({"design": design, "templates": [template]})

        # Then: the page is self-contained and preserves safety, provenance, and link boundaries.
        html = rendered["html"]
        content = template["content"]
        for token in design["tokens"].values():
            self.assertIn(token, rendered["css"])
        self.assertIn(design["brand_consistency"]["approved_brand_name"], html)
        self.assertIn(design["brand_consistency"]["approved_direction"], html)
        for evidence_id in design["brand_consistency"]["evidence_ids"]:
            self.assertIn(evidence_id, html)
        self.assertIn('<nav aria-label="Related cluster guides">', html)
        self.assertIn('<nav aria-label="Related pillar pages">', html)
        declared_links = {(link["target_content_id"], link["relationship"]) for link in template["links"]}
        declared_routes = {(link["target_content_id"], link["relationship"]): link["href"] for link in template["links"]}
        content_links = [
            link
            for group in content["grouped_cluster_links"]["groups"]
            for link in group["links"]
        ] + content["cross_pillar_links"]["links"]
        for link in content_links:
            self.assertIn((link["target_content_id"], link["relationship"]), declared_links)
            self.assertIn(f'href="{declared_routes[(link["target_content_id"], link["relationship"])]}"', html)
        self.assertIn('<a class="skip-link" href="#main">', html)
        for reference in template["jsonld_references"]:
            self.assertIn(reference["reference_id"], html)
        self.assertNotIn("physical_address", html)
        self.assertNotIn("<link ", html.lower())
        self.assertNotIn("<script src=", html.lower())
        self.assertNotIn("@import", rendered["css"].lower())
        self.assertNotIn("url(", rendered["css"].lower())

    def test_renderer_escapes_canonical_content_values(self) -> None:
        # Given: canonical display fields containing markup-significant characters.
        design = json.loads((FIXTURES / "pq0-1c-canonical-design-system.json").read_text(encoding="utf-8"))
        template = json.loads((FIXTURES / "pq0-1c-canonical-template.json").read_text(encoding="utf-8"))
        template["content"]["hero"]["heading"] = "<strong>Escaped hero</strong>"
        template["content"]["faq"]["items"][0]["answer"] = "Use < and > only as text."

        # When: the public renderer emits standalone HTML.
        html = render_step1c({"design": design, "templates": [template]})["html"]

        # Then: content remains text rather than executable or structural markup.
        self.assertIn("&lt;strong&gt;Escaped hero&lt;/strong&gt;", html)
        self.assertIn("Use &lt; and &gt; only as text.", html)
        self.assertNotIn("<strong>Escaped hero</strong>", html)
