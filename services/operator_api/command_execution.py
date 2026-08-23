"""Command validation, event execution, and projection recovery."""

from __future__ import annotations

import json
from typing import Final

from fastapi import FastAPI
from jsonschema import Draft202012Validator, FormatChecker

from services.operator_routing import route_error
from services.transition_service import process_transition

from .app_errors import ApiError
from .event_store import EventStore, EventStoreError
from .models import CommandRequest, CommandResult, JsonValue
from .repository import ProjectRepository, RepositoryError, WorkspaceRegistry
from .transition_recovery import TransitionRecovery

_TRANSITION_VERBS: Final = frozenset({"start", "submit-for-gate", "approve", "complete", "resume"})
_EVENT_FOR_VERB: Final = {
    "start": "run.started", "request-revision": "task.created", "request-input": "step.blocked",
    "create-defect": "defect.created", "escalate": "escalation.created", "request-waiver": "task.created",
    "submit-for-gate": "gate.ready", "approve": "gate.approved", "complete": "release.created", "reject": "gate.rejected", "resolve": "task.resolved", "resume": "run.resumed",
}
_RECORDS_FOR_VERB: Final = {
    "request-revision": frozenset({"revision-request"}), "request-input": frozenset({"operator-task", "blocker-record"}),
    "create-defect": frozenset({"workflow-defect"}), "escalate": frozenset({"escalation-record"}),
    "request-waiver": frozenset({"operator-task"}), "reject": frozenset({"revision-request", "workflow-defect"}),
    "resolve": frozenset({"resolution-record"}),
}


def register_command_route(app: FastAPI, repository: ProjectRepository, registry: WorkspaceRegistry) -> None:
    """Register the sole deprecated raw-command endpoint."""

    @app.post("/v1/tenants/{tenant_id}/projects/{project_id}/commands/{verb}", response_model=CommandResult, operation_id="submitOperatorCommand", deprecated=True)
    def command(tenant_id: str, project_id: str, verb: str, body: CommandRequest) -> CommandResult:
        if not app.state.ready:
            raise ApiError("ERROR_DOMAIN_CONTRACT_FILE_MISSING", 503, "Operator API is not ready.")
        _assert_command_identity(tenant_id, project_id, verb, body)
        store = EventStore(registry.resolve(tenant_id, project_id), app.state.dependencies["event_schema"])
        if verb in _TRANSITION_VERBS:
            return _transition(repository, store, app, tenant_id, project_id, body)
        return _operator_record(repository, store, app, app.state.dependencies["record_schemas"], tenant_id, project_id, body)


def _assert_command_identity(tenant_id: str, project_id: str, verb: str, body: CommandRequest) -> None:
    if verb not in _EVENT_FOR_VERB:
        raise ApiError("ERR_TRANSITION_NOT_ALLOWED", 409, "Command verb is not allowed.", True)
    if body.command != verb or body.tenant_id != tenant_id or body.project_id != project_id:
        raise ApiError("ERR_TENANT_ISOLATION", 409, "Route and command identity do not match.", True)
    event_identity = body.event.get("identity")
    if not isinstance(event_identity, dict):
        raise ApiError("ERR_TENANT_ISOLATION", 409, "Event identity is invalid.", True)
    expected = {"tenant_id": body.tenant_id, "project_id": body.project_id, "run_id": body.run_id, "step_id": body.step_id, "revision": body.expected_revision}
    if any(event_identity.get(key) != value for key, value in expected.items()):
        raise ApiError("ERR_TENANT_ISOLATION", 409, "Event and command identity do not match.", True)
    if body.event.get("correlation_id") != body.correlation_id or body.event.get("idempotency_key") != body.idempotency_key:
        raise ApiError("ERR_IDEMPOTENCY_CONFLICT", 409, "Event idempotency identity does not match the command.", True)
    if body.event.get("event_type") != _EVENT_FOR_VERB[verb]:
        raise ApiError("ERR_TRANSITION_NOT_ALLOWED", 409, "Event type is not allowed for this command.", True)


