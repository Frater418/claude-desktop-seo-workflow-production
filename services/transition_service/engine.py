"""Pure transition evaluation authority."""

from __future__ import annotations

import copy

from services.quality_gate_registry import evaluate_gate_runs, load_registry

from .contracts import STATE_RULES, approval_errors, error, fingerprint, human_quality_gate_run, load_workflow_graph, predecessor_ok, release_record


def process_transition(command: dict, run: dict, current_artifact: dict | None, supporting_artifacts: list[dict] | None = None, quality_gate_runs: list[dict] | None = None, approval: dict | None = None, predecessor_release: dict | None = None, context: dict | None = None, idempotency_ledger: dict[str, str] | None = None, max_attempts: int = 3, registry: dict | None = None, graph: dict | None = None) -> dict:
    """Evaluate one transition without partial state mutation."""
    supporting_artifacts, quality_gate_runs, context, idempotency_ledger = supporting_artifacts or [], quality_gate_runs or [], context or {}, idempotency_ledger or {}
    registry, graph = registry or load_registry(), graph or load_workflow_graph()
    errors: list[tuple[str, str]] = []
    command_fingerprint = fingerprint(command)
    previous_fingerprint = idempotency_ledger.get(command.get("idempotency_key"))
    if previous_fingerprint and previous_fingerprint != command_fingerprint:
        errors.append(("ERR_IDEMPOTENCY_CONFLICT", "Idempotency key was already used for a different command."))
    elif previous_fingerprint == command_fingerprint:
        return {"ok": True, "replay": True, "command_fingerprint": command_fingerprint, "run": copy.deepcopy(run), "human_quality_gate_run": None, "release_record": None, "errors": []}
    if any(command.get(key) != value for key, value in {"tenant_id": run.get("tenant_id"), "project_id": run.get("project_id"), "run_id": run.get("run_id")}.items()):
        errors.append(("ERR_TENANT_ISOLATION", "Command tenant, project or run identity does not match the current run."))
    if command.get("expected_revision") != run.get("revision"):
        errors.append(("ERR_STALE_REVISION", "Command expected revision does not match the current run revision."))
    if command.get("input_hash") != run.get("input_hash"):
        errors.append(("ERR_STALE_REVISION", "Command input hash does not match the current run input hash."))
    operation = command.get("operation")
    if operation not in STATE_RULES:
        errors.append(("ERR_TRANSITION_NOT_ALLOWED", f"Unsupported operation: {operation}."))
    else:
        allowed_states, _ = STATE_RULES[operation]
        if run.get("status") not in allowed_states:
            errors.append(("ERR_TRANSITION_NOT_ALLOWED", f"Operation {operation} is not allowed from status {run.get('status')}."))
    if command.get("to_step_id") != run.get("step_id"):
        errors.append(("ERR_TRANSITION_NOT_ALLOWED", "Command target step does not match the current run step."))
    if operation in {"approve", "complete", "publish", "retry", "supersede"} and command.get("from_step_id") != run.get("step_id"):
        errors.append(("ERR_TRANSITION_NOT_ALLOWED", "Same-step operation must use the current step as source and target."))
    if operation in {"start", "submit_for_gate", "post_publication"} and not predecessor_ok(command, graph, run, predecessor_release):
        errors.append(("ERR_TRANSITION_NOT_ALLOWED", "A matching released predecessor and workflow edge are required."))
    artifact_required = operation in {"submit_for_gate", "post_publication", "approve", "complete", "publish"}
    if artifact_required and not isinstance(current_artifact, dict):
        errors.append(("ERR_ARTIFACT_REQUIRED", "Current artifact is required for this transition."))
    elif isinstance(current_artifact, dict):
        if any(current_artifact.get(key) != value for key, value in {"tenant_id": run.get("tenant_id"), "project_id": run.get("project_id"), "run_id": run.get("run_id"), "step_id": run.get("step_id")}.items()):
            errors.append(("ERR_ARTIFACT_REQUIRED", "Current artifact identity does not match the run."))
        if command.get("output_hash") and command.get("output_hash") != current_artifact.get("content_sha256"):
            errors.append(("ERR_ARTIFACT_REQUIRED", "Command output hash does not match the current artifact."))
    if operation == "retry" and int(run.get("attempt", 1)) >= max_attempts:
        errors.append(("ERR_RETRY_EXHAUSTED", "Retry attempt limit is exhausted."))
    gate_result = None
    if not errors and operation == "start" and (current_artifact is not None or not bool(context.get("local_workflow", False))):
        gate_result = evaluate_gate_runs(registry, run["step_id"], operation, context, run["tenant_id"], run["run_id"], run["gate_id"], current_artifact or {}, supporting_artifacts, quality_gate_runs)
        errors.extend(("ERR_GATE_REQUIRED", f"{item['gate_id']}: {item['message']}") for item in gate_result["errors"])
    if not errors and artifact_required:
        gate_operation = "submit_for_gate" if operation in {"submit_for_gate", "approve", "complete"} else operation
        gate_result = evaluate_gate_runs(registry, run["step_id"], gate_operation, context, run["tenant_id"], run["run_id"], run["gate_id"], current_artifact, supporting_artifacts, quality_gate_runs)
        errors.extend(("ERR_GATE_REQUIRED", f"{item['gate_id']}: {item['message']}") for item in gate_result["errors"])
    human_gate_defs: list[dict] = []
    if not errors and operation in {"approve", "complete", "publish"}:
        human_result = evaluate_gate_runs(registry, run["step_id"], "approve" if operation != "publish" else "publish", context, run["tenant_id"], run["run_id"], run["gate_id"], current_artifact, supporting_artifacts, quality_gate_runs)
        human_gate_defs = human_result["human_gate_definitions"]
        errors.extend(("ERR_GATE_REQUIRED", f"{item['gate_id']}: {item['message']}") for item in human_result["errors"])
        errors.extend(("ERR_APPROVAL_STALE", item) for item in approval_errors(approval, run, current_artifact, command["requested_at"]))
        if len(human_gate_defs) != 1:
            errors.append(("ERR_GATE_REQUIRED", "Exactly one applicable human gate definition is required."))
    if not errors and operation in {"complete", "publish"}:
        human_gate_id = human_gate_defs[0]["gate_id"]
        if not any(record.get("quality_gate_id") == human_gate_id and record.get("tenant_id") == run["tenant_id"] and record.get("run_id") == run["run_id"] and record.get("artifact_id") == current_artifact["artifact_id"] and record.get("artifact_sha256") == current_artifact["content_sha256"] and record.get("result") == "passed" for record in quality_gate_runs):
            errors.append(("ERR_GATE_REQUIRED", "A current passed human quality-gate run is required before completion."))
    if errors:
        return {"ok": False, "replay": False, "command_fingerprint": command_fingerprint, "run": copy.deepcopy(run), "human_quality_gate_run": None, "release_record": None, "errors": [error(command, run, index + 1, code, message) for index, (code, message) in enumerate(errors)]}
    _, target_status = STATE_RULES[operation]
    next_run = copy.deepcopy(run)
    next_run["status"] = target_status
    if operation in {"submit_for_gate", "post_publication", "approve", "complete", "publish"}:
        next_run["output_hash"] = current_artifact["content_sha256"]
    if operation == "retry":
        next_run["attempt"] = int(run["attempt"]) + 1
    return {"ok": True, "replay": False, "command_fingerprint": command_fingerprint, "run": next_run, "human_quality_gate_run": human_quality_gate_run(command, run, current_artifact, approval, human_gate_defs[0], registry["schema_version"]) if operation == "approve" else None, "release_record": release_record(command, run, current_artifact, approval) if operation in {"complete", "publish"} else None, "errors": []}
