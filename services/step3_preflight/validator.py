"""Fail-fast validation for deterministic Step 3 plans."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping, TypeAlias
from jsonschema import Draft202012Validator, FormatChecker
from services.preflight_common import validate_lineage
from services.step2_preflight.validator import validate_step2_candidate


JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]


def _items(value: JsonValue | None) -> list[Mapping[str, JsonValue]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _canonical_payload(value: JsonValue | None) -> tuple[dict[str, JsonValue] | None, str | None]:
    if not isinstance(value, str):
        return None, None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None, None
    if not isinstance(parsed, dict):
        return None, None
    canonical = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if value != canonical:
        return None, None
    return parsed, hashlib.sha256(value.encode("utf-8")).hexdigest()


def _schema_valid(candidate: Mapping[str, JsonValue]) -> bool:
    schema_path = Path(__file__).resolve().parents[2] / "standards" / "outputs" / "step-3-plan.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return not list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(candidate))


def step2_solver_projection(candidate: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    rows = candidate.get("pillars")
    projection_rows = [
        {"evidence_id": row["evidence_id"], "keyword": row["keyword"], "pillar_id": pillar["pillar_id"], "provider": row["provider"], "raw_response_sha256": row["raw_response_sha256"]}
        for pillar in rows if isinstance(rows, list) and isinstance(pillar, dict)
        for row in pillar.get("rows", []) if isinstance(row, dict)
    ]
    return {"rows": sorted(projection_rows, key=lambda row: (row["pillar_id"], row["keyword"], row["evidence_id"]))}


def validate_step3_candidate(bundle: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """Return one operator-surface error when a plan cannot await Gate 3."""
    if not _schema_valid(bundle):
        return {"valid": False, "errors": [{"code": "ERROR_STEP3_PREFLIGHT", "message": "Plan must match the closed awaiting-gate Step 3 candidate schema.", "path": ["plan"], "remediation": "Submit only the complete canonical awaiting-gate candidate."}]}
    weeks = _items(bundle.get("weeks"))
    item_ids = {
        item_id
        for week in weeks
        for item_id in (week.get("item_ids") if isinstance(week.get("item_ids"), list) else [])
        if isinstance(item_id, str)
    }
    valid_capacity = all(
        isinstance(week.get("capacity_hours"), int | float)
        and 0 < week["capacity_hours"] <= 15
        for week in weeks
    )
    mandatory = bundle.get("mandatory_item_ids")
    mandatory_ids = mandatory if isinstance(mandatory, list) else []
    valid_mandatory = bool(mandatory_ids) and all(item_id in item_ids for item_id in mandatory_ids)
    valid_graphs = bool(_items(bundle.get("vertical_links"))) and bool(_items(bundle.get("horizontal_links")))
    solver_input, input_hash = _canonical_payload(bundle.get("solver_input"))
    solver_output, output_hash = _canonical_payload(bundle.get("solver_output"))
    valid_evidence = (
        solver_input is not None
        and solver_output is not None
        and bundle.get("solver_input_sha256") == input_hash
        and bundle.get("solver_output_sha256") == output_hash
        and all(solver_output.get(key) == bundle.get(key) for key in ("weeks", "mandatory_item_ids", "backlog_item_ids", "vertical_links", "horizontal_links"))
        and solver_input.get("rows") is not None
        and "solver_input_sha256" not in solver_output
        and "solver_output_sha256" not in solver_output
    )
    if len(weeks) != 17 or not valid_capacity or not valid_mandatory or not valid_graphs or not valid_evidence:
        return {
            "valid": False,
            "errors": [{
                "code": "ERROR_STEP3_PREFLIGHT",
                "message": "Plan requires canonical solver input and output bytes, matching SHA-256 values and solver-derived plan fields.",
                "path": ["plan"],
                "remediation": "Run the deterministic solver from verified Step 2 evidence and submit only awaiting_gate.",
            }],
        }
    return {"valid": True, "errors": []}


def validate_step3_preflight(bundle: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    candidate = bundle.get("candidate") if isinstance(bundle.get("candidate"), dict) else bundle
    result = validate_step3_candidate(candidate)
    lineage_errors = validate_lineage(dict(bundle), "3", "2", "GATE-2", candidate_schema_name="step-3-plan.schema.json")
    if lineage_errors:
        return {"valid": False, "errors": lineage_errors}
    predecessor_content = bundle.get("predecessor_content")
    artifact = bundle.get("predecessor_artifact")
    if not isinstance(predecessor_content, str) or not isinstance(artifact, dict):
        return {"valid": False, "errors": [{"code": "ERROR_STEP3_PREFLIGHT", "message": "Step 3 requires canonical released Step 2 content bytes.", "path": ["predecessor_content"], "remediation": "Supply the exact released Step 2 canonical content."}]}
    if hashlib.sha256(predecessor_content.encode("utf-8")).hexdigest() != artifact.get("content_sha256"):
        return {"valid": False, "errors": [{"code": "ERROR_STEP3_PREFLIGHT", "message": "Released Step 2 bytes do not match the predecessor artifact hash.", "path": ["predecessor_content"], "remediation": "Supply the exact released Step 2 canonical content."}]}
    try:
        predecessor = json.loads(predecessor_content)
    except json.JSONDecodeError:
        predecessor = None
    if not isinstance(predecessor, dict) or predecessor_content != json.dumps(predecessor, ensure_ascii=False, separators=(",", ":"), sort_keys=True) or not validate_step2_candidate({"candidate": predecessor})["valid"]:
        return {"valid": False, "errors": [{"code": "ERROR_STEP3_PREFLIGHT", "message": "Released Step 2 content must be a valid canonical candidate.", "path": ["predecessor_content"], "remediation": "Supply the verified canonical Step 2 candidate bytes."}]}
    if candidate.get("solver_input") != json.dumps(step2_solver_projection(predecessor), ensure_ascii=False, separators=(",", ":"), sort_keys=True):
        return {"valid": False, "errors": [{"code": "ERROR_STEP3_PREFLIGHT", "message": "Solver input must equal the deterministic projection of released Step 2 rows.", "path": ["candidate", "solver_input"], "remediation": "Rebuild the solver input from the released Step 2 canonical content."}]}
    return result
