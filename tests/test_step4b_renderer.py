from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from services.step4b_preflight.html_sections import render_sections, render_tracking_slots
from services.step4b_preflight.render import render_step4b
from services.step4b_preflight.validator import (
    page_content_sha256,
    staging_evidence_sha256,
    validate_step4b_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "step4b"


def load_bundle(name: str) -> dict:
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


class Step4bRendererTests(unittest.TestCase):
    def test_renderer_helpers_use_link_labels_and_inert_consent_tracking_attributes(self) -> None:
        # Given: typed related links and a consent-bound tracking placeholder.
        bundle = load_bundle("pq0-4b-001-positive.json")
        page = bundle["page_spec"]
        link = page["sibling_links"][0]
        link["label"] = "Beratung fuer B2B-Teams"
        page["tracking_slots"] = [{"slot_id": "analytics-local", "consent_category": "analytics"}]

        # When: the renderer helpers project the typed structures.
        sections = render_sections(page, bundle["project"])
        tracking = render_tracking_slots(page)

        # Then: visible links use labels and tracking remains non-executable markup.
        self.assertIn(link["label"], sections)
        self.assertNotIn(link["link_id"], sections)
        self.assertIn('data-tracking-slot="analytics-local"', tracking)
        self.assertIn('data-consent-category="analytics"', tracking)
        self.assertNotIn("<script", tracking)
        self.assertNotIn("http", tracking)

    def test_renderer_projects_professional_german_representative_page(self) -> None:
        # Given: the complete de-DE representative Page Spec and Project V2 binding.
        bundle = load_bundle("pq0-4b-006-positive.json")
        page = bundle["page_spec"]
        self.assertTrue(validate_step4b_candidate(bundle)["valid"])

        # When: the validated representative artifact is rendered.
        rendered = render_step4b(bundle)

        # Then: professional German content, truthful types, labels, and inert slots are visible.
        self.assertIn("B2B-Beratung fuer klare Projektentscheidungen", rendered)
        self.assertIn("Haeufige Fragen", rendered)
        self.assertIn("Unverbindliches Erstgespraech anfragen", rendered)
        self.assertIn("Deutschland", rendered)
        self.assertIn("Lokale Pruefgrundlage fuer die Freigabe dokumentiert", rendered)
        self.assertIn("Leistungen fuer B2B-Teams", rendered)
        self.assertNotIn(page["sibling_links"][0]["link_id"], rendered)
        related_links = next(section for section in page["sections"] if section["role"] == "related_links")
        self.assertIn(f'<nav aria-label="{related_links["heading"]}">', rendered)
        self.assertNotIn('aria-label="Related pages"', rendered)
        self.assertIn("Ihre Nachricht", rendered)
        self.assertIn("Datenverarbeitung gemaess der Richtlinie", rendered)
        self.assertIn('"@type":"DefinedTerm"', rendered)
        self.assertIn('"@type":"Dataset"', rendered)
        self.assertIn('"@type":"ItemList"', rendered)
        self.assertIn('data-tracking-slot="analytics-local"', rendered)
        self.assertIn('data-consent-category="analytics"', rendered)
        self.assertEqual(1, rendered.count('<script type="application/ld+json">'))

    def test_renderer_projects_a_valid_raw_typed_page_spec_deterministically(self) -> None:
        # Given: a self-contained valid Page Spec matrix with all nine typed roles.
        bundle = load_bundle("pq0-4b-001-positive.json")
        baseline = validate_step4b_candidate(bundle)
        self.assertTrue(baseline["valid"], baseline["errors"])
        page = bundle["page_spec"]

        # When: the validated typed document is rendered twice.
        first = render_step4b(bundle)
        second = render_step4b(bundle)

        # Then: the standalone document projects every authoritative structure once.
        self.assertEqual(first, second)
        self.assertEqual(1, first.count("<!doctype html>"))
        self.assertEqual(1, first.count("<html "))
        self.assertEqual(1, first.count("<head>"))
        self.assertEqual(1, first.count("<body>"))
        self.assertEqual(1, first.count("<main "))
        self.assertIn('lang="%s"' % page["language"], first)
        self.assertIn(f"<title>{page['meta']['title']}</title>", first)
        self.assertIn(f'content="{page["meta"]["description"]}"', first)
        self.assertIn(f'href="{page["canonical_url"]}"', first)
        self.assertEqual(1, first.count('<script type="application/ld+json">'))
        self.assertIn("Heartweb Production Design System Tokens", first)
        self.assertNotIn("cdn", first.lower())

        for section in page["sections"]:
            marker = (
                f'<section id="{section["section_id"]}" '
                f'data-section-role="{section["role"]}" '
                f'data-schema-node-id="{section["schema_node_id"]}"'
            )
            self.assertIn(marker, first)
            if "microdata" in section:
                microdata = section["microdata"]
                self.assertIn(f'itemtype="{microdata["itemtype"]}"', first)
                for key, value in microdata.items():
                    if key.endswith("itemprop"):
                        self.assertIn(f'itemprop="{value}"', first)

        for form in page["forms"]:
            self.assertIn(f'<form id="{form["form_id"]}"', first)
            self.assertIn(f'<label for="{form["form_id"]}-message">', first)
        self.assertIn(f'data-consent-policy="{page["consent"]["policy_id"]}"', first)
        for slot in page["tracking_slots"]:
            self.assertIn(f'data-tracking-slot="{slot["slot_id"]}"', first)
        for area_id in page["service_area"]["service_area_ids"]:
            self.assertIn(f'data-service-area-id="{area_id}"', first)
        faq = next(section for section in page["sections"] if section["role"] == "faq")
        self.assertIn(faq["content"]["items"][0]["question"], first)
        self.assertIn(faq["content"]["items"][0]["answer"], first)
        for cta in page["ctas"]:
            self.assertIn(cta["label"], first)
        for link in page["sibling_links"]:
            self.assertIn(f'href="{link["url"]}"', first)

    def test_renderer_escapes_hostile_typed_text_and_jsonld(self) -> None:
        # Given: a valid typed Page Spec whose reachable text and graph name contain markup.
        bundle = copy.deepcopy(load_bundle("pq0-4b-001-positive.json"))
        page = bundle["page_spec"]
        direct_answer = next(section for section in page["sections"] if section["role"] == "direct_answer")
        direct_answer["content"]["paragraphs"][0] = '<img src=x onerror="window.audit_marker=1">'
        page["jsonld"]["graph"]["@graph"][0]["name"] = "<script>window.audit_marker=1"
        bind_hashes(bundle)
        self.assertTrue(validate_step4b_candidate(bundle)["valid"])

        # When: the hostile typed values are projected into the standalone document.
        rendered = render_step4b(bundle)

        # Then: neither value becomes executable markup or ends the JSON-LD block.
        self.assertIn("&lt;img src=x onerror=&quot;window.audit_marker=1&quot;&gt;", rendered)
        self.assertNotIn('<img src=x onerror="window.audit_marker=1">', rendered)
        self.assertIn("\\u003cscript\\u003ewindow.audit_marker=1", rendered)
        self.assertEqual(1, rendered.count('<script type="application/ld+json">'))

    def test_renderer_uses_only_verified_project_location_material(self) -> None:
        # Given: a valid physical-location Page Spec bound to Project V2.
        bundle = load_bundle("pq0-4b-002-positive.json")
        baseline = validate_step4b_candidate(bundle)
        self.assertTrue(baseline["valid"], baseline["errors"])
        page = bundle["page_spec"]
        locations = {
            item["location_id"]: item
            for item in bundle["project"]["entity_domain_gbp"]["physical_locations"]
        }

        # When: the verified physical-location page is rendered.
        rendered = render_step4b(bundle)

        # Then: each rendered location is restricted to trusted project material.
        for location_id in page["service_area"]["physical_location_ids"]:
            location = locations[location_id]
            self.assertIn(", ".join((location["name"], location["locality"], location["country_code"])), rendered)
        self.assertNotIn("<address", rendered)


if __name__ == "__main__":
    unittest.main()
