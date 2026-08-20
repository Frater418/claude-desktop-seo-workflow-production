from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from services.preflight_common import validate_lineage


def validate_step3b_candidate(adjustment: object, root: Path | None = None) -> dict[str, object]:
    root = root or Path(__file__).resolve().parents[2]
    schema = json.loads((root / "standards" / "outputs" / "step-3b-adjustment.schema.json").read_text(encoding="utf-8"))
    errors = [{"code": "ERROR_STEP3B_ADJUSTMENT_INVALID", "message": error.message, "path": list(error.absolute_path)} for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(adjustment)]
    if isinstance(adjustment, dict):
        source_plan = adjustment.get("source_plan", {})
        proposed_plan = adjustment.get("proposed_plan", {})
        if (
            source_plan.get("artifact_id") == proposed_plan.get("artifact_id")
            or source_plan.get("artifact_id") not in adjustment.get("source_artifact_ids", [])
            or proposed_plan.get("revision", 0) <= source_plan.get("revision", 0)
            or proposed_plan.get("content_sha256") == source_plan.get("content_sha256")
        ):
            errors.append({"code": "ERROR_STEP3B_PLAN_IMMUTABILITY_INVALID", "message": "Adjustment must reference, not overwrite, the released Step 3 plan.", "path": ["adjustment", "source_plan"]})
    return {"valid": not errors, "errors": errors}


def validate_step3b_preflight(bundle: dict[str, object], root: Path | None = None) -> dict[str, object]:
    adjustment = bundle.get("adjustment")
    result = validate_step3b_candidate(adjustment, root)
    result["errors"].extend(validate_lineage({**bundle, "candidate": adjustment}, "3b", "3", "GATE-3", root, "step-3b-adjustment.schema.json"))
    predecessor = bundle.get("predecessor_artifact")
    source_plan = adjustment.get("source_plan") if isinstance(adjustment, dict) else None
    if isinstance(predecessor, dict) and isinstance(source_plan, dict) and any(source_plan.get(field) != predecessor.get(field) for field in ("artifact_id", "revision", "content_sha256")):
        result["errors"].append({"code": "ERROR_STEP3B_SOURCE_PLAN_INVALID", "message": "Source plan must bind the exact released Step 3 artifact record.", "path": ["adjustment", "source_plan"]})
    result["valid"] = not result["errors"]
    return result
