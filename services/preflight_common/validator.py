"""Reusable closed-candidate and lineage enforcement."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


def validate_submission(bundle: dict, schema_name: str, step_id: str, root: Path) -> list[dict]:
    """Validate a canonical V2 candidate when a cross-step submission is supplied."""
    candidate = bundle.get("candidate")
    if not isinstance(candidate, dict):
        return []
    schema = json.loads((root / "standards" / "outputs" / schema_name).read_text(encoding="utf-8"))
    errors = [{"code": f"ERROR_STEP{step_id.upper()}_PREFLIGHT", "message": item.message, "path": ["candidate", *item.absolute_path]} for item in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(candidate)]
    required = ("project", "predecessor_release", "gate_record")
    missing = [name for name in required if not isinstance(bundle.get(name), dict)]
    if missing:
        errors.append({"code": "ERROR_PREFLIGHT_PREDECESSOR_MISSING", "message": "Cross-step submission requires Project V2, released predecessor, and gate record.", "path": missing})
        return errors
    project = bundle["project"]
    predecessor = bundle["predecessor_release"]
    gate = bundle["gate_record"]
    if candidate.get("candidate_status") != "awaiting_gate" or candidate.get("step_id") != step_id:
        errors.append({"code": "ERROR_PREFLIGHT_CANDIDATE_INVALID", "message": "Candidate must bind the current step and awaiting_gate state.", "path": ["candidate"]})
    if candidate.get("project_id") != project.get("project_id") or candidate.get("deployment_id") not in {item.get("deployment_id") for item in project.get("market_deployments", [])}:
        errors.append({"code": "ERROR_PREFLIGHT_PROJECT_INVALID", "message": "Candidate identity must bind Project V2 and a declared deployment.", "path": ["candidate"]})
    sources = candidate.get("source_artifact_ids", [])
    if predecessor.get("status") != "released" or predecessor.get("artifact_id") not in sources or predecessor.get("artifact_revision") is None or predecessor.get("artifact_sha256") is None:
        errors.append({"code": "ERROR_PREFLIGHT_PREDECESSOR_INVALID", "message": "Released predecessor must be a sourced artifact with revision and SHA-256.", "path": ["predecessor_release"]})
    if gate.get("artifact_id") != predecessor.get("artifact_id") or gate.get("artifact_sha256") != predecessor.get("artifact_sha256"):
        errors.append({"code": "ERROR_PREFLIGHT_GATE_INVALID", "message": "Gate record must bind the released predecessor artifact and hash.", "path": ["gate_record"]})
    return errors
