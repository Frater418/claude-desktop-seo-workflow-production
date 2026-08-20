from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from services.step4b_preflight.validator import validate_step4b_candidate, validate_step4b_preflight


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "step4b"


def load_fixture(name: str) -> dict:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    page = value.get("page_spec", value)
    if isinstance(page, dict) and "service_area" in page:
        page.update({"language": "de", "locale": "de-DE", "project_id": "project-national-b2b", "deployment_id": "dep-national-b2b-de"})
        if "service_area" in page:
            page["service_area"]["areas"] = ["Germany"]
    if "page_spec" in value:
        value["project"] = json.loads((ROOT / "tests/fixtures/domain/real-customer-matrix/national-b2b.json").read_text(encoding="utf-8"))
    if isinstance(page, dict) and "html" in page:
        graph = {"@context": "https://schema.org", "@graph": [{"@id": "https://example.invalid/page#product", "@type": "Product", "name": "Verified page"}]}
        canonical_graph = json.dumps(graph, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        page["jsonld"] = {"level": "basic", "graph": graph, "graph_hash": __import__("hashlib").sha256(canonical_graph.encode("utf-8")).hexdigest()}
        payload = dict(page)
        payload.pop("content_sha256", None)
        page["content_sha256"] = __import__("hashlib").sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
        if isinstance(value.get("staging_evidence"), dict):
            value["staging_evidence"]["content_sha256"] = page["content_sha256"]
    return value


class Step4BContractTests(unittest.TestCase):
    def test_preflight_accepts_non_ahd_product_candidate_when_evidence_is_complete(self) -> None:
        # Given: a non-AHD product page and staging evidence fixture.
        bundle = load_fixture("non-ahd-product-bundle.json")

        # When: the Step 4b preflight validates the candidate.
        result = validate_step4b_candidate(bundle)

        # Then: the generic candidate is accepted without a market-specific rule.
        self.assertTrue(result["valid"], result["errors"])

    def test_positive_page_and_staging_evidence_validate(self) -> None:
        for schema_name, fixture_name in (
            ("step-4b-page-spec.schema.json", "positive-page-spec.json"),
            ("staging-evidence.schema.json", "positive-staging-evidence.json"),
        ):
            schema = json.loads((ROOT / "standards" / "outputs" / schema_name).read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema).iter_errors(load_fixture(fixture_name)))
            self.assertEqual([], errors, [error.message for error in errors])

    def test_preflight_accepts_safe_service_area_candidate(self) -> None:
        result = validate_step4b_candidate(load_fixture("positive-bundle.json"))
        self.assertTrue(result["valid"], result["errors"])

    def test_preflight_rejects_service_area_address_claim(self) -> None:
        result = validate_step4b_preflight(load_fixture("unsafe-service-area-bundle.json"))
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_STEP4B_SERVICE_AREA_UNSAFE", {error["code"] for error in result["errors"]})


if __name__ == "__main__":
    unittest.main()
