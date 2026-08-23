"""Fail-fast validation for Step 3 deterministic plan candidates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping, TypeAlias

from jsonschema import Draft202012Validator, FormatChecker

from services.canonical_json import canonical_json_bytes
from services.preflight_common import validate_lineage
from services.step2_preflight.validator import validate_step2_candidate
from services.step3_preflight.solver_bridge import (
    SolverBridgeError,
    derive_step3_plan_fields,
    step2_solver_projection,
)


JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
_MACHINE_FIELD_NAMES = (
    "solver_version",
    "solver_input",
    "solver_output",
    "solver_input_sha256",
    "solver_output_sha256",
    "weeks",
    "mandatory_item_ids",
    "backlog_item_ids",
    "vertical_links",
    "horizontal_links",
)


def _error(code: str, message: str, path: list[str], remediation: str = "Run the deterministic solver from released Step 2 evidence and submit its canonical output.") -> dict[str, JsonValue]:
    return {"valid": False, "errors": [{"code": code, "message": message, "path": path, "remediation": remediation}]}


def _canonical_payload(value: JsonValue | None) -> tuple[dict[str, JsonValue] | None, str | None]:
    if not isinstance(value, str):
        return None, None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None, None
    if not isinstance(parsed, dict):
        return None, None
    canonical = canonical_json_bytes(parsed).decode("utf-8")
    if value != canonical:
        return None, None
    return parsed, hashlib.sha256(value.encode("utf-8")).hexdigest()


def _schema_valid(candidate: Mapping[str, JsonValue]) -> bool:
    schema_path = Path(__file__).resolve().parents[2] / "standards" / "outputs" / "step-3-plan.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return not list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(candidate))


def _item_map(solver_input: dict[str, JsonValue]) -> dict[str, Mapping[str, JsonValue]] | None:
    items = solver_input.get("items")
    if not isinstance(items, list) or not items:
        return None
    mapped = {item.get("item_id"): item for item in items if isinstance(item, dict) and isinstance(item.get("item_id"), str)}
    if len(mapped) != len(items) or any(not isinstance(item.get("pillar"), str) or not isinstance(item.get("is_mandatory"), bool) for item in mapped.values()):
        return None
    return mapped


def _valid_machine_fields(candidate: Mapping[str, JsonValue]) -> bool:
    solver_input, input_hash = _canonical_payload(candidate.get("solver_input"))
    solver_output, output_hash = _canonical_payload(candidate.get("solver_output"))
    if solver_input is None or solver_output is None or candidate.get("solver_input_sha256") != input_hash or candidate.get("solver_output_sha256") != output_hash:
        return False
    if set(solver_output) != set(_MACHINE_FIELD_NAMES[5:]) or any(solver_output.get(name) != candidate.get(name) for name in _MACHINE_FIELD_NAMES[5:]):
        return False
    item_map = _item_map(solver_input)
    weeks = candidate.get("weeks")
    backlog_ids = candidate.get("backlog_item_ids")
    mandatory_ids = candidate.get("mandatory_item_ids")
    vertical_links = candidate.get("vertical_links")
    horizontal_links = candidate.get("horizontal_links")
    if item_map is None or not isinstance(weeks, list) or not isinstance(backlog_ids, list) or not isinstance(mandatory_ids, list) or not isinstance(vertical_links, list) or not isinstance(horizontal_links, list):
        return False
    if [week.get("week") for week in weeks if isinstance(week, dict)] != list(range(1, 18)) or len(weeks) != 17:
        return False
    if any(not isinstance(week, dict) or not isinstance(week.get("capacity_hours"), int | float) or not 0 <= week["capacity_hours"] <= 15 or not isinstance(week.get("item_ids"), list) or len(week["item_ids"]) != len(set(week["item_ids"])) for week in weeks):
        return False
    scheduled_ids = [item_id for week in weeks for item_id in week["item_ids"]]
    input_ids = set(item_map)
    if len(scheduled_ids) != len(set(scheduled_ids)) or len(backlog_ids) != len(set(backlog_ids)) or set(scheduled_ids) & set(backlog_ids) or set(scheduled_ids) | set(backlog_ids) != input_ids:
        return False
    expected_mandatory = sorted(item_id for item_id, item in item_map.items() if item["is_mandatory"])
    scheduled_weeks = {item_id: week["week"] for week in weeks for item_id in week["item_ids"]}
    if mandatory_ids != expected_mandatory or any(scheduled_weeks.get(item_id, 18) > 8 for item_id in mandatory_ids):
        return False
    vertical_pairs = [(link.get("source_item_id"), link.get("target_pillar_id")) for link in vertical_links if isinstance(link, dict)]
    expected_vertical = {(item_id, item["pillar"]) for item_id, item in item_map.items()}
    if len(vertical_pairs) != len(vertical_links) or len(vertical_pairs) != len(set(vertical_pairs)) or set(vertical_pairs) != expected_vertical or vertical_pairs != sorted(vertical_pairs):
        return False
    horizontal_pairs = [(link.get("source_item_id"), link.get("target_item_id")) for link in horizontal_links if isinstance(link, dict)]
    if len(horizontal_pairs) != len(horizontal_links) or len(horizontal_pairs) != len(set(horizontal_pairs)) or horizontal_pairs != sorted(horizontal_pairs):
        return False
    if any(source not in item_map or target not in item_map or source == target or item_map[source]["pillar"] != item_map[target]["pillar"] for source, target in horizontal_pairs):
        return False
    sibling_pillars = {item["pillar"] for item in item_map.values() if sum(other["pillar"] == item["pillar"] for other in item_map.values()) >= 2}
    return not sibling_pillars or bool(horizontal_pairs)


def validate_step3_candidate(bundle: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """Return one operator-surface error when a plan cannot await Gate 3."""
    if not _schema_valid(bundle) or not _valid_machine_fields(bundle):
        return _error("ERROR_STEP3_PREFLIGHT", "Plan requires canonical solver input and output bytes, matching SHA-256 values and a self-consistent machine plan.", ["plan"])
    return {"valid": True, "errors": []}


def validate_step3_preflight(bundle: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """Accept only a candidate exactly derived from released canonical Step 2 bytes."""
    candidate = bundle.get("candidate") if isinstance(bundle.get("candidate"), dict) else bundle
    result = validate_step3_candidate(candidate)
    if not result["valid"]:
        return result
    execution_identity = bundle.get("execution_identity")
    expected_execution_identity = {
        "project_id": candidate.get("project_id"),
        "run_id": candidate.get("run_id"),
        "step_id": candidate.get("step_id"),
        "target_revision": candidate.get("revision"),
    }
    if not isinstance(execution_identity, dict) or any(execution_identity.get(key) != value for key, value in expected_execution_identity.items()):
        return _error("ERROR_STEP3_EXECUTION_IDENTITY_INVALID", "Candidate project, run, step and revision must match trusted provider execution identity.", ["execution_identity"], "Submit the candidate returned by the trusted provider execution.")
    predecessor_content = bundle.get("predecessor_content")
    artifact = bundle.get("predecessor_artifact")
    if not isinstance(predecessor_content, str) or not isinstance(artifact, dict) or hashlib.sha256(predecessor_content.encode("utf-8")).hexdigest() != artifact.get("content_sha256"):
        return _error("ERROR_STEP3_PREFLIGHT", "Step 3 requires exact released Step 2 canonical content bytes matching the artifact hash.", ["predecessor_content"])
    try:
        predecessor = json.loads(predecessor_content)
    except json.JSONDecodeError:
        predecessor = None
    if not isinstance(predecessor, dict) or predecessor_content != json.dumps(predecessor, ensure_ascii=False, separators=(",", ":"), sort_keys=True) or not validate_step2_candidate(predecessor)["valid"]:
        return _error("ERROR_STEP3_PREFLIGHT", "Released Step 2 content must be a valid canonical candidate.", ["predecessor_content"])
    if candidate.get("deployment_id") != predecessor.get("deployment_id"):
        return _error("ERROR_STEP3_PREDECESSOR_DEPLOYMENT_INVALID", "Candidate deployment must exactly match released Step 2 deployment.", ["candidate", "deployment_id"], "Use the deployment bound to the released Step 2 candidate.")
    if candidate.get("evidence_ids") != predecessor.get("evidence_ids"):
        return _error("ERROR_STEP3_PREDECESSOR_EVIDENCE_INVALID", "Candidate evidence_ids must exactly match released Step 2 evidence_ids.", ["candidate", "evidence_ids"], "Use the canonical evidence_ids from the released Step 2 candidate.")
    if candidate.get("source_artifact_ids") != [artifact.get("artifact_id")]:
        return _error("ERROR_STEP3_PREDECESSOR_SOURCE_ARTIFACT_INVALID", "Candidate source_artifact_ids must contain only the released Step 2 artifact.", ["candidate", "source_artifact_ids"], "Use only the released Step 2 artifact as the Step 3 source.")
    lineage_errors = validate_lineage(dict(bundle), "3", "2", "GATE-2", candidate_schema_name="step-3-plan.schema.json")
    if lineage_errors:
        return {"valid": False, "errors": lineage_errors}
    try:
        derived = derive_step3_plan_fields(predecessor)
    except SolverBridgeError:
        return _error("ERROR_STEP3_SOLVER_DERIVATION_MISMATCH", "Released Step 2 evidence cannot produce the required deterministic Step 3 plan.", ["candidate"])
    if any(candidate.get(name) != derived[name] for name in _MACHINE_FIELD_NAMES):
        return _error("ERROR_STEP3_SOLVER_DERIVATION_MISMATCH", "Step 3 machine fields do not exactly match the deterministic derivation from released Step 2 bytes.", ["candidate"])
    return result