def _replay(store: EventStore, event: dict[str, JsonValue]) -> dict[str, JsonValue] | None:
    encoded = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    key = event["idempotency_key"]
    for existing in store.history():
        if existing["idempotency_key"] == key:
            known = json.dumps(existing, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
            if known == encoded:
                return existing
            raise ApiError("ERR_IDEMPOTENCY_CONFLICT", 409, "Idempotency key was already used for a different command.", True)
    return None


def _transition(repository: ProjectRepository, store: EventStore, app: FastAPI, tenant_id: str, project_id: str, body: CommandRequest, approval_override: dict[str, JsonValue] | None = None) -> CommandResult:
    transition = body.transition_command
    if transition is None:
        raise ApiError("ERROR_CONTEXT_SCHEMA_INVALID", 422, "Transition command is required.")
    errors = list(Draft202012Validator(app.state.dependencies["record_schemas"]["transition-command.schema"], format_checker=FormatChecker()).iter_errors(transition))
    if errors:
        raise ApiError("ERROR_CONTEXT_SCHEMA_INVALID", 422, "Transition command does not satisfy its contract.")
    _assert_transition_envelope(body, transition)
    recovery = TransitionRecovery(repository)
    pending = recovery.load(tenant_id, project_id, body.command_id)
    replay = _replay(store, body.event)
    if pending is not None and (pending.get("event") != body.event or replay is None):
        raise ApiError("ERR_IDEMPOTENCY_CONFLICT", 409, "Transition recovery conflicts with the command.", True)
    replay_identity = None
    if pending is not None:
        from .recovery_inventory import RecoveryReplayIdentity
        replay_identity = RecoveryReplayIdentity(tenant_id, project_id, "transition-recovery", f"transition-recovery/{body.command_id}.json")
    try:
        app.state.recovery_inventory.authorize(replay_identity)
    except RepositoryError as error:
        raise ApiError(error.code, 503, error.message, True) from error
    if pending is not None:
        return _finalize_transition_recovery(repository, recovery, app, tenant_id, project_id, body, replay)
    if replay is not None:
        return CommandResult(command_id=body.command_id, correlation_id=body.correlation_id, replay=True, event=replay, readback_url=_run_url(tenant_id, project_id, body.run_id))
    run = repository.run(tenant_id, project_id, body.run_id)
    artifacts = repository.artifacts(tenant_id, project_id)
    current = next((item for item in artifacts if item.get("tenant_id") == tenant_id and item.get("project_id") == project_id and item.get("run_id") == body.run_id and item.get("step_id") == body.step_id and item.get("revision") == run.get("revision") and item.get("input_hash", run.get("input_hash")) == run.get("input_hash")), None)
    gates = repository.quality_gate_runs(tenant_id, project_id)
    approval = approval_override or next((item for item in repository.collection(tenant_id, project_id, "approvals") if item.get("tenant_id") == tenant_id and item.get("run_id") == body.run_id and item.get("gate_id") == run.get("gate_id") and item.get("decision") == "approved"), None)
    predecessor = repository.released_predecessor(tenant_id, project_id, transition["from_step_id"]) if body.step_id != "0" else None
    result = process_transition(command=transition, run=run, current_artifact=current, supporting_artifacts=artifacts, quality_gate_runs=gates, approval=approval, predecessor_release=predecessor, context=run.get("gate_context", {}), registry=app.state.dependencies["gate_registry"], graph=app.state.dependencies["graph"])
    if not result["ok"]:
        error = result["errors"][0]
        route_error(error["code"], app.state.dependencies["policy"])
        raise ApiError(error["code"], 409, error["message"], True)
    recovery.stage(tenant_id, project_id, body.command_id, body.event, result, approval if body.command == "approve" else None)
    try:
        appended = store.append(body.event)
    except EventStoreError:
        repository._remove(tenant_id, project_id, f"transition-recovery/{body.command_id}.json")
        raise
    return _finalize_transition_recovery(repository, recovery, app, tenant_id, project_id, body, appended.event, appended.replay)


def _finalize_transition_recovery(repository: ProjectRepository, recovery: TransitionRecovery, app: FastAPI, tenant_id: str, project_id: str, body: CommandRequest, event: dict[str, JsonValue], replay: bool = True) -> CommandResult:
    try:
        repaired = recovery.finalize(tenant_id, project_id, body.command_id)
        app.state.projection_rebuild_needed = repository.has_any_operator_recoveries() or recovery.pending(tenant_id, project_id)
    except RepositoryError as error:
        app.state.projection_rebuild_needed = True
        raise ApiError(error.code, 503, "Transition projection is temporarily unavailable.", True) from error
    return CommandResult(command_id=body.command_id, correlation_id=body.correlation_id, replay=replay, event=event, run=repaired["run"], readback_url=_run_url(tenant_id, project_id, body.run_id))


def _operator_record(repository: ProjectRepository, store: EventStore, app: FastAPI, schemas: dict[str, JsonValue], tenant_id: str, project_id: str, body: CommandRequest) -> CommandResult:
    record = body.operator_record
    record_type = body.record_type
    if record is None or record_type is None or record_type not in _RECORDS_FOR_VERB[body.command]:
        raise ApiError("ERROR_CONTEXT_SCHEMA_INVALID", 422, "Typed operator record is not allowed for this command.")
    schema = schemas.get(f"{record_type}.schema")
    if not isinstance(schema, dict) or list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record)):
        raise ApiError("ERROR_CONTEXT_SCHEMA_INVALID", 422, "Operator record does not satisfy its contract.")
    run_field = repository.operator_record_run_field(record_type)
    if any(record.get(key) != value for key, value in {"tenant_id": tenant_id, "project_id": project_id, run_field: body.run_id, "step_id": body.step_id}.items()):
        raise ApiError("ERR_TENANT_ISOLATION", 409, "Operator record identity does not match command.", True)
    record_id = repository.operator_record_id(record_type, record)
    recovery = repository.operator_recovery(tenant_id, project_id, record_type, record_id)
    replay = _replay(store, body.event)
    if recovery is not None:
        _assert_recovery_matches(recovery, body, record_type, record_id, record, schemas)
        if replay is None:
            app.state.projection_rebuild_needed = True
            raise ApiError("ERROR_CONTEXT_SOURCE_INVALID", 503, "Operator record recovery is unavailable.")
    replay_identity = None
    if recovery is not None:
        from .recovery_inventory import RecoveryReplayIdentity
        replay_identity = RecoveryReplayIdentity(tenant_id, project_id, "projection-recovery", f"projection-recovery/{record_type}--{record_id}.json")
    try:
        app.state.recovery_inventory.authorize(replay_identity)
    except RepositoryError as error:
        raise ApiError(error.code, 503, error.message, True) from error
    if recovery is not None:
        return _repair_operator_record(repository, app, tenant_id, project_id, record_type, record_id, body, replay)
    if replay is not None:
        return CommandResult(command_id=body.command_id, correlation_id=body.correlation_id, replay=True, event=replay, readback_url=_record_url(tenant_id, project_id, record_type, record_id))
    repository.write_operator_recovery(tenant_id, project_id, record_type, body.command_id, record)
    try:
        appended = store.append(body.event)
    except EventStoreError:
        repository.remove_operator_recovery(tenant_id, project_id, record_type, record_id)
        raise
    return _repair_operator_record(repository, app, tenant_id, project_id, record_type, record_id, body, appended.event, appended.replay)


