import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[2]
DOMAIN_DIR = ROOT / "standards" / "domain"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "domain"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


DOMAIN_SCHEMA_NAMES = (
    "project.schema.json",
    "search-deployment.schema.json",
    "entity-domain-gbp.schema.json",
    "risk-compliance.schema.json",
    "market-registry.schema.json",
)


def build_schema_registry():
    schemas = {name: load_json(DOMAIN_DIR / name) for name in DOMAIN_SCHEMA_NAMES}
    registry = Registry()
    for schema in schemas.values():
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return schemas, registry


def foundation_error_code(project, market_by_id, validator):
    deployments = project.get("market_deployments", [])
    for deployment in deployments:
        if "locale" not in deployment:
            return "E_DOMAIN_LOCALE_REQUIRED"
    risk = project.get("risk_compliance", {})
    if risk.get("ymyl") is True and not risk.get("claim_evidence"):
        return "E_COMPLIANCE_YMYL_EVIDENCE_REQUIRED"

    if list(validator.iter_errors(project)):
        return "E_DOMAIN_SCHEMA_INVALID"

    for deployment in deployments:
        registered_market = market_by_id.get(deployment["market_id"])
        if registered_market is None:
            return "E_DOMAIN_MARKET_UNKNOWN"
        for field in ("country_code", "language", "locale", "legal_jurisdiction"):
            if deployment.get(field) != registered_market[field]:
                return "E_DOMAIN_GEO_MISMATCH"

    locations = {
        location["location_id"]: location
        for location in project["entity_domain_gbp"]["physical_locations"]
    }
    for profile in project["entity_domain_gbp"]["gbp_profiles"]:
        location = locations.get(profile["location_id"])
        if location is None or location["evidence_status"] != "verified":
            return "E_DOMAIN_LOCAL_PRESENCE_UNVERIFIED"

    entities = project["entity_domain_gbp"]
    domain_ids = {domain["domain_id"] for domain in entities["domains"]}
    location_ids = set(locations)
    service_area_ids = {area["service_area_id"] for area in entities["service_areas"]}
    for deployment in project["market_deployments"]:
        if deployment["brand_id"] != entities["brand"]["brand_id"]:
            return "E_DOMAIN_REFERENCE_UNKNOWN"
        if not set(deployment["domain_ids"]) <= domain_ids:
            return "E_DOMAIN_REFERENCE_UNKNOWN"
        if not set(deployment["physical_location_ids"]) <= location_ids:
            return "E_DOMAIN_REFERENCE_UNKNOWN"
        if not set(deployment["service_area_ids"]) <= service_area_ids:
            return "E_DOMAIN_REFERENCE_UNKNOWN"

    return None


class RealCustomerDomainFixturesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas, cls.schema_registry = build_schema_registry()
        cls.project_validator = Draft202012Validator(
            cls.schemas["project.schema.json"],
            registry=cls.schema_registry,
            format_checker=FormatChecker(),
        )
        registry = load_json(DOMAIN_DIR / "market-registry.json")
        cls.market_by_id = {market["market_id"]: market for market in registry["markets"]}

    def test_market_registry_is_closed_and_has_no_unverified_codes(self):
        registry_schema = load_json(DOMAIN_DIR / "market-registry.schema.json")
        registry = load_json(DOMAIN_DIR / "market-registry.json")
        self.assertEqual(registry_schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertTrue(registry_schema["additionalProperties"] is False)
        self.assertEqual(registry["registry_version"], "v1.1.0")
        self.assertTrue({"DE", "AT", "CH", "FR", "LU", "LK", "ID", "AE", "GB", "US"} <= {market["country_code"] for market in registry["markets"]})
        errors = list(
            Draft202012Validator(
                registry_schema,
                registry=self.schema_registry,
                format_checker=FormatChecker(),
            ).iter_errors(registry)
        )
        self.assertEqual([], errors, [error.message for error in errors])
        for market in registry["markets"]:
            verification = market["provider_location_verification"]
            if verification["status"] != "verified":
                self.assertIsNone(verification["provider_location_code"])

    def test_domain_schemas_have_closed_draft_2020_12_contracts(self):
        for schema_name in DOMAIN_SCHEMA_NAMES:
            with self.subTest(schema=schema_name):
                schema = load_json(DOMAIN_DIR / schema_name)
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(
                    schema["$id"],
                    f"https://heartweb.example/schema/{schema_name}",
                )
                self.assertTrue(schema["additionalProperties"] is False)

    def test_all_ten_real_customer_archetypes_validate(self):
        fixtures = sorted((FIXTURE_DIR / "real-customer-matrix").glob("*.json"))
        self.assertEqual(len(fixtures), 10)
        for fixture_path in fixtures:
            with self.subTest(fixture=fixture_path.name):
                project = load_json(fixture_path)
                schema_errors = list(self.project_validator.iter_errors(project))
                self.assertEqual([], schema_errors, [error.message for error in schema_errors])
                self.assertIsNone(
                    foundation_error_code(project, self.market_by_id, self.project_validator)
                )

    def test_every_positive_deployment_reference_resolves(self):
        for fixture_path in sorted((FIXTURE_DIR / "real-customer-matrix").glob("*.json")):
            with self.subTest(fixture=fixture_path.name):
                project = load_json(fixture_path)
                self.assertIsNone(foundation_error_code(project, self.market_by_id, self.project_validator))

    def test_geo_mismatch_returns_stable_code(self):
        project = load_json(FIXTURE_DIR / "negative-geo-mismatch.json")
        self.assertEqual([], list(self.project_validator.iter_errors(project)))
        self.assertEqual(
            foundation_error_code(project, self.market_by_id, self.project_validator),
            "E_DOMAIN_GEO_MISMATCH",
        )

    def test_missing_locale_returns_stable_code(self):
        project = load_json(FIXTURE_DIR / "negative-missing-locale.json")
        self.assertTrue(list(self.project_validator.iter_errors(project)))
        self.assertEqual(
            foundation_error_code(project, self.market_by_id, self.project_validator),
            "E_DOMAIN_LOCALE_REQUIRED",
        )

    def test_unverified_local_presence_returns_stable_code(self):
        project = load_json(FIXTURE_DIR / "negative-unverified-local-presence.json")
        self.assertEqual([], list(self.project_validator.iter_errors(project)))
        self.assertEqual(
            foundation_error_code(project, self.market_by_id, self.project_validator),
            "E_DOMAIN_LOCAL_PRESENCE_UNVERIFIED",
        )

    def test_missing_ymyl_evidence_returns_stable_code(self):
        project = load_json(FIXTURE_DIR / "negative-missing-ymyl-evidence.json")
        self.assertTrue(list(self.project_validator.iter_errors(project)))
        self.assertEqual(
            foundation_error_code(project, self.market_by_id, self.project_validator),
            "E_COMPLIANCE_YMYL_EVIDENCE_REQUIRED",
        )


if __name__ == "__main__":
    unittest.main()
