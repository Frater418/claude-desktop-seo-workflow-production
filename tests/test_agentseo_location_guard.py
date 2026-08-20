#!/usr/bin/env python3
"""Tests fuer den Hermes-AgentSEO-Standortadapter.

Autor: Raphael Rechberger
"""

import copy
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from services.agentseo_gateway.core import (  # noqa: E402
    AgentSEOAdapterError,
    build_keyword_metrics_payload,
    build_serp_analysis_payload,
    load_location_target,
    normalize_agentseo_result,
)


class AgentSEOLocationGuardTests(unittest.TestCase):
    def setUp(self):
        self.target = {
            "country": "DE",
            "location_name": "Germany",
            "location_code": 2276,
            "language": "de",
        }

    def test_keyword_result_preserves_provider_iso_and_corrects_metadata(self):
        raw = {
            "location": {
                "input": "Germany",
                "location_code": 2276,
                "location_name": "Germany",
                "country_iso_code": "US",
            },
            "keyword_metrics": {"items": [{"keyword": "pflegedienst sauerlach"}]},
        }
        original = copy.deepcopy(raw)

        normalized = normalize_agentseo_result(raw, self.target)

        self.assertEqual(raw, original)
        self.assertEqual(normalized["result"]["location"]["country_iso_code"], "DE")
        self.assertEqual(
            normalized["result"]["location"]["provider_country_iso_code"], "US"
        )
        self.assertEqual(
            normalized["location_validation"]["status"],
            "validated_with_provider_metadata_correction",
        )
        self.assertIn(
            "WARN_AGENTSEO_COUNTRY_ISO_METADATA_CORRECTED",
            normalized["location_validation"]["warnings"],
        )

    def test_serp_result_uses_explicit_location_code(self):
        raw = {
            "search_parameters": {
                "q": "pflegedienst sauerlach",
                "geo_target": {
                    "input": "Germany",
                    "source": "explicit_code",
                    "location_code": 2276,
                    "location_name": "Germany",
                    "country_iso_code": "US",
                },
                "language_used": "de",
                "location_used": "Germany",
            },
            "items": [{"rank": 1, "url": "https://example.de/"}],
        }

        normalized = normalize_agentseo_result(raw, self.target)

        geo = normalized["result"]["search_parameters"]["geo_target"]
        self.assertEqual(geo["location_code"], 2276)
        self.assertEqual(geo["location_name"], "Germany")
        self.assertEqual(geo["country_iso_code"], "DE")
        self.assertEqual(geo["provider_country_iso_code"], "US")

    def test_wrong_location_code_fails_fast(self):
        raw = {
            "location": {
                "input": "Germany",
                "location_code": 2840,
                "location_name": "United States",
                "country_iso_code": "US",
            }
        }

        with self.assertRaises(AgentSEOAdapterError) as caught:
            normalize_agentseo_result(raw, self.target)

        self.assertEqual(caught.exception.code, "ERROR_LOCATION_MISMATCH")

    def test_wrong_location_name_fails_fast(self):
        raw = {
            "location": {
                "input": "Germany",
                "location_code": 2276,
                "location_name": "Many,Louisiana,United States",
                "country_iso_code": "US",
            }
        }

        with self.assertRaises(AgentSEOAdapterError) as caught:
            normalize_agentseo_result(raw, self.target)

        self.assertEqual(caught.exception.code, "ERROR_LOCATION_MISMATCH")

    def test_keyword_payload_contains_all_required_market_fields(self):
        payload = build_keyword_metrics_payload(
            keywords=["pflegedienst sauerlach"],
            target=self.target,
            min_search_volume=0,
            sort_by="priority",
        )

        self.assertEqual(payload["location"], "Germany")
        self.assertEqual(payload["location_code"], 2276)
        self.assertEqual(payload["language"], "de")
        self.assertNotIn("sync", payload)

    def test_serp_payload_forces_undocumented_location_code(self):
        payload = build_serp_analysis_payload(
            keyword="pflegedienst sauerlach",
            target=self.target,
            device="desktop",
        )

        self.assertEqual(payload["location"], "Germany")
        self.assertEqual(payload["location_code"], 2276)
        self.assertEqual(payload["language"], "de")
        self.assertEqual(payload["device"], "desktop")

    def test_location_target_loads_from_binding_table(self):
        target = load_location_target(
            country="DE",
            path=REPO_ROOT / "standards" / "location-codes.json",
        )

        self.assertEqual(target, self.target)

    def test_unknown_country_fails_fast(self):
        with self.assertRaises(AgentSEOAdapterError) as caught:
            load_location_target(
                country="XX",
                path=REPO_ROOT / "standards" / "location-codes.json",
            )

        self.assertEqual(caught.exception.code, "ERROR_LOCATION_UNKNOWN")


if __name__ == "__main__":
    unittest.main()