def _assert_transition_envelope(body: CommandRequest, transition: dict[str, JsonValue]) -> None:
    expected = {"command_id": body.command_id, "tenant_id": body.tenant_id, "project_id": body.project_id, "run_id": body.run_id, "expected_revision": body.expected_revision, "idempotency_key": body.idempotency_key}
    if any(transition.get(key) != value for key, value in expected.items()):
        raise ApiError("ERR_TENANT_ISOLATION", 409, "Transition command identity does not match the command envelope.", True)
    nested_step = transition.get("step_id")
    if nested_step is not None and nested_step != body.step_id:
        raise ApiError("ERR_TENANT_ISOLATION", 409, "Transition step identity does not match the command envelope.", True)
    expected_operation = {"start": "start", "submit-for-gate": "submit_for_gate", "approve": "approve", "complete": "complete", "resume": "retry"}[body.command]
    if transition.get("operation") != expected_operation:
        raise ApiError("ERR_TRANSITION_NOT_ALLOWED", 409, "Transition operation does not match command verb.", True)


def _assert_recovery_matches(recovery: dict[str, JsonValue], body: CommandRequest, record_type: str, record_id: str, record: dict[str, JsonValue], schemas: dict[str, JsonValue]) -> None:
    stored_record = recovery.get("record")
    schema = schemas.get(f"{record_type}.schema")
    if (recovery.get("record_type") != record_type or recovery.get("record_id") != record_id or recovery.get("command_id") != body.command_id or not isinstance(stored_record, dict) or not isinstance(schema, dict) or list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(stored_record)) or json.dumps(stored_record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) != json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)):
        raise ApiError("ERR_IDEMPOTENCY_CONFLICT", 409, "Recovery record conflicts with the command.", True)


def _repair_operator_record(repository: ProjectRepository, app: FastAPI, tenant_id: str, project_id: str, record_type: str, record_id: str, body: CommandRequest, event: dict[str, JsonValue], replay: bool = True) -> CommandResult:
    try:
        repository.finalize_operator_recovery(tenant_id, project_id, record_type, record_id)
        app.state.projection_rebuild_needed = repository.has_any_operator_recoveries()
    except RepositoryError as error:
        app.state.projection_rebuild_needed = True
        raise ApiError(error.code, 503, "Operator record projection is temporarily unavailable.", True) from error
    return CommandResult(command_id=body.command_id, correlation_id=body.correlation_id, replay=replay, event=event, readback_url=_record_url(tenant_id, project_id, record_type, record_id))


def _run_url(tenant_id: str, project_id: str, run_id: str) -> str:
    return f"/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}"


def _record_url(tenant_id: str, project_id: str, record_type: str, record_id: str) -> str:
    return f"/v1/tenants/{tenant_id}/projects/{project_id}/operator-records/{record_type}/{record_id}"
