from __future__ import annotations

import unittest
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from services.provider_gateway.core import ProviderGatewayError, canonical_request_sha256, validate_exchange


ROOT = Path(__file__).resolve().parents[1]


def load_fixture() -> dict[str, object]:
    fixture = json.loads((ROOT / "tests/fixtures/provider_gateway/non-ahd-agentseo-fr-ca.json").read_text(encoding="utf-8"))
    raw_response = fixture["response"]["raw_response"]
    fixture["response"]["raw_response_sha256"] = hashlib.sha256(
        json.dumps(raw_response, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()
    return fixture


class ProviderGatewayTests(unittest.TestCase):
    def test_validates_contrasting_non_ahd_provider_evidence(self) -> None:
        # Given: a complete non-AHD provider request and completed raw response
        fixture = load_fixture()
        request = fixture["request"]
        response = fixture["response"]
        # When: the provider gateway validates the exchange
        result = validate_exchange(request, response)
        # Then: immutable provider-neutral evidence is returned
        self.assertEqual(response["provider"], result["provider"])
        expected_digest = hashlib.sha256(
            json.dumps(response["raw_response"], ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ).hexdigest()
        self.assertEqual(expected_digest, result["raw_response_sha256"])

    def test_rejects_tampered_raw_response_with_stale_declared_hash(self) -> None:
        # Given: a completed response whose declared hash belongs to different raw content
        fixture = load_fixture()
        request = fixture["request"]
        response = fixture["response"]
        response["raw_response"] = {"tasks": ["tampered"]}
        # When: the provider gateway validates the exchange
        with self.assertRaises(ProviderGatewayError) as captured:
            validate_exchange(request, response)
        # Then: the stable provider-gateway violation rejects the stale declaration
        self.assertEqual("ERROR_PROVIDER_GATEWAY", captured.exception.code)
        self.assertIn("raw_response_hash_mismatch", captured.exception.violations)

    def test_rejects_stale_request_hash_before_keyword_normalization(self) -> None:
        # Given: a schema-valid local request whose declared hash belongs to prior request content
        fixture = load_fixture()
        fixture["request"]["request_sha256"] = "f" * 64
        # When: the provider gateway validates the local exchange
        with self.assertRaises(ProviderGatewayError) as captured:
            validate_exchange(fixture["request"], fixture["response"])
        # Then: the stable mismatch prevents normalization from trusting stale provenance
        self.assertIn("request_hash_mismatch", captured.exception.violations)

    def test_accepts_contrasting_fixture_under_both_provider_contracts(self) -> None:
        # Given: a contrasting provider-neutral fixture and both closed contracts
        fixture = load_fixture()
        request_schema = json.loads((ROOT / "standards/providers/research-request.schema.json").read_text(encoding="utf-8"))
        response_schema = json.loads((ROOT / "standards/providers/research-response.schema.json").read_text(encoding="utf-8"))
        # When: each provider contract validates the fixture side
        request_errors = list(Draft202012Validator(request_schema).iter_errors(fixture["request"]))
        response_errors = list(Draft202012Validator(response_schema).iter_errors(fixture["response"]))
        # Then: the non-AHD data remains valid without special handling
        self.assertEqual([], request_errors)
        self.assertEqual([], response_errors)

    def test_consolidates_provider_failures_at_operator_surface(self) -> None:
        # Given: a response with every fail-fast provider defect
        fixture = load_fixture()
        request = fixture["request"]
        invalid = fixture["response"]
        invalid.update({"provider_job_id": "", "raw_response": None})
        invalid["geo"] = {"country_code": "AT", "provider_location_code": 2276}
        invalid["cost"] = {"currency": "USD", "actual": None}
        invalid["status"] = "timeout"
        # When: the provider gateway validates the exchange
        with self.assertRaises(ProviderGatewayError) as captured:
            validate_exchange(request, invalid)
        # Then: the operator receives exactly one consolidated error
        self.assertEqual("ERROR_PROVIDER_GATEWAY", captured.exception.code)
        self.assertGreaterEqual(len(captured.exception.violations), 5)


class ProviderGatewayNormalizationDeltaTests(unittest.TestCase):
    def load_normalization_fixture(self) -> dict[str, object]:
        return json.loads(
            (ROOT / "tests/fixtures/provider_gateway/pq0-2-local-normalized-keyword.json").read_text(encoding="utf-8")
        )

    def test_normalizes_local_keyword_metrics_with_explicit_cpc_unavailability(self) -> None:
        # Given: a local deterministic raw keyword response with no CPC metric
        fixture = self.load_normalization_fixture()
        self.assertNotIn("cpc_usd", fixture["response"]["raw_response"]["keyword_metrics"][0])
        # When: the public provider gateway validates and normalizes the exchange
        result = validate_exchange(fixture["request"], fixture["response"])
        # Then: available metrics remain numeric and unavailable CPC has no fabricated value
        normalized = result["normalized_keyword_records"]
        self.assertEqual(fixture["normalized_keyword_records"], normalized)
        cpc = normalized[0]["metrics"]["cpc_usd"]
        self.assertEqual("unavailable", cpc["availability"])
        self.assertNotIn("value", cpc)

    def test_rejects_missing_null_or_negative_available_metric_without_defaulting(self) -> None:
        # Given: local raw responses with invalid available metric values
        fixture = self.load_normalization_fixture()
        for metric_name in ("search_volume", "difficulty"):
            for invalid_value in ("missing", None, -1):
                with self.subTest(metric_name=metric_name, invalid_value=invalid_value):
                    exchange = deepcopy(fixture)
                    metrics = exchange["response"]["raw_response"]["keyword_metrics"][0]
                    if invalid_value == "missing":
                        del metrics[metric_name]
                    else:
                        metrics[metric_name] = invalid_value
                    exchange["response"]["raw_response_sha256"] = hashlib.sha256(
                        json.dumps(exchange["response"]["raw_response"], ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
                    ).hexdigest()
                    # When: the gateway receives malformed available metrics
                    with self.assertRaises(ProviderGatewayError) as captured:
                        validate_exchange(exchange["request"], exchange["response"])
                    # Then: it fails instead of inferring a provider default or zero
                    self.assertIn(f"normalized_metric_invalid:{metric_name}", captured.exception.violations)

    def test_binds_normalization_provenance_to_validated_exchange_hashes(self) -> None:
        # Given: one local deterministic request-response exchange
        fixture = self.load_normalization_fixture()
        # When: the gateway returns its normalized provider-neutral record
        result = validate_exchange(fixture["request"], fixture["response"])
        # Then: every provenance identity comes from the validated exchange
        provenance = result["normalized_keyword_records"][0]["provenance"]
        self.assertEqual(fixture["request"]["request_sha256"], provenance["request_sha256"])
        self.assertEqual(result["raw_response_sha256"], provenance["raw_response_sha256"])
        self.assertEqual(fixture["response"]["provider_job_id"], provenance["provider_job_id"])
        self.assertEqual(fixture["response"]["provider"], provenance["provider"])
        self.assertEqual({"identifier": "heartweb.keyword-metrics", "version": "1.0.0"}, provenance["normalizer"])

    def test_preserves_serp_passthrough_and_rejects_malformed_normalization_inputs(self) -> None:
        # Given: a valid non-keyword exchange and malformed keyword evidence variants
        fixture = self.load_normalization_fixture()
        serp = deepcopy(fixture)
        serp["request"]["operation"] = "serp_analysis"
        serp["request"]["request_sha256"] = canonical_request_sha256(serp["request"])
        malformed = (
            ("whitespace", lambda exchange: exchange["response"]["raw_response"]["keyword_metrics"][0].update({"keyword": "  "}), "normalized_metric_invalid:keyword"),
            ("non-string-id", lambda exchange: exchange["response"].update({"evidence_ids": [1]}), "normalized_metric_invalid:evidence_ids"),
            ("duplicate-id", lambda exchange: exchange["response"].update({"evidence_ids": ["evidence-pq2-0001", "evidence-pq2-0001"]}) or exchange["response"]["raw_response"].update({"keyword_metrics": [exchange["response"]["raw_response"]["keyword_metrics"][0], exchange["response"]["raw_response"]["keyword_metrics"][0]]}), "normalized_metric_invalid:evidence_ids"),
        )
        # When: gateway validation dispatches each exchange
        self.assertNotIn("normalized_keyword_records", validate_exchange(serp["request"], serp["response"]))
        for name, mutate, violation in malformed:
            with self.subTest(name=name):
                exchange = deepcopy(fixture)
                mutate(exchange)
                exchange["response"]["raw_response_sha256"] = hashlib.sha256(json.dumps(exchange["response"]["raw_response"], ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
                # Then: malformed normalization input fails closed without an exception leak
                with self.assertRaises(ProviderGatewayError) as captured:
                    validate_exchange(exchange["request"], exchange["response"])
                self.assertIn(violation, captured.exception.violations)
