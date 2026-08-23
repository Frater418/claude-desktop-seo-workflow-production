"""Versioned Quality Gate Registry applicability and binding evaluator.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import json
from pathlib import Path


def load_registry(root: Path | None = None) -> dict:
    root = root or Path(__file__).resolve().parents[2]
    path = root / "standards" / "quality" / "quality-gate-registry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _error(code: str, gate: dict, message: str) -> dict:
    return {
        "code": code,
        "gate_id": gate["gate_id"],
        "message": message,
        "remediation": gate["remediation"],
    }


def _applicability(gate: dict, context: dict) -> tuple[bool, dict | None]:
    applicability = gate["applicability"]
    if applicability == "always":
        return True, None
    if applicability == "when_existing_site":
        status = context.get("site_status")
        if status == "existing_site":
            return True, None
        if status == "non_existing_site":
            return False, None
        return False, _error("ERROR_GATE_APPLICABILITY_UNDECIDED", gate, "Site status is not explicitly declared.")
    flag_map = {
        "when_multilingual": "multilingual",
        "when_ymyl": "ymyl",
        "when_local": "local",
        "when_production": "production",
    }
    if applicability in flag_map:
        flag = flag_map[applicability]
        if flag not in context:
            return False, _error("ERROR_GATE_APPLICABILITY_UNDECIDED", gate, f"Applicability flag '{flag}' is missing.")
        return bool(context[flag]), None
    if applicability == "when_configured":
        gate_tools = {tool["tool_id"] for tool in gate["tools"]}
        configured = gate_tools.intersection(set(context.get("configured_tools", [])))
        if not configured:
            decision = context.get("not_applicable_decisions", {}).get(gate["gate_id"])
            if not isinstance(decision, dict) or len(str(decision.get("reason", ""))) < 10:
                return False, _error(
                    "ERROR_GATE_APPLICABILITY_UNDECIDED",
                    gate,
                    "Configured-source gate requires an explicit not-applicable decision when no source is configured.",
                )
            return False, None
        unavailable = configured.difference(set(context.get("available_tools", [])))
        if unavailable:
            return False, _error(
                "ERROR_CONFIGURED_GATE_TOOL_UNAVAILABLE",
                gate,
                f"Configured gate tools are unavailable: {', '.join(sorted(unavailable))}.",
            )
        return True, None
    return False, _error("ERROR_GATE_APPLICABILITY_UNDECIDED", gate, f"Unknown applicability: {applicability}.")


def resolve_required_gates(registry: dict, step_id: str, operation: str, context: dict) -> dict:
    required: list[dict] = []
    not_applicable: list[str] = []
    errors: list[dict] = []
    for gate in registry["gates"]:
        if step_id not in gate["steps"] or operation not in gate["blocks_operations"]:
            continue
        applies, error = _applicability(gate, context)
        if error is not None:
            errors.append(error)
        elif applies:
            required.append(gate)
        else:
            not_applicable.append(gate["gate_id"])
    errors.sort(key=lambda item: (item["code"], item["gate_id"]))
    required.sort(key=lambda item: item["gate_id"])
    return {
        "valid": not errors,
        "required_gates": required,
        "required_gate_ids": [gate["gate_id"] for gate in required],
        "not_applicable_gate_ids": sorted(not_applicable),
        "errors": errors,
    }


def evaluate_gate_runs(
    registry: dict,
    step_id: str,
    operation: str,
    context: dict,
    tenant_id: str,
    run_id: str,
    human_gate_id: str,
    current_artifact: dict,
    supporting_artifacts: list[dict],
    quality_gate_runs: list[dict],
) -> dict:
    resolution = resolve_required_gates(registry, step_id, operation, context)
    errors = list(resolution["errors"])
    human_gates: list[dict] = []
    allowed_support = {
        (artifact["artifact_id"], artifact["content_sha256"], artifact.get("run_id"))
        for artifact in supporting_artifacts
    }
    revision_sources = [*supporting_artifacts]
    if "artifact_id" in current_artifact:
        revision_sources.append(current_artifact)
    artifact_revisions = {
        (artifact["artifact_id"], artifact["content_sha256"], artifact.get("run_id")): artifact.get("revision")
        for artifact in revision_sources
    }
    for gate in resolution["required_gates"]:
        if gate["stage"] == "human_approval":
            human_gates.append(gate)
            continue
        matching = []
        for record in quality_gate_runs:
            if (
                record.get("quality_gate_id") != gate["gate_id"]
                or record.get("tenant_id") != tenant_id
                or record.get("step_id") != step_id
                or record.get("human_gate_id") != human_gate_id
                or record.get("result") != "passed"
            ):
                continue
            binding = (
                record.get("artifact_id"),
                record.get("artifact_sha256"),
                record.get("run_id"),
            )
            if "artifact_revision" in record and record["artifact_revision"] != artifact_revisions.get(binding):
                continue
            if gate["binding_scope"] == "current_artifact":
                if binding != (current_artifact["artifact_id"], current_artifact["content_sha256"], run_id):
                    continue
            elif gate["binding_scope"] in {"supporting_artifact", "external_evidence"}:
                if binding not in allowed_support and binding != (
                    current_artifact["artifact_id"], current_artifact["content_sha256"], run_id
                ):
                    continue
            matching.append(record)
        if not matching:
            errors.append(_error("ERROR_REQUIRED_QUALITY_GATE_MISSING", gate, "No current passed quality-gate run matches the required binding scope."))
            continue
        record = matching[0]
        if record.get("registry_version") != registry["schema_version"]:
            errors.append(
                _error(
                    "ERROR_REQUIRED_QUALITY_GATE_REGISTRY_VERSION",
                    gate,
                    "Quality-gate run does not bind the active registry version.",
                )
            )
        evidence = record.get("evidence")
        missing_evidence = [
            key
            for key in gate["evidence_required"]
            if not isinstance(evidence, dict) or key not in evidence or evidence[key] in ("", None, [], {})
        ]
        if missing_evidence:
            errors.append(
                _error(
                    "ERROR_REQUIRED_QUALITY_GATE_EVIDENCE",
                    gate,
                    f"Quality-gate run omits required evidence: {', '.join(missing_evidence)}.",
                )
            )
        if (
            gate["binding_scope"] == "external_evidence"
            and "provenance_classification" in gate["evidence_required"]
            and (not isinstance(evidence, dict) or evidence.get("provenance_classification") != "external_report")
        ):
            errors.append(
                _error(
                    "ERROR_REQUIRED_QUALITY_GATE_PROVENANCE",
                    gate,
                    "External evidence requires provenance_classification to be external_report.",
                )
            )
        if gate["binding_scope"] == "external_evidence" and (
            not isinstance(evidence, dict) or evidence.get("raw_evidence_artifact_sha256") != record.get("artifact_sha256")
        ):
            errors.append(
                _error(
                    "ERROR_REQUIRED_QUALITY_GATE_RAW_EVIDENCE",
                    gate,
                    "Configured external evidence must bind its raw-evidence artifact hash.",
                )
            )
    errors.sort(key=lambda item: (item["code"], item["gate_id"]))
    return {
        "valid": not errors,
        "required_gate_ids": resolution["required_gate_ids"],
        "human_gate_definitions": human_gates,
        "not_applicable_gate_ids": resolution["not_applicable_gate_ids"],
        "errors": errors,
    }
