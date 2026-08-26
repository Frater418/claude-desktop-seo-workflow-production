from __future__ import annotations

import unittest
import json
import hashlib
from pathlib import Path
from unittest.mock import patch

import mcp as mcp_sdk

ROOT = Path(__file__).resolve().parents[1]
local_mcp_path = str(ROOT / "mcp")
if local_mcp_path not in mcp_sdk.__path__:
    mcp_sdk.__path__.append(local_mcp_path)

from mcp.tools.capacity_matrix_solver import CapacityValidationError, solve_capacity_plan
from jsonschema import Draft202012Validator
from services.step3_preflight import validator as step3_validator
from services.step3_preflight.solver_bridge import SolverBridgeError
from services.step3_preflight.validator import validate_step3_candidate, validate_step3_preflight
from tests.test_preflight_common import _predecessor
from tests.test_step3_renderer import _operational_bundle

MACHINE_PLAN_FIELDS = (
    "weeks",
    "mandatory_item_ids",
    "backlog_item_ids",
    "vertical_links",
    "horizontal_links",
)
DERIVED_FIELD_NAMES = {
    "solver_version",
    "solver_input",
    "solver_output",
    "solver_input_sha256",
    "solver_output_sha256",
    *MACHINE_PLAN_FIELDS,
}


def load_fixture() -> dict[str, object]:
    fixture = json.loads((ROOT / "tests/fixtures/step3/non-ahd-solar-fr-ca.json").read_text(encoding="utf-8"))
    fixture["candidate"]["candidate_status"] = "awaiting_gate"
    for value in (fixture["candidate"], fixture["preflight_bundle"]):
        item_ids = [item_id for week in value["weeks"] for item_id in week["item_ids"]] + value["backlog_item_ids"]
        pillar_id = value["vertical_links"][0]["target_pillar_id"]
        input_payload = {"items": [{"item_id": item_id, "pillar": pillar_id, "is_mandatory": item_id in value["mandatory_item_ids"]} for item_id in item_ids]}
        value["vertical_links"] = [{"source_item_id": item_id, "target_pillar_id": pillar_id} for item_id in sorted(item_ids)]
        output = {key: value[key] for key in ("weeks", "mandatory_item_ids", "backlog_item_ids", "vertical_links", "horizontal_links")}
        value.pop("input_sha256", None)
        value.pop("output_sha256", None)
        value["solver_input"] = json.dumps(input_payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        value["solver_output"] = json.dumps(output, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        value["solver_input_sha256"] = hashlib.sha256(value["solver_input"].encode("utf-8")).hexdigest()
        value["solver_output_sha256"] = hashlib.sha256(value["solver_output"].encode("utf-8")).hexdigest()
    return fixture


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _released_pq0_step2() -> tuple[dict[str, object], str, dict[str, object], dict[str, object]]:
    fixture = json.loads((ROOT / "tests/fixtures/step2/pq0-2-canonical-candidate.json").read_text(encoding="utf-8"))
    candidate = fixture["candidate"]
    content = _canonical(candidate)
    content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    artifact, release = _predecessor("2", "GATE-2")
    artifact.update({"artifact_id": candidate["artifact_id"], "content_sha256": content_sha256, "project_id": candidate["project_id"], "revision": candidate["revision"], "run_id": candidate["run_id"]})
    release.update({"artifact_id": artifact["artifact_id"], "artifact_sha256": content_sha256, "artifact_revision": artifact["revision"], "project_id": artifact["project_id"], "run_id": artifact["run_id"]})
    return candidate, content, artifact, release


def _source_rows(candidate: dict[str, object]) -> list[tuple[str, dict[str, object]]]:
    return [(pillar["pillar_id"], row) for pillar in candidate["pillars"] for row in pillar["rows"]]


def _derive(released_step2: dict[str, object]) -> dict[str, object]:
    return getattr(step3_validator, "derive_step3_plan_fields")(released_step2)


class Step3ContractTests(unittest.TestCase):
    def test_accepts_contrasting_non_ahd_deterministic_plan(self) -> None:
        # Given: a non-AHD capacity-bounded plan with both link graphs
        fixture = load_fixture()
        # When: Step 3 preflight evaluates the candidate
        result = validate_step3_candidate(fixture["candidate"])
        # Then: the deterministic plan is ready for an awaiting-gate transition
        self.assertTrue(result["valid"])

    def test_accepts_contrasting_fixture_under_closed_output_contract(self) -> None:
        # Given: a non-AHD Step 3 output fixture and its closed schema
        fixture = load_fixture()
        schema = json.loads((ROOT / "standards/outputs/step-3-plan.schema.json").read_text(encoding="utf-8"))
        # When: the schema validates the candidate
        errors = list(Draft202012Validator(schema).iter_errors(fixture["candidate"]))
        # Then: the plan has no market, language, capacity or link specialization
        self.assertEqual([], errors)

    def test_consolidates_invalid_plan_constraints_for_operator(self) -> None:
        # Given: a plan missing a week, mandatory work, and its horizontal graph
        fixture = load_fixture()
        bundle = fixture["preflight_bundle"]
        bundle["weeks"] = bundle["weeks"][:-1]
        bundle["mandatory_item_ids"] = []
        bundle["horizontal_links"] = []
        # When: Step 3 preflight evaluates the candidate
        result = validate_step3_candidate(bundle)
        # Then: the prompt surface exposes one actionable operator error
        self.assertFalse(result["valid"])
        self.assertEqual(1, len(result["errors"]))
        self.assertEqual("ERROR_STEP3_PREFLIGHT", result["errors"][0]["code"])

    def test_pq0_3_001_projects_all_released_step2_solver_items(self) -> None:
        # Given: exact canonical released Step 2 content with verified rows only
        released_step2, content, artifact, release = _released_pq0_step2()
        # When: Step 3 builds its public solver projection without side data
        projection = step3_validator.step2_solver_projection(released_step2)
        # Then: each source row has a deterministic complete solver item
        self.assertEqual(_canonical(released_step2), content)
        self.assertEqual(hashlib.sha256(content.encode("utf-8")).hexdigest(), artifact["content_sha256"])
        self.assertEqual(artifact["content_sha256"], release["artifact_sha256"])
        self.assertIn("items", projection)
        items = projection["items"]
        self.assertEqual(len(_source_rows(released_step2)), len(items))
        self.assertEqual(items, sorted(items, key=lambda item: (item["pillar"], item["keyword"], item["item_id"])))
        by_item_id = {item["item_id"]: item for item in items}
        for pillar_id, row in _source_rows(released_step2):
            expected = {
                "item_id": row["evidence_id"], "pillar": pillar_id, "title": row["title"], "keyword": row["keyword"],
                "search_volume": row["search_volume"], "difficulty": row["difficulty"], "category": row["category"],
                "content_type": row["content_type"], "geo_type": row["geo_type"], "engine_target": row["engine_target"],
                "information_gain": row["information_gain"], "entity_density": row["entity_density"],
                "business_relevance": row["business_relevance"], "is_mandatory": row["mandatory_location_policy"]["state"] == "required",
                "provider": row["provider"], "raw_response_sha256": row["raw_response_sha256"],
            }
            self.assertEqual(expected, {key: by_item_id[row["evidence_id"]][key] for key in expected})

    def test_accepts_exact_canonical_released_step2_bytes_in_step3_preflight(self) -> None:
        # Given: a deterministic Step 3 bundle bound to released canonical Step 2 content
        bundle = _operational_bundle()
        predecessor_content = bundle["predecessor_content"]
        predecessor_artifact = bundle["predecessor_artifact"]
        # When: Step 3 consumes the persisted predecessor bytes unchanged
        result = validate_step3_preflight(bundle)
        # Then: the canonical bytes and their immutable hash remain acceptable lineage
        self.assertEqual(_canonical(json.loads(predecessor_content)), predecessor_content)
        self.assertEqual(hashlib.sha256(predecessor_content.encode("utf-8")).hexdigest(), predecessor_artifact["content_sha256"])
        self.assertTrue(result["valid"], result["errors"])

    def test_pq0_3_003_derives_real_solver_schedule_and_backlog(self) -> None:
        # Given: canonical released Step 2 content and the real capacity solver
        released_step2, _, _, _ = _released_pq0_step2()
        # When: the public derivation seam produces Step 3 machine fields
        fields = _derive(released_step2)
        # Then: the 17-week bridge preserves real placement, empty weeks, and backlog
        solver_input = json.loads(fields["solver_input"])
        real_output = solve_capacity_plan(solver_input["items"])
        expected_weeks = [{"week": week["week"], "capacity_hours": week["hours"], "item_ids": [item["item_id"] for item in week["items"]]} for week in real_output["weeks"]]
        self.assertEqual(expected_weeks, fields["weeks"])
        self.assertEqual(list(range(1, 18)), [week["week"] for week in fields["weeks"]])
        self.assertTrue(all(0 <= week["capacity_hours"] <= 15 for week in fields["weeks"]))
        self.assertTrue(any(not week["item_ids"] for week in fields["weeks"]))
        scheduled = [item_id for week in fields["weeks"] for item_id in week["item_ids"]]
        input_ids = [item["item_id"] for item in solver_input["items"]]
        self.assertEqual(len(input_ids), len(scheduled) + len(fields["backlog_item_ids"]))
        self.assertEqual(set(input_ids), set(scheduled) | set(fields["backlog_item_ids"]))
        self.assertEqual(len(scheduled), len(set(scheduled)))
        self.assertEqual(len(fields["backlog_item_ids"]), len(set(fields["backlog_item_ids"])))
        self.assertFalse(set(scheduled) & set(fields["backlog_item_ids"]))
        self.assertEqual(fields["backlog_item_ids"], [item["item_id"] for item in real_output["unplaced"]])
        mandatory_ids = sorted(item["item_id"] for item in solver_input["items"] if item["is_mandatory"])
        scheduled_weeks = {item_id: week["week"] for week in fields["weeks"] for item_id in week["item_ids"]}
        self.assertEqual(mandatory_ids, fields["mandatory_item_ids"])
        self.assertTrue(all(scheduled_weeks[item_id] <= 8 for item_id in mandatory_ids))

    def test_pq0_3_004_binds_canonical_machine_fields_and_link_maps(self) -> None:
        # Given: the exact released PQ0 Step 2 candidate
        released_step2, _, _, _ = _released_pq0_step2()
        # When: deterministic Step 3 machine fields are derived
        fields = _derive(released_step2)
        # Then: hashes bind canonical bytes and maps cover the released evidence graph
        self.assertEqual(DERIVED_FIELD_NAMES, set(fields))
        self.assertEqual("1.3.0", fields["solver_version"])
        self.assertEqual(_canonical(json.loads(fields["solver_input"])), fields["solver_input"])
        self.assertEqual(_canonical(json.loads(fields["solver_output"])), fields["solver_output"])
        self.assertEqual(hashlib.sha256(fields["solver_input"].encode("utf-8")).hexdigest(), fields["solver_input_sha256"])
        self.assertEqual(hashlib.sha256(fields["solver_output"].encode("utf-8")).hexdigest(), fields["solver_output_sha256"])
        self.assertEqual({key: fields[key] for key in MACHINE_PLAN_FIELDS}, json.loads(fields["solver_output"]))
        input_items = json.loads(fields["solver_input"])["items"]
        input_ids = {item["item_id"] for item in input_items}
        expected_vertical = {(item["item_id"], item["pillar"]) for item in input_items}
        actual_vertical = {(link["source_item_id"], link["target_pillar_id"]) for link in fields["vertical_links"]}
        self.assertEqual(expected_vertical, actual_vertical)
        horizontal = [(link["source_item_id"], link["target_item_id"]) for link in fields["horizontal_links"]]
        self.assertEqual(horizontal, sorted(horizontal))
        self.assertTrue(horizontal)
        self.assertTrue(all(source in input_ids and target in input_ids and source != target for source, target in horizontal))

    def test_pq0_3_005_rejects_self_consistent_machine_fields_not_derived_from_release(self) -> None:
        # Given: a schema-valid candidate with self-consistent hashes and a released Step 2 bundle
        bundle = _operational_bundle()
        self.assertTrue(validate_step3_candidate(bundle["candidate"])["valid"])
        bundle["candidate"]["solver_version"] = "manual-1.3.0"
        # When: preflight evaluates manually supplied plan fields
        result = validate_step3_preflight(bundle)
        # Then: only a real derivation from the release can pass the deterministic bridge
        self.assertFalse(result["valid"])
        self.assertEqual(["ERROR_STEP3_SOLVER_DERIVATION_MISMATCH"], [error["code"] for error in result["errors"]])

    def test_rejects_candidate_deployment_not_bound_to_released_step2(self) -> None:
        # Given: a complete plan derived from a released Step 2 candidate
        bundle = _operational_bundle()
        bundle["candidate"]["deployment_id"] = "dep-national-b2b-fr"
        # When: operational preflight checks predecessor provenance
        result = validate_step3_preflight(bundle)
        # Then: deployment identity cannot be substituted after derivation
        self.assertFalse(result["valid"])
        self.assertEqual(["ERROR_STEP3_PREDECESSOR_DEPLOYMENT_INVALID"], [error["code"] for error in result["errors"]])

    def test_rejects_candidate_evidence_not_bound_to_released_step2(self) -> None:
        # Given: a complete plan with one substituted evidence identifier
        bundle = _operational_bundle()
        bundle["candidate"]["evidence_ids"] = ["evidence-forged-0001"]
        # When: operational preflight checks predecessor provenance
        result = validate_step3_preflight(bundle)
        # Then: only the exact released evidence set is accepted
        self.assertFalse(result["valid"])
        self.assertEqual(["ERROR_STEP3_PREDECESSOR_EVIDENCE_INVALID"], [error["code"] for error in result["errors"]])

    def test_rejects_candidate_source_artifacts_not_exactly_released_step2(self) -> None:
        # Given: a complete plan that adds an untrusted source artifact
        bundle = _operational_bundle()
        bundle["candidate"]["source_artifact_ids"].append("artifact-forged-0001")
        # When: operational preflight checks predecessor provenance
        result = validate_step3_preflight(bundle)
        # Then: the released predecessor is the sole permitted source
        self.assertFalse(result["valid"])
        self.assertEqual(["ERROR_STEP3_PREDECESSOR_SOURCE_ARTIFACT_INVALID"], [error["code"] for error in result["errors"]])

    def test_rejects_candidate_run_id_not_bound_to_trusted_execution(self) -> None:
        # Given: a complete plan whose candidate run differs from provider execution identity
        bundle = _operational_bundle()
        bundle["candidate"]["run_id"] = "run-forged-0001"
        # When: operational preflight checks trusted execution identity
        result = validate_step3_preflight(bundle)
        # Then: current execution run identity cannot be forged from the candidate
        self.assertFalse(result["valid"])
        self.assertEqual(["ERROR_STEP3_EXECUTION_IDENTITY_INVALID"], [error["code"] for error in result["errors"]])

    def test_translates_solver_validation_error_before_preflight(self) -> None:
        # Given: an otherwise valid release whose solver rejects its projected input
        bundle = _operational_bundle()
        solver_error = CapacityValidationError("ERROR_SOLVER_REQUIRED_FIELD_MISSING", "required solver input is absent")
        with patch("services.step3_preflight.solver_bridge.solve_capacity_plan", side_effect=solver_error):
            # When: direct derivation crosses the solver boundary
            with self.assertRaises(SolverBridgeError) as context:
                _derive(json.loads(bundle["predecessor_content"]))
            # Then: the bridge exposes only its stable translation code
            self.assertEqual("ERROR_STEP3_SOLVER_INPUT_INVALID", str(context.exception))
            # When: preflight derives from the same released source
            result = validate_step3_preflight(bundle)
        # Then: the operator surface remains structured and fail-closed
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_STEP3_SOLVER_DERIVATION_MISMATCH", result["errors"][0]["code"])
