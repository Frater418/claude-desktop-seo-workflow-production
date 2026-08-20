from __future__ import annotations

import unittest
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from services.provider_gateway.core import ProviderGatewayError, validate_exchange


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
