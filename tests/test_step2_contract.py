from __future__ import annotations

import unittest
from copy import deepcopy
import csv
import io
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from services.step2_preflight.render import render_step2
from services.step2_preflight.validator import validate_step2_candidate, validate_step2_preflight
from tests.support.pq0_2_step2 import load_pq0_2_fixture, pq0_2_operational_bundle, pq0_2_provider_records


ROOT = Path(__file__).resolve().parents[1]


def load_fixture() -> dict[str, object]:
    fixture = json.loads((ROOT / "tests/fixtures/step2/non-ahd-solar-fr-ca.json").read_text(encoding="utf-8"))
    fixture["candidate"]["candidate_status"] = "awaiting_gate"
    fixture["candidate"]["evidence_ids"] = [row["evidence_id"] for pillar in fixture["candidate"]["pillars"] for row in pillar["rows"]]
    fixture["candidate"]["language"] = "fr"
    fixture["candidate"]["geo"] = {"country_code": "CA", "provider_location_code": 1001}
    return fixture


class Step2ContractTests(unittest.TestCase):
    def test_accepts_contrasting_non_ahd_keyword_evidence(self) -> None:
        # Given: a non-AHD approved pillar with verified provider rows
        fixture = load_fixture()
        # When: Step 2 preflight evaluates the candidate
        result = validate_step2_candidate({"candidate": fixture["candidate"]})
        # Then: the candidate is ready for an awaiting-gate transition
        self.assertTrue(result["valid"])

    def test_accepts_contrasting_fixture_under_closed_output_contract(self) -> None:
        # Given: a non-AHD Step 2 output fixture and its closed schema
        fixture = load_fixture()
        schema = json.loads((ROOT / "standards/outputs/step-2-keyword-evidence.schema.json").read_text(encoding="utf-8"))
        # When: the schema validates the candidate
        errors = list(Draft202012Validator(schema).iter_errors(fixture["candidate"]))
        # Then: no market, language, pillar or provider specialization is needed
        self.assertEqual([], errors)

    def test_consolidates_incomplete_keyword_evidence_for_operator(self) -> None:
        # Given: an approved pillar below the mandatory evidence threshold
        fixture = load_fixture()
        bundle = {"candidate": fixture["candidate"]}
        bundle["candidate"]["pillars"][0]["rows"] = bundle["candidate"]["pillars"][0]["rows"][:-1]
        # When: Step 2 preflight evaluates the candidate
        result = validate_step2_candidate(bundle)
        # Then: the prompt surface exposes one actionable operator error
        self.assertFalse(result["valid"])
        self.assertEqual(1, len(result["errors"]))
        self.assertEqual("ERROR_STEP2_PREFLIGHT", result["errors"][0]["code"])


