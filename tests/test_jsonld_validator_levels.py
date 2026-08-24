"""Honest validation-level tests for the JSON-LD validator.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import json
import importlib.util
import unittest
from pathlib import Path


def _load_validator_module():
    path = Path(__file__).resolve().parents[1] / "mcp" / "tools" / "validate_schema_jsonld.py"
    spec = importlib.util.spec_from_file_location("heartweb_validate_schema_jsonld", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validate_text = _load_validator_module().validate_text


class JsonLdValidationLevelTests(unittest.TestCase):
    def test_invalid_date_fails_format_level(self):
        payload = self.valid_article()
        payload["datePublished"] = "bad"
        result = validate_text(json.dumps(payload), strict_geo=True)
        self.assertFalse(result["valid"])
        self.assertEqual("failed", result["levels"]["format"])
        self.assertIn("ERROR_SCHEMA_DATE_INVALID", {issue["code"] for issue in result["issues"]})

    def test_empty_about_item_fails_geo_level(self):
        payload = self.valid_article()
        payload["about"] = [{}]
        result = validate_text(json.dumps(payload), strict_geo=True)
        self.assertFalse(result["valid"])
        self.assertEqual("failed", result["levels"]["geo"])
        self.assertIn("ERROR_SCHEMA_ABOUT_INVALID", {issue["code"] for issue in result["issues"]})

    def test_unknown_type_fails_contract_level(self):
        payload = {"@context": "https://schema.org", "@type": "InventedType", "name": "Example"}
        result = validate_text(json.dumps(payload), strict_geo=False)
        self.assertFalse(result["valid"])
        self.assertEqual("failed", result["levels"]["contract"])
        self.assertIn("ERROR_SCHEMA_TYPE_UNKNOWN", {issue["code"] for issue in result["issues"]})

    def test_valid_article_reports_evidence_not_assessed(self):
        result = validate_text(json.dumps(self.valid_article()), strict_geo=True)
        self.assertTrue(result["valid"])
        self.assertEqual("passed", result["levels"]["parse"])
        self.assertEqual("passed", result["levels"]["contract"])
        self.assertEqual("passed", result["levels"]["format"])
        self.assertEqual("passed", result["levels"]["geo"])
        self.assertEqual("not_assessed", result["levels"]["claim_evidence"])
        self.assertEqual("not_assessed", result["levels"]["google_eligibility"])

    def test_visible_geo_section_types_pass_with_required_properties(self):
        # Given: graph nodes with visible name, description, data, and list content.
        payload = {
            "@context": "https://schema.org",
            "@graph": [
                {"@id": "https://example.test/page#definition", "@type": "DefinedTerm", "name": "B2B-Beratung", "description": "Eine strukturierte Erstklaerung."},
                {"@id": "https://example.test/page#evidence", "@type": "Dataset", "name": "Projektgrundlagen", "description": "Lokal simulierte Pruefhinweise.", "variableMeasured": ["Pruefstatus"]},
                {"@id": "https://example.test/page#comparison", "@type": "ItemList", "name": "Leistungsoptionen", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Erstklaerung"}]},
            ],
        }

        # When: the local JSON-LD validator evaluates the supported GEO nodes.
        result = validate_text(json.dumps(payload), strict_geo=False)

        # Then: their narrow required-field contracts pass.
        self.assertTrue(result["valid"], result["issues"])

    @staticmethod
    def valid_article() -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "@id": "https://example.com/article#schema",
            "headline": "Example article",
            "datePublished": "2026-08-19T03:00:00Z",
            "author": {"@type": "Person", "name": "Raphael Rechberger"},
            "about": [
                {
                    "@type": "Thing",
                    "name": "Search engine optimization",
                    "sameAs": "https://www.wikidata.org/wiki/Q180711",
                }
            ],
        }


if __name__ == "__main__":
    unittest.main()
