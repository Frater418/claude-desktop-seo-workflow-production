"""Server-derived public action preview and confirmation authority."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Final

from jsonschema import Draft202012Validator, FormatChecker

from services.transition_service import process_transition

from .app_errors import ApiError
from .command_execution import _operator_record, _transition
from .event_store import EventStore
from .next_runs import NextRunError, NextRunService
from .package4 import Package4Error
from .models import (
    ActionBlocker,
    ActionConfirmRequest,
    ActionConfirmResult,
    ActionIntent,
    ActionPreview,
    CommandRequest,
    JsonValue,
)

if TYPE_CHECKING:
    from fastapi import FastAPI

    from .repository import ProjectRepository, WorkspaceRegistry


_TRANSITIONS: Final = frozenset({"start", "submit-for-gate", "approve", "complete"})
_EVENTS: Final = {
    "start": "run.started", "submit-for-gate": "gate.ready", "approve": "gate.approved",
    "complete": "release.created", "reject": "gate.rejected", "request-revision": "task.created",
    "request-input": "step.blocked", "escalate": "escalation.created", "request-waiver": "task.created",
    "resolve": "task.resolved",
}
_REMEDIATION: Final = {
    "ERR_STALE_REVISION": "Refresh the run and preview the action again.",
    "ERR_ARTIFACT_REQUIRED": "Create or validate the current artifact, then preview again.",
    "ERR_GATE_REQUIRED": "Satisfy the required quality gate, then preview again.",
    "ERR_APPROVAL_STALE": "Record a current revision-bound approval, then preview again.",
    "ERR_TRANSITION_NOT_ALLOWED": "Choose an action allowed by the canonical run status.",
    "ERROR_CONTEXT_SCHEMA_INVALID": "Provide the required typed operator action details.",
}


@dataclass(frozen=True, slots=True)
class ActionPreviewBinding:
    intent: ActionIntent
    effective_intent: ActionIntent
    occurred_at: str


def preview_action(repository: ProjectRepository, app: FastAPI, intent: ActionIntent) -> ActionPreview:
    """Evaluate the action against current canonical projections without persisting it."""
    try:
        effective_intent, state = _start_state(repository, app, intent, False)
    except NextRunError as error:
        return ActionPreview(intent=intent, allowed=False, blockers=(_blocker(error.code, error.message),), consequence={}, preview_hash=_hash(intent.model_dump(mode="json")))
    requested_at = app.state.clock.now()
    state["operator_id"] = app.state.operator_id
    fingerprint = _preview_hash(effective_intent, state, app.state.dependencies["gate_registry"], requested_at, app.state.operator_id)
    command = _command(effective_intent, fingerprint, "idem-preview-" + fingerprint[:16], requested_at, state)
    if effective_intent.action in _TRANSITIONS:
        approval = _approval(effective_intent, state, requested_at, fingerprint) if effective_intent.action == "approve" and isinstance(state["current_artifact"], dict) else state["approval"]
        if isinstance(approval, dict) and isinstance(command["transition_command"], dict):
            command["transition_command"]["approval"] = _transition_approval(approval)
        result = _transition_preview(app, command, state, approval)
        blockers = tuple(_blocker(item["code"], item["message"]) for item in result["errors"])
        consequence = {"run": result["run"], "human_quality_gate_run": result["human_quality_gate_run"], "release_record": result["release_record"]}
    else:
        record = _record(effective_intent, state, fingerprint, requested_at)
        schema = app.state.dependencies["record_schemas"].get(f"{_record_type(effective_intent.action)}.schema")
        valid = isinstance(schema, dict) and not list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record))
        run = state["run"]
        stale = isinstance(run, dict) and intent.expected_revision != run.get("revision")
        blockers = ((_blocker("ERR_STALE_REVISION", "Action expected revision does not match the current run revision."),) if stale else ()) + (() if valid else (_blocker("ERROR_CONTEXT_SCHEMA_INVALID", "Derived operator record does not satisfy its contract."),))
        consequence = {"record_type": _record_type(effective_intent.action), "record": record}
    app.state.action_previews[fingerprint] = ActionPreviewBinding(intent, effective_intent, requested_at)
    return ActionPreview(intent=effective_intent, allowed=not blockers, blockers=blockers, consequence=consequence, preview_hash=fingerprint)


def confirm_action(repository: ProjectRepository, registry: WorkspaceRegistry, app: FastAPI, request: ActionConfirmRequest) -> ActionConfirmResult:
    """Recompute current state, then execute the established lifecycle or record path."""
    store = EventStore(registry.resolve(request.intent.tenant_id, request.intent.project_id), app.state.dependencies["event_schema"])
    existing = next((event for event in store.history() if event["idempotency_key"] == request.idempotency_key), None)
    binding = app.state.action_previews.get(request.preview_hash)
    if existing is None and (not isinstance(binding, ActionPreviewBinding) or binding.intent != request.intent):
        raise ApiError("ERR_STALE_REVISION", 409, "Action preview is unavailable or does not match the requested action.", True)
    occurred_at = existing["occurred_at"] if existing is not None else binding.occurred_at
    try:
        effective_intent, state = _start_state(repository, app, request.intent, True)
    except NextRunError as error:
        raise ApiError(error.code, 409, error.message, True) from error
    state["operator_id"] = app.state.operator_id
    fingerprint = _preview_hash(effective_intent, state, app.state.dependencies["gate_registry"], occurred_at, app.state.operator_id)
    replay_candidate = _action_fingerprint(request.intent, request.preview_hash)
    if existing is None and request.preview_hash != fingerprint:
        raise ApiError("ERR_STALE_REVISION", 409, "Action preview no longer matches canonical state.", True)
    command = _command(effective_intent, replay_candidate, request.idempotency_key, occurred_at, state)
    if effective_intent.action not in _TRANSITIONS:
        command["operator_record"] = _record(effective_intent, state, replay_candidate, occurred_at)
    if effective_intent.action in _TRANSITIONS:
        approval = _approval(effective_intent, state, occurred_at, replay_candidate) if effective_intent.action == "approve" else state["approval"]
        if isinstance(approval, dict) and isinstance(command["transition_command"], dict):
            command["transition_command"]["approval"] = _transition_approval(approval)
        result = _transition(repository, store, app, effective_intent.tenant_id, effective_intent.project_id, CommandRequest(**command), approval)
    else:
        result = _operator_record(repository, store, app, app.state.dependencies["record_schemas"], effective_intent.tenant_id, effective_intent.project_id, CommandRequest(**command))
    canonical = _readback(repository, effective_intent, result.readback_url)
    return ActionConfirmResult(replay=result.replay, preview_hash=request.preview_hash, readback_urls=tuple(canonical["urls"]), canonical=canonical["projections"])


def _state(repository: ProjectRepository, intent: ActionIntent) -> dict[str, JsonValue]:
    run = repository.run(intent.tenant_id, intent.project_id, intent.run_id)
    artifacts = repository.artifacts(intent.tenant_id, intent.project_id)
    matching = [artifact for artifact in artifacts if artifact.get("tenant_id") == intent.tenant_id and artifact.get("project_id") == intent.project_id and artifact.get("run_id") == intent.run_id and artifact.get("step_id") == intent.step_id]
    highest = max(matching, key=lambda artifact: (int(artifact.get("revision", 0)), str(artifact.get("artifact_id", "")))) if matching else None
    current = max(
        (artifact for artifact in matching if artifact.get("input_hash", run.get("input_hash")) == run.get("input_hash")),
        key=lambda artifact: int(artifact.get("revision", 0)),
        default=None,
    )
    gates = repository.quality_gate_runs(intent.tenant_id, intent.project_id)
    approvals = repository.collection(intent.tenant_id, intent.project_id, "approvals")
    approval = next((item for item in approvals if item.get("run_id") == intent.run_id and item.get("gate_id") == run.get("gate_id") and item.get("decision") == "approved"), None)
    workflow = repository.workflow(intent.tenant_id, intent.project_id)
    predecessor_step = next((edge.get("from_step_id") for edge in workflow.get("initial_edges", []) if edge.get("to_step_id") == intent.step_id), None)
    predecessor = repository.released_predecessor(intent.tenant_id, intent.project_id, predecessor_step) if isinstance(predecessor_step, str) else None
    resolution_source = _resolution_source(repository, intent) if intent.action == "resolve" else None
    return {"run": run, "artifacts": artifacts, "highest_artifact": highest, "current_artifact": current, "gates": gates, "approval": approval, "predecessor": predecessor, "resolution_source": resolution_source}


def _start_state(repository: ProjectRepository, app: FastAPI, intent: ActionIntent, create: bool) -> tuple[ActionIntent, dict[str, JsonValue]]:
    state = _state(repository, intent)
    run = state["run"]
    if intent.action != "start" or not isinstance(run, dict) or run.get("status") != "completed":
        return intent, state
    service = app.state.next_runs
    if not isinstance(service, NextRunService):
        raise NextRunError("ERROR_CONTEXT_SOURCE_INVALID", "Successor run authority is unavailable.")
    successor = service.create(intent.tenant_id, intent.project_id, intent.run_id) if create else service.derive(intent.tenant_id, intent.project_id, intent.run_id)
    next_intent = intent.model_copy(update={"run_id": successor["run_id"], "step_id": successor["step_id"], "expected_revision": successor["revision"]})
    return next_intent, {**state, "run": successor, "highest_artifact": None, "current_artifact": None, "approval": None, "predecessor": repository.released_predecessor(intent.tenant_id, intent.project_id, intent.step_id)}


def _preview_hash(intent: ActionIntent, state: dict[str, JsonValue], registry: JsonValue, occurred_at: str, operator_id: str) -> str:
    run = state["run"]
    highest = state["highest_artifact"]
    material = {"intent": intent.model_dump(mode="json"), "run": {"revision": run.get("revision"), "status": run.get("status"), "input_hash": run.get("input_hash")}, "artifact": highest, "gates": state["gates"], "resolution_source": state["resolution_source"], "registry_version": registry.get("registry_version") if isinstance(registry, dict) else None, "occurred_at": occurred_at, "operator_id": operator_id}
    return _hash(material)


def _action_fingerprint(intent: ActionIntent, preview_hash: str) -> str:
    return _hash({"intent": intent.model_dump(mode="json"), "preview_hash": preview_hash})


def _command(intent: ActionIntent, fingerprint: str, idempotency_key: str, requested_at: str, state: dict[str, JsonValue]) -> dict[str, JsonValue]:
    suffix = fingerprint[:16]
    command_id = f"command-{suffix}"
    run = state["run"]
    if not isinstance(run, dict):
        raise RuntimeError("Canonical run is malformed.")
    predecessor = state["predecessor"]
    from_step = predecessor["step_id"] if intent.action in {"start", "submit-for-gate"} and isinstance(predecessor, dict) else intent.step_id
    transition = {"command_id": command_id, "tenant_id": intent.tenant_id, "project_id": intent.project_id, "run_id": intent.run_id, "expected_revision": intent.expected_revision, "idempotency_key": idempotency_key, "operation": {"submit-for-gate": "submit_for_gate"}.get(intent.action, intent.action), "from_step_id": from_step, "to_step_id": intent.step_id, "input_hash": run["input_hash"], "requested_at": requested_at}
    artifact = state["current_artifact"]
    if isinstance(artifact, dict):
        transition["output_hash"] = artifact["content_sha256"]
        transition["artifacts"] = [{"artifact_id": artifact["artifact_id"], "revision": artifact["revision"], "content_sha256": artifact["content_sha256"]}]
    event = {"event_id": f"event-{suffix}", "event_type": _EVENTS[intent.action], "schema_version": "2.0.0", "occurred_at": requested_at, "correlation_id": f"corr-{suffix}", "idempotency_key": idempotency_key, "identity": {"tenant_id": intent.tenant_id, "project_id": intent.project_id, "run_id": intent.run_id, "step_id": intent.step_id, "revision": intent.expected_revision}, "integration_mode": "simulated", "simulation_id": f"sim-{suffix}", "payload": _event_payload(intent, fingerprint, run)}
    return {"command": intent.action, "command_id": command_id, "correlation_id": f"corr-{suffix}", "idempotency_key": idempotency_key, "tenant_id": intent.tenant_id, "project_id": intent.project_id, "run_id": intent.run_id, "step_id": intent.step_id, "expected_revision": intent.expected_revision, "transition_command": transition if intent.action in _TRANSITIONS else None, "record_type": None if intent.action in _TRANSITIONS else _record_type(intent.action), "operator_record": None, "event": event}


def _event_payload(intent: ActionIntent, fingerprint: str, run: dict[str, JsonValue]) -> dict[str, JsonValue]:
    suffix = fingerprint[:16]
    match intent.action:
        case "start": return {"attempt": run["attempt"], "input_hash": run["input_hash"]}
        case "submit-for-gate": return {"gate_id": run["gate_id"]}
        case "approve": return {"gate_id": run["gate_id"], "approval_id": f"approval-{suffix}"}
        case "complete": return {"release_id": f"release-{suffix}", "gate_id": run["gate_id"]}
        case "reject": return {"gate_id": run["gate_id"], "reason": intent.payload.reason}
        case "request-input": return {"blocker_id": f"blocker-{suffix}", "reason": intent.payload.reason}
        case "request-revision" | "request-waiver": return {"task_id": f"task-{suffix}", "task_type": "revision_required" if intent.action == "request-revision" else "waiver_candidate"}
        case "escalate": return {"escalation_id": f"escalation-{suffix}", "decision_owner": "business_owner"}
        case "resolve": return {"task_id": intent.payload.source_id, "resolution_id": f"resolution-{suffix}"}
        case unreachable: raise RuntimeError(f"Unsupported action: {unreachable}")


def _transition_preview(app: FastAPI, command: dict[str, JsonValue], state: dict[str, JsonValue], approval: JsonValue) -> dict[str, JsonValue]:
    transition = command["transition_command"]
    run = state["run"]
    if not isinstance(transition, dict) or not isinstance(run, dict):
        raise RuntimeError("Derived transition state is malformed.")
    transition["input_hash"] = run["input_hash"]
    transition["output_hash"] = state["current_artifact"].get("content_sha256") if isinstance(state["current_artifact"], dict) else None
    return process_transition(command=transition, run=run, current_artifact=state["current_artifact"], supporting_artifacts=state["artifacts"], quality_gate_runs=state["gates"], approval=approval if isinstance(approval, dict) else None, predecessor_release=state["predecessor"], context=run.get("gate_context", {}), registry=app.state.dependencies["gate_registry"], graph=app.state.dependencies["graph"])


def _approval(intent: ActionIntent, state: dict[str, JsonValue], decided_at: str, fingerprint: str) -> dict[str, JsonValue]:
    artifact = state["current_artifact"]
    run = state["run"]
    if not isinstance(artifact, dict) or not isinstance(run, dict):
        raise RuntimeError("Canonical approval state is malformed.")
    expiry = (datetime.fromisoformat(decided_at.replace("Z", "+00:00")) + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    return {"approval_id": f"approval-{fingerprint[:16]}", "tenant_id": intent.tenant_id, "run_id": intent.run_id, "gate_id": run["gate_id"], "artifact_id": artifact["artifact_id"], "artifact_sha256": artifact["content_sha256"], "artifact_revision": artifact["revision"], "policy_version": "1.0.0", "reviewer_id": "reviewer-heartweb-admin", "decision": "approved", "decided_at": decided_at, "expires_at": expiry}


def _transition_approval(approval: dict[str, JsonValue]) -> dict[str, JsonValue]:
    names = ("approval_id", "gate_id", "artifact_id", "artifact_sha256", "artifact_revision", "policy_version", "reviewer_id", "decision", "decided_at", "expires_at")
    return {name: approval[name] for name in names}


def _record_type(action: str) -> str:
    return {"request-revision": "revision-request", "reject": "revision-request", "request-input": "blocker-record", "escalate": "escalation-record", "request-waiver": "operator-task", "resolve": "resolution-record"}[action]


def _record(intent: ActionIntent, state: dict[str, JsonValue], fingerprint: str, requested_at: str) -> dict[str, JsonValue]:
    artifact = state["highest_artifact"]
    if not isinstance(artifact, dict):
        return {}
    reference = {"artifact_id": artifact["artifact_id"], "content_sha256": artifact["content_sha256"], "revision": artifact["revision"]}
    evidence = [{"evidence_id": f"evidence-{fingerprint[:16]}", "content_sha256": artifact["content_sha256"]}]
    common = {"tenant_id": intent.tenant_id, "project_id": intent.project_id, "run_id": intent.run_id, "step_id": intent.step_id}
    actor = state["operator_id"]
    if not isinstance(actor, str):
        raise RuntimeError("Canonical action actor is malformed.")
    match intent.action:
        case "request-input": return {**common, "blocker_id": f"blocker-{fingerprint[:16]}", "blocker_type": "input", "title": "Input required", "description": intent.payload.reason, "blocking_scope": "step", "status": "open", "artifact": reference, "evidence": evidence, "reported_by": actor, "reported_at": requested_at}
        case "request-revision" | "reject": return {**common, "revision_request_id": f"revision-{fingerprint[:16]}", "current_artifact_id": artifact["artifact_id"], "current_content_sha256": artifact["content_sha256"], "current_revision": artifact["revision"], "artifact": reference, "affected_sections": list(intent.payload.affected_sections), "problem": intent.payload.reason, "expected_result": intent.payload.instructions, "immutable_constraints": list(intent.payload.immutable_constraints), "evidence": evidence, "reviewer_feedback": intent.payload.reason, "attempt_number": 1, "status": "open", "requested_by": "reviewer-heartweb-admin", "requested_at": requested_at}
        case "escalate": return {**common, "escalation_id": f"escalation-{fingerprint[:16]}", "route": "management_decision", "title": intent.payload.reason, "decision_owner_role": "business_owner", "options": [{"option_id": f"option-{index + 1:03d}", "description": option} for index, option in enumerate(intent.payload.options)], "impacts": list(intent.payload.impacts), "deadline": requested_at, "evidence": evidence, "blocking_scope": "step", "final_decision": None, "status": "open", "created_at": requested_at}
        case "request-waiver": return {**common, "task_id": f"task-{fingerprint[:16]}", "task_type": "waiver_candidate", "title": "Waiver review required", "description": intent.payload.reason, "owner_role": "operator", "priority": "high", "blocking_scope": "step", "artifact": reference, "evidence": evidence, "acceptance_criteria": [intent.payload.instructions], "resolution_method": "request_waiver", "status": "open", "operator_action": {"action": "request_waiver", "requested_by": actor, "requested_at": requested_at, "instructions": intent.payload.instructions}}
        case "resolve": return {**common, "resolution_id": f"resolution-{fingerprint[:16]}", "source_record": {"record_id": intent.payload.source_id, "record_type": intent.payload.source_type}, "artifact": reference, "evidence": evidence, "verification_gate": {"gate_id": state["run"]["gate_id"], "result": "passed"}, "resolver": actor, "resolved_at": requested_at, "action": intent.payload.instructions, "resume_command": {"action": "resume_run", "requested_by": actor, "requested_at": requested_at, "instructions": intent.payload.instructions}, "status": "resolved"}
        case unreachable: raise RuntimeError(f"Unsupported action: {unreachable}")


def _readback(repository: ProjectRepository, intent: ActionIntent, record_url: str) -> dict[str, JsonValue]:
    base = f"/v1/tenants/{intent.tenant_id}/projects/{intent.project_id}"
    urls = [record_url, f"{base}/runs/{intent.run_id}", f"{base}/artifacts", f"{base}/gates", f"{base}/tasks", f"{base}/tickets"]
    projections: dict[str, JsonValue] = {"run": repository.run(intent.tenant_id, intent.project_id, intent.run_id), "artifacts": repository.artifacts(intent.tenant_id, intent.project_id), "gates": repository.quality_gate_runs(intent.tenant_id, intent.project_id), "tasks": repository.collection(intent.tenant_id, intent.project_id, "tasks"), "tickets": repository.collection(intent.tenant_id, intent.project_id, "tickets")}
    if "/operator-records/" in record_url:
        _, record_type, record_id = record_url.rsplit("/", 2)
        projections["record"] = repository.operator_record(intent.tenant_id, intent.project_id, record_type, record_id)
    return {"urls": urls, "projections": projections}


def _blocker(code: str, message: str) -> ActionBlocker:
    return ActionBlocker(code=code, message=message, remediation=_REMEDIATION.get(code, "Correct the canonical action prerequisites and preview again."))


def _resolution_source(repository: ProjectRepository, intent: ActionIntent) -> dict[str, JsonValue]:
    source_type, source_id = intent.payload.source_type, intent.payload.source_id
    if source_type is None or source_id is None:
        raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Resolve requires a canonical source record.")
    record_type = {"operator_task": "operator-task", "blocker": "blocker-record", "revision_request": "revision-request", "workflow_defect": "workflow-defect", "escalation": "escalation-record"}[source_type]
    from .repository import RepositoryError
    try:
        record = repository.operator_record(intent.tenant_id, intent.project_id, record_type, source_id)
    except RepositoryError as error:
        raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Resolve source record is unavailable.") from error
    run_field = repository.operator_record_run_field(record_type)
    if record.get(run_field) != intent.run_id or record.get("step_id") != intent.step_id or record.get("status") != "open":
        raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Resolve source record is not open for this run and step.")
    return {"record_type": source_type, "record_id": source_id, "record_sha256": _hash(record)}


def _hash(value: JsonValue) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()