class Step2Pq0_2DeltaTests(unittest.TestCase):
    def test_pq0_2_001_accepts_only_25_to_40_candidate_rows(self) -> None:
        # Given: the dedicated local deterministic 25-row candidate
        candidate = load_pq0_2_fixture()["candidate"]
        pillar = candidate["pillars"][0]
        approved_families = set(pillar["approved_category_families"])
        covered_families = {row["category"] for row in pillar["rows"]}
        # When: the Step 2 candidate contract validates permitted breadth
        result = validate_step2_candidate({"candidate": candidate})
        # Then: the declared families are complete, valid, and count-bounded
        self.assertEqual(approved_families, covered_families)
        self.assertTrue(covered_families.issubset(approved_families))
        self.assertTrue(result["valid"])
        for count in (24, 41):
            with self.subTest(count=count):
                changed = deepcopy(candidate)
                rows = changed["pillars"][0]["rows"]
                while len(rows) < count:
                    additional = deepcopy(rows[0])
                    number = len(rows) + 1
                    additional["evidence_id"] = f"evidence-pq2-{number:04d}"
                    additional["title"] = f"Solar local landing page {number:02d}"
                    rows.append(additional)
                    changed["evidence_ids"].append(additional["evidence_id"])
                del rows[count:]
                changed["evidence_ids"] = [row["evidence_id"] for row in rows]
                self.assertFalse(validate_step2_candidate({"candidate": changed})["valid"])
        missing_family = deepcopy(candidate)
        for row in missing_family["pillars"][0]["rows"]:
            if row["category"] == "Transaktional":
                row["category"] = "Lokal"
        # When: a declared family has no verified rows despite preserving all 25 rows
        result = validate_step2_candidate({"candidate": missing_family})
        # Then: validation fails at the category-family coverage seam, not count alone
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_STEP2_CATEGORY_FAMILY_COVERAGE", result["errors"][0]["code"])

    def test_pq0_2_002_requires_typed_keyword_and_available_metrics(self) -> None:
        # Given: a full canonical local candidate
        candidate = load_pq0_2_fixture()["candidate"]
        # When: the public candidate validator evaluates it
        result = validate_step2_candidate({"candidate": candidate})
        # Then: title, keyword, search volume, and difficulty are accepted as typed fields
        self.assertTrue(result["valid"])

    def test_pq0_2_003_requires_solver_ready_classifications(self) -> None:
        # Given: a full canonical candidate with current EFFORT_WEIGHTS content types
        candidate = load_pq0_2_fixture()["candidate"]
        # When: its classifications reach the public validator
        result = validate_step2_candidate({"candidate": candidate})
        # Then: category and content type remain canonical solver inputs
        self.assertTrue(result["valid"])

    def test_rejects_whitespace_only_solver_and_family_text(self) -> None:
        # Given: otherwise canonical candidates with whitespace at a solver or family boundary
        candidate = load_pq0_2_fixture()["candidate"]
        cases = (
            ("title", lambda changed: changed["pillars"][0]["rows"][0].__setitem__("title", " \t")),
            ("keyword", lambda changed: changed["pillars"][0]["rows"][0].__setitem__("keyword", " \t")),
            ("category", lambda changed: changed["pillars"][0]["rows"][0].__setitem__("category", " \t")),
            ("approved_category_families", lambda changed: changed["pillars"][0]["approved_category_families"].__setitem__(0, " \t")),
        )
        for field, change in cases:
            with self.subTest(field=field):
                changed = deepcopy(candidate)
                change(changed)
                # When: the public candidate validator receives the whitespace-only text
                result = validate_step2_candidate({"candidate": changed})
                # Then: it fails at the schema/candidate boundary before solver use
                self.assertFalse(result["valid"])

    def test_pq0_2_004_rejects_candidate_metrics_that_drift_from_gateway_normalization(self) -> None:
        # Given: complete provider records derived from the local gateway fixture
        bundle = pq0_2_operational_bundle()
        bundle["candidate"]["pillars"][0]["rows"][0]["search_volume"] = 721
        # When: a candidate metric differs from its normalized evidence record
        result = validate_step2_preflight(bundle)
        # Then: preflight closes the exact evidence binding instead of accepting drift
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_STEP2_PROVIDER_BINDING", result["errors"][0]["code"])

    def test_pq0_2_005_accepts_complete_gateway_bound_candidate(self) -> None:
        # Given: every candidate row has one exact local provider exchange record
        bundle = pq0_2_operational_bundle()
        records = bundle["provider_evidence_records"]
        rows = bundle["candidate"]["pillars"][0]["rows"]
        # Then: each deterministic exchange has distinct identities and exact candidate bindings
        self.assertEqual(25, len({row["title"] for row in rows}))
        self.assertEqual(25, len({row["keyword"] for row in rows}))
        self.assertEqual(25, len({record["request"]["request_id"] for record in records}))
        self.assertEqual(25, len({record["response"]["response_id"] for record in records}))
        self.assertEqual(25, len({record["response"]["provider_job_id"] for record in records}))
        self.assertEqual(25, len({record["request"]["request_sha256"] for record in records}))
        self.assertEqual(25, len({record["response"]["raw_response_sha256"] for record in records}))
        for row, record in zip(rows, records, strict=True):
            metrics = record["response"]["raw_response"]["keyword_metrics"][0]
            self.assertEqual(row["keyword"], metrics["keyword"])
            self.assertEqual(row["search_volume"], metrics["search_volume"])
            self.assertEqual(row["difficulty"], metrics["difficulty"])
            self.assertNotIn("cpc_usd", metrics)
            self.assertEqual({"availability": "unavailable", "reason": "not_returned_by_provider"}, row["cpc_usd"])
            self.assertEqual(row["raw_response_sha256"], record["response"]["raw_response_sha256"])
        # When: operational preflight validates the full candidate
        result = validate_step2_preflight(bundle)
        # Then: request, response, job, provider, and raw-hash provenance remain bound
        self.assertTrue(result["valid"])

    def test_rejects_reused_provider_exchange_across_distinct_evidence_ids(self) -> None:
        # Given: two evidence wrappers that reuse one request, response, job, and raw exchange
        bundle = pq0_2_operational_bundle()
        reused = deepcopy(bundle["provider_evidence_records"][0])
        reused["evidence_id"] = bundle["provider_evidence_records"][1]["evidence_id"]
        bundle["provider_evidence_records"][1] = reused
        # When: operational preflight binds provider evidence to distinct candidate rows
        result = validate_step2_preflight(bundle)
        # Then: reused exchange provenance fails closed at the stable provider-binding seam
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_STEP2_PROVIDER_BINDING", result["errors"][0]["code"])

    def test_rejects_keyword_reused_across_distinct_pillars(self) -> None:
        # Given: a two-pillar candidate with unique rows and provider exchanges
        bundle = pq0_2_operational_bundle()
        primary_pillar = bundle["candidate"]["pillars"][0]
        secondary_pillar = deepcopy(primary_pillar)
        secondary_pillar["pillar_id"] = "pillar-national-b2b-secondary"
        for number, row in enumerate(secondary_pillar["rows"], start=1):
            row["evidence_id"] = f"evidence-pq2-secondary-{number:04d}"
            row["keyword"] = f"{row['keyword']} secondary"
        bundle["candidate"]["pillars"].append(secondary_pillar)
        bundle["candidate"]["evidence_ids"] = [
            row["evidence_id"]
            for pillar in bundle["candidate"]["pillars"]
            for row in pillar["rows"]
        ]
        bundle["provider_evidence_records"] = pq0_2_provider_records(bundle["candidate"])
        self.assertTrue(validate_step2_preflight(bundle)["valid"])

        # When: one otherwise independently evidenced keyword duplicates the first pillar
        secondary_pillar["rows"][0]["keyword"] = primary_pillar["rows"][0]["keyword"]
        bundle["provider_evidence_records"] = pq0_2_provider_records(bundle["candidate"])
        result = validate_step2_preflight(bundle)

        # Then: candidate-wide uniqueness fails at the stable provider-binding seam
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_STEP2_PROVIDER_BINDING", result["errors"][0]["code"])

    def test_rejects_provider_records_from_a_foreign_run(self) -> None:
        # Given: a valid local bundle whose exchange is rebadged to another run
        bundle = pq0_2_operational_bundle()
        for exchange in (bundle["provider_evidence_records"][0]["request"], bundle["provider_evidence_records"][0]["response"]):
            exchange["run_id"] = "run-foreign-0001"
        # When: Step 2 preflight binds the exchange to the candidate
        result = validate_step2_preflight(bundle)
        # Then: foreign run provenance fails at the stable binding seam
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_STEP2_PROVIDER_BINDING", result["errors"][0]["code"])

    def test_rejects_provider_records_from_a_foreign_source(self) -> None:
        # Given: a valid local bundle whose exchange names another source artifact
        bundle = pq0_2_operational_bundle()
        for exchange in (bundle["provider_evidence_records"][0]["request"], bundle["provider_evidence_records"][0]["response"]):
            exchange["source_artifact_ids"] = ["artifact-foreign-0001"]
        # When: Step 2 preflight binds the exchange to the candidate
        result = validate_step2_preflight(bundle)
        # Then: foreign source provenance fails at the stable binding seam
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_STEP2_PROVIDER_BINDING", result["errors"][0]["code"])

    def test_rejects_provider_records_with_a_stale_request_hash(self) -> None:
        # Given: a valid local bundle with one declared request hash changed after construction
        bundle = pq0_2_operational_bundle()
        bundle["provider_evidence_records"][0]["request"]["request_sha256"] = "f" * 64
        # When: Step 2 preflight checks its gateway-bound exchange
        result = validate_step2_preflight(bundle)
        # Then: stale request provenance fails at the stable binding seam
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_STEP2_PROVIDER_BINDING", result["errors"][0]["code"])

    def test_rejects_aliased_keyword_payload_and_raw_exchange(self) -> None:
        # Given: two distinct evidence records that claim the same local keyword response
        bundle = pq0_2_operational_bundle()
        first_row, second_row = bundle["candidate"]["pillars"][0]["rows"][:2]
        first_record, second_record = bundle["provider_evidence_records"][:2]
        for field in ("keyword", "search_volume", "difficulty", "cpc_usd", "raw_response_sha256"):
            second_row[field] = deepcopy(first_row[field])
        second_record["response"]["raw_response"] = deepcopy(first_record["response"]["raw_response"])
        second_record["response"]["raw_response_sha256"] = first_record["response"]["raw_response_sha256"]
        # When: Step 2 preflight binds evidence rows to normalized provider payloads
        result = validate_step2_preflight(bundle)
        # Then: duplicate keyword and raw response provenance cannot alias another record
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_STEP2_PROVIDER_BINDING", result["errors"][0]["code"])

    def test_pq0_2_006_preserves_25_verified_rows_per_approved_pillar(self) -> None:
        # Given: the exact 25-row lower boundary and complete provider evidence
        bundle = pq0_2_operational_bundle()
        # When: preflight receives the approved pillar
        result = validate_step2_preflight(bundle)
        # Then: the existing 25 verified rows threshold remains accepted
        self.assertTrue(result["valid"])

    def test_pq0_2_007_rejects_every_missing_required_canonical_row_field(self) -> None:
        # Given: canonical rows with one required field removed at a time
        candidate = load_pq0_2_fixture()["candidate"]
        required_fields = ("title", "keyword", "search_volume", "difficulty", "cpc_usd", "category", "content_type", "geo_type", "engine_target", "information_gain", "entity_density", "business_relevance", "mandatory_location_policy")
        for field in required_fields:
            with self.subTest(field=field):
                changed = deepcopy(candidate)
                del changed["pillars"][0]["rows"][0][field]
                result = validate_step2_candidate({"candidate": changed})
                # When: the public validator receives an incomplete canonical row
                # Then: it fails closed and identifies the missing field
                self.assertFalse(result["valid"])
                self.assertIn(field, result["errors"][0]["message"])

    def test_pq0_2_008_rejects_cpc_value_when_cpc_is_unavailable(self) -> None:
        # Given: an explicit unavailable CPC state that carries a fabricated value
        candidate = load_pq0_2_fixture()["candidate"]
        candidate["pillars"][0]["rows"][0]["cpc_usd"]["value"] = 0
        # When: the candidate validator receives that impossible representation
        result = validate_step2_candidate({"candidate": candidate})
        # Then: the CPC availability contract fails closed
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_STEP2_METRIC_INVALID", result["errors"][0]["code"])

    def test_pq0_2_009_rejects_non_solver_content_type(self) -> None:
        # Given: a canonical candidate whose content type is outside EFFORT_WEIGHTS
        candidate = load_pq0_2_fixture()["candidate"]
        candidate["pillars"][0]["rows"][0]["content_type"] = "unsupported-content-type"
        # When: the public validator receives the classification
        result = validate_step2_candidate({"candidate": candidate})
        # Then: it rejects the non-solver classification
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_STEP2_CLASSIFICATION_INVALID", result["errors"][0]["code"])

    def test_pq0_2_010_renders_typed_fields_without_raw_provider_payload(self) -> None:
        # Given: a complete local candidate with exact provider records
        bundle = pq0_2_operational_bundle()
        # When: the public Step 2 renderer emits deterministic CSV
        rendered = render_step2(bundle)
        # Then: the canonical typed fields are present and raw provider payload is absent
        header = rendered.splitlines()[0].split(",")
        rows = list(csv.DictReader(io.StringIO(rendered)))
        self.assertEqual(rendered, render_step2(bundle))
        self.assertTrue({"title", "keyword", "search_volume", "difficulty", "cpc_usd", "category", "content_type", "geo_type", "engine_target", "information_gain", "entity_density", "business_relevance", "mandatory_location_policy", "is_mandatory"}.issubset(header))
        self.assertEqual("true", rows[0]["is_mandatory"])
        self.assertIn("raw_response_sha256", header)
        self.assertEqual(bundle["candidate"]["pillars"][0]["rows"][0]["raw_response_sha256"], rows[0]["raw_response_sha256"])
        self.assertNotIn("raw_response", header)
        self.assertNotIn("keyword_metrics", rendered)
        self.assertNotIn("local-deterministic-only", rendered)
