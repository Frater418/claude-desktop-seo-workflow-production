from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from services.domain_contract.validator import validate_project


def _error(code: str, message: str) -> dict[str, object]:
    return {"code": code, "message": message, "path": ["predecessor"], "remediation": "Submit an awaiting-gate candidate bound to the released predecessor."}


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _schema_errors(value: object, schema_name: str, root: Path) -> bool:
    runtime_schema = root / "standards" / "runtime" / schema_name
    schema_path = runtime_schema if runtime_schema.is_file() else root / "standards" / "outputs" / schema_name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return bool(list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value)))


def validate_lineage(
    bundle: dict[str, object],
    step_id: str,
    predecessor_step: str,
    gate_id: str,
    root: Path | None = None,
    candidate_schema_name: str | None = None,
) -> list[dict[str, object]]:
    """Validate immutable predecessor lineage for one awaiting-gate candidate."""
    candidate = bundle.get("candidate", bundle)
    if not isinstance(candidate, dict):
        return [
            _error("ERROR_PREFLIGHT_CANDIDATE_INVALID", "A canonical candidate object is required."),
            _error("ERROR_PREFLIGHT_PREDECESSOR_RELEASE_INVALID", "A released predecessor artifact and release record are required."),
        ]
    errors: list[dict[str, object]] = []
    resolved_root = root or _root()
    if candidate_schema_name and _schema_errors(candidate, candidate_schema_name, resolved_root):
        errors.append(_error("ERROR_PREFLIGHT_CANDIDATE_INVALID", "Candidate must match its closed output schema."))
    project = bundle.get("project")
    if not isinstance(project, dict) or not validate_project(project, resolved_root)["valid"]:
        errors.append(_error("ERROR_PREFLIGHT_PROJECT_IDENTITY_INVALID", "A valid canonical Project V2 record is required."))
    elif project.get("project_id") != candidate.get("project_id"):
        errors.append(_error("ERROR_PREFLIGHT_PROJECT_IDENTITY_INVALID", "Candidate and Project V2 must bind the same project."))
    elif candidate.get("deployment_id", "").startswith("dep-") and not any(
        deployment.get("deployment_id") == candidate["deployment_id"]
        for deployment in project["market_deployments"]
    ):
        errors.append(_error("ERROR_PREFLIGHT_PROJECT_IDENTITY_INVALID", "Candidate deployment must resolve in Project V2."))
    if candidate.get("candidate_status") != "awaiting_gate":
        errors.append(_error("ERROR_PREFLIGHT_CANDIDATE_STATUS_INVALID", "Candidate status must be awaiting_gate."))
    artifact = bundle.get("predecessor_artifact")
    release = bundle.get("predecessor_release")
    if not isinstance(artifact, dict) or not isinstance(release, dict):
        return errors + [_error("ERROR_PREFLIGHT_PREDECESSOR_RELEASE_INVALID", "A released predecessor artifact and release record are required.")]
    if _schema_errors(artifact, "artifact-record.schema.json", resolved_root) or _schema_errors(release, "release-record.schema.json", resolved_root):
        errors.append(_error("ERROR_PREFLIGHT_PREDECESSOR_RELEASE_INVALID", "Predecessor artifact and release records must match their runtime schemas."))
        return errors
    expected = {
        "step_id": predecessor_step,
        "gate_id": gate_id,
        "status": "released",
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": artifact["content_sha256"],
        "artifact_revision": artifact["revision"],
        "project_id": artifact["project_id"],
        "tenant_id": artifact["tenant_id"],
    }
    if any(release.get(key) != value for key, value in expected.items()):
        errors.append(_error("ERROR_PREFLIGHT_PREDECESSOR_RELEASE_INVALID", "Release must bind the exact released predecessor identity, hash, revision, step and gate."))
    if candidate.get("project_id") != artifact["project_id"]:
        errors.append(_error("ERROR_PREFLIGHT_PROJECT_IDENTITY_INVALID", "Candidate and predecessor must bind the same project."))
    if isinstance(project, dict) and project.get("tenant", {}).get("tenant_id") != artifact["tenant_id"]:
        errors.append(_error("ERROR_PREFLIGHT_PROJECT_IDENTITY_INVALID", "Project V2 and predecessor must bind the same tenant."))
    sources = candidate.get("source_artifact_ids")
    if not isinstance(sources, list) or artifact["artifact_id"] not in sources:
        errors.append(_error("ERROR_PREFLIGHT_SOURCE_ARTIFACT_INVALID", "Candidate source_artifact_ids must contain the released predecessor."))
    return errors
