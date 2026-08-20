"""FastAPI composition root for the contained local Operator API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from jsonschema import Draft202012Validator, FormatChecker

from services.operator_routing import load_policy, route_error, validate_policy
from services.quality_gate_registry import load_registry
from services.transition_service import process_transition
from services.transition_service.service import load_workflow_graph

from .event_store import EventStore, EventStoreError
from .models import CommandRequest, CommandResult, DataEnvelope, ErrorEnvelope, JsonValue
from .repository import ProjectRepository, RepositoryError, WorkspaceRegistry


_TRANSITION_VERBS: Final = frozenset({"start", "approve", "resume"})
_EVENT_FOR_VERB: Final = {
    "start": "run.started", "request-revision": "task.created", "request-input": "step.blocked",
    "create-defect": "defect.created", "escalate": "escalation.created", "request-waiver": "task.created",
    "approve": "gate.approved", "reject": "gate.rejected", "resolve": "task.resolved", "resume": "run.resumed",
}
_RECORDS_FOR_VERB: Final = {
    "request-revision": frozenset({"revision-request"}), "request-input": frozenset({"operator-task", "blocker-record"}),
    "create-defect": frozenset({"workflow-defect"}), "escalate": frozenset({"escalation-record"}),
    "request-waiver": frozenset({"operator-task"}), "reject": frozenset({"revision-request", "workflow-defect"}),
    "resolve": frozenset({"resolution-record"}),
}


class ApiError(RuntimeError):
    """Path-free HTTP boundary error."""

    def __init__(self, code: str, status_code: int, message: str, routed: bool = False) -> None:
        self.code = code
        self.status_code = status_code
        self.message = message
        self.routed = routed
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Injected dependency mode for production and isolated tests."""

    repository_root: Path
    allow_unready: bool = False


def create_app(registry: WorkspaceRegistry, repository_root: Path, config: AppConfig | None = None) -> FastAPI:
    """Create the only local HTTP adapter around existing core authorities."""
    effective = config or AppConfig(repository_root)
    repository = ProjectRepository(registry)
    app = FastAPI(title="Heartweb Local Operator API", version="1.0.0")
    app.state.ready = False
    app.state.projection_rebuild_needed = False
    app.state.dependencies: dict[str, JsonValue] = {}

    try:
        app.state.dependencies = _dependencies(effective.repository_root, registry)
        app.state.projection_rebuild_needed = repository.has_any_operator_recoveries()
        app.state.ready = True
    except (OSError, json.JSONDecodeError, RepositoryError, EventStoreError, ValueError) as exc:
        if not effective.allow_unready:
            raise RuntimeError("Operator API dependencies are unavailable.") from exc

    @app.exception_handler(ApiError)
    async def api_error(_: Request, error: ApiError) -> JSONResponse:
        if error.routed:
            route_error(error.code, app.state.dependencies["policy"])
        return JSONResponse(status_code=error.status_code, content=ErrorEnvelope(code=error.code, message=error.message).model_dump())

    @app.exception_handler(RepositoryError)
    async def repository_error(_: Request, error: RepositoryError) -> JSONResponse:
        status = 404 if error.code == "ERR_TENANT_ISOLATION" else 503
        return JSONResponse(status_code=status, content=ErrorEnvelope(code=error.code, message=error.message).model_dump())

    @app.exception_handler(EventStoreError)
    async def event_error(_: Request, error: EventStoreError) -> JSONResponse:
        status = 422 if error.code == "ERROR_CONTEXT_SCHEMA_INVALID" else 409 if error.code in {"ERR_IDEMPOTENCY_CONFLICT", "ERROR_TRANSITION_LEDGER_LOCKED"} else 503
        return JSONResponse(status_code=status, content=ErrorEnvelope(code=error.code, message=error.message).model_dump())

    @app.get("/healthz", response_model=DataEnvelope, operation_id="healthz")
    def healthz() -> DataEnvelope:
        return DataEnvelope(data={"status": "alive"})

    @app.get("/readyz", response_model=DataEnvelope, operation_id="readyz")
    def readyz() -> DataEnvelope:
        if not app.state.ready or app.state.projection_rebuild_needed:
            raise ApiError("ERROR_DOMAIN_CONTRACT_FILE_MISSING", 503, "Operator API is not ready.")
        return DataEnvelope(data={"status": "ready"})

    @app.get("/v1/tenants/{tenant_id}/projects", response_model=DataEnvelope, operation_id="listProjects")
    def list_projects(tenant_id: str) -> DataEnvelope:
        return DataEnvelope(data=repository.list_projects(tenant_id))

    @app.get("/v1/tenants/{tenant_id}/projects/{project_id}", response_model=DataEnvelope, operation_id="getProject")
    def get_project(tenant_id: str, project_id: str) -> DataEnvelope:
        return _envelope(repository.project(tenant_id, project_id))

    @app.get("/v1/tenants/{tenant_id}/projects/{project_id}/logical-session", response_model=DataEnvelope, operation_id="getLogicalSession")
    def logical_session(tenant_id: str, project_id: str) -> DataEnvelope:
        return _envelope(repository.logical_session(tenant_id, project_id))

    @app.get("/v1/tenants/{tenant_id}/projects/{project_id}/workflow", response_model=DataEnvelope, operation_id="getWorkflow")
    def workflow(tenant_id: str, project_id: str) -> DataEnvelope:
        return _envelope(repository.workflow(tenant_id, project_id))

    @app.get("/v1/tenants/{tenant_id}/projects/{project_id}/steps", response_model=DataEnvelope, operation_id="listSteps")
    def steps(tenant_id: str, project_id: str) -> DataEnvelope:
        return _envelope(repository.collection(tenant_id, project_id, "steps"))

    @app.get("/v1/tenants/{tenant_id}/projects/{project_id}/steps/{step_id}", response_model=DataEnvelope, operation_id="getStep")
    def step(tenant_id: str, project_id: str, step_id: str) -> DataEnvelope:
        records = repository.collection(tenant_id, project_id, "steps")
        record = next((item for item in records if item.get("step_id") == step_id), None)
        if record is None:
            raise ApiError("ERROR_DOMAIN_REFERENCE_UNKNOWN", 404, "Requested projection is unavailable.")
        return _envelope(record)

    for collection, suffix, operation in (
        ("artifacts", "artifacts", "listArtifacts"), ("gates", "gates", "listGates"), ("tasks", "tasks", "listTasks"),
        ("tickets", "tickets", "listTickets"), ("assignments", "assignments", "listAssignments"),
        ("context-packages", "context-packages", "listContextPackages"), ("performance-checkpoints", "performance-checkpoints", "listPerformanceCheckpoints"),
        ("metrics", "metrics", "listMetrics"), ("adjustment-proposals", "adjustment-proposals", "listAdjustmentProposals"),
        ("integrations-status", "integrations/status", "getIntegrationStatus"),
    ):
        app.add_api_route(
            f"/v1/tenants/{{tenant_id}}/projects/{{project_id}}/{suffix}",
            _collection_handler(repository, collection), methods=["GET"], response_model=DataEnvelope, operation_id=operation,
        )

    @app.get("/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}", response_model=DataEnvelope, operation_id="getRun")
    def run(tenant_id: str, project_id: str, run_id: str) -> DataEnvelope:
        return _envelope(repository.run(tenant_id, project_id, run_id))

    @app.get("/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}/history", response_model=DataEnvelope, operation_id="getRunHistory")
    def run_history(tenant_id: str, project_id: str, run_id: str) -> DataEnvelope:
        return _envelope(repository.run_history(tenant_id, project_id, run_id))

    @app.post("/v1/tenants/{tenant_id}/projects/{project_id}/commands/{verb}", response_model=CommandResult, operation_id="submitOperatorCommand")
    def command(tenant_id: str, project_id: str, verb: str, body: CommandRequest) -> CommandResult:
        if not app.state.ready:
            raise ApiError("ERROR_DOMAIN_CONTRACT_FILE_MISSING", 503, "Operator API is not ready.")
        _assert_command_identity(tenant_id, project_id, verb, body)
        store = EventStore(registry.resolve(tenant_id, project_id), app.state.dependencies["event_schema"])
        if verb in _TRANSITION_VERBS:
            replay = _replay(store, body.event)
            if replay is not None:
                return CommandResult(command_id=body.command_id, correlation_id=body.correlation_id, replay=True, event=replay)
            return _transition(repository, store, app, tenant_id, project_id, body)
        return _operator_record(repository, store, app, app.state.dependencies["record_schemas"], tenant_id, project_id, body)

    return app


def _envelope(value: JsonValue) -> DataEnvelope:
    return DataEnvelope(data=value)


def _collection_handler(repository: ProjectRepository, collection: str):
    def handler(tenant_id: str, project_id: str) -> DataEnvelope:
        return _envelope(repository.collection(tenant_id, project_id, collection))
    return handler


def _dependencies(root: Path, registry: WorkspaceRegistry) -> dict[str, JsonValue]:
    schemas: dict[str, JsonValue] = {}
    for folder in ("runtime", "operator", "integrations", "workflow"):
        for path in (root / "standards" / folder).glob("*.schema.json"):
            schema = _json(path)
            Draft202012Validator.check_schema(schema)
            schemas[path.stem] = schema
    graph = load_workflow_graph(root)
    graph_schema = _json(root / "standards/workflow/workflow-graph.schema.json")
    Draft202012Validator(graph_schema, format_checker=FormatChecker()).validate(graph)
    policy = load_policy(root)
    if not validate_policy(policy).valid:
        raise ValueError("routing policy is incomplete")
    catalog = _json(root / "standards/integrations/event-catalog-v2.json")
    event_schema = _json(root / "standards/integrations/workflow-event-v2.schema.json")
    if set(catalog["events"]) != set(event_schema["properties"]["event_type"]["enum"]):
        raise ValueError("event catalog is incomplete")
    for registration in registry._registrations:
        EventStore(registration.workspace, event_schema).validate_history()
    return {"policy": policy, "graph": graph, "gate_registry": load_registry(root), "event_schema": event_schema, "record_schemas": schemas}


def _json(path: Path) -> dict[str, JsonValue]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("schema is not an object")
    return value


def _assert_command_identity(tenant_id: str, project_id: str, verb: str, body: CommandRequest) -> None:
    if verb not in _EVENT_FOR_VERB:
        raise ApiError("ERR_TRANSITION_NOT_ALLOWED", 409, "Command verb is not allowed.", True)
    if body.command != verb or body.tenant_id != tenant_id or body.project_id != project_id:
        raise ApiError("ERR_TENANT_ISOLATION", 409, "Route and command identity do not match.", True)
    event_identity = body.event.get("identity")
    if not isinstance(event_identity, dict):
        raise ApiError("ERR_TENANT_ISOLATION", 409, "Event identity is invalid.", True)
    expected = {
        "tenant_id": body.tenant_id, "project_id": body.project_id, "run_id": body.run_id,
        "step_id": body.step_id, "revision": body.expected_revision,
    }
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


def _transition(
    repository: ProjectRepository,
    store: EventStore,
    app: FastAPI,
    tenant_id: str,
    project_id: str,
    body: CommandRequest,
) -> CommandResult:
    transition = body.transition_command
    if transition is None:
        raise ApiError("ERROR_CONTEXT_SCHEMA_INVALID", 422, "Transition command is required.")
    errors = list(Draft202012Validator(app.state.dependencies["record_schemas"]["transition-command.schema"], format_checker=FormatChecker()).iter_errors(transition))
    if errors:
        raise ApiError("ERROR_CONTEXT_SCHEMA_INVALID", 422, "Transition command does not satisfy its contract.")
    _assert_transition_envelope(body, transition)
    run = repository.run(tenant_id, project_id, body.run_id)
    artifacts = repository.collection(tenant_id, project_id, "artifacts")
    current = next((item for item in artifacts if item.get("run_id") == body.run_id and item.get("step_id") == body.step_id), None)
    gates = repository.collection(tenant_id, project_id, "gates")
    approval = next((item for item in gates if item.get("decision") == "approved"), None)
    result = process_transition(
        command=transition, run=run, current_artifact=current, supporting_artifacts=artifacts,
        quality_gate_runs=gates, approval=approval, predecessor_release=transition.get("predecessor_release"),
        context=run.get("gate_context", {}), registry=app.state.dependencies["gate_registry"], graph=app.state.dependencies["graph"],
    )
    if not result["ok"]:
        error = result["errors"][0]
        route_error(error["code"], app.state.dependencies["policy"])
        raise ApiError(error["code"], 409, error["message"], True)
    appended = store.append(body.event)
    if appended.replay:
        return CommandResult(command_id=body.command_id, correlation_id=body.correlation_id, replay=True, event=appended.event)
    try:
        repository.write_run(tenant_id, project_id, result["run"])
        release = result["release_record"]
        if release is not None:
            repository.write_release(tenant_id, project_id, release)
    except RepositoryError:
        app.state.projection_rebuild_needed = True
        raise
    return CommandResult(command_id=body.command_id, correlation_id=body.correlation_id, replay=False, event=appended.event, run=result["run"])


def _operator_record(
    repository: ProjectRepository,
    store: EventStore,
    app: FastAPI,
    schemas: dict[str, JsonValue],
    tenant_id: str,
    project_id: str,
    body: CommandRequest,
) -> CommandResult:
    record = body.operator_record
    record_type = body.record_type
    if record is None or record_type is None or record_type not in _RECORDS_FOR_VERB[body.command]:
        raise ApiError("ERROR_CONTEXT_SCHEMA_INVALID", 422, "Typed operator record is not allowed for this command.")
    schema = schemas.get(f"{record_type}.schema")
    if not isinstance(schema, dict) or list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record)):
        raise ApiError("ERROR_CONTEXT_SCHEMA_INVALID", 422, "Operator record does not satisfy its contract.")
    run_field = repository.operator_record_run_field(record_type)
    expected = {"tenant_id": tenant_id, "project_id": project_id, run_field: body.run_id, "step_id": body.step_id}
    if any(record.get(key) != value for key, value in expected.items()):
        raise ApiError("ERR_TENANT_ISOLATION", 409, "Operator record identity does not match command.", True)
    record_id = repository.operator_record_id(record_type, record)
    recovery = repository.operator_recovery(tenant_id, project_id, record_type, record_id)
    replay = _replay(store, body.event)
    if recovery is not None:
        _assert_recovery_matches(recovery, body, record_type, record_id, record, schemas)
        if replay is None:
            app.state.projection_rebuild_needed = True
            raise ApiError("ERROR_CONTEXT_SOURCE_INVALID", 503, "Operator record recovery is unavailable.")
        return _repair_operator_record(repository, app, tenant_id, project_id, record_type, record_id, body, replay)
    if replay is not None:
        return CommandResult(command_id=body.command_id, correlation_id=body.correlation_id, replay=True, event=replay)
    repository.write_operator_recovery(tenant_id, project_id, record_type, body.command_id, record)
    try:
        appended = store.append(body.event)
    except EventStoreError:
        repository.remove_operator_recovery(tenant_id, project_id, record_type, record_id)
        raise
    return _repair_operator_record(repository, app, tenant_id, project_id, record_type, record_id, body, appended.event, appended.replay)


def _assert_transition_envelope(body: CommandRequest, transition: dict[str, JsonValue]) -> None:
    expected = {
        "command_id": body.command_id, "tenant_id": body.tenant_id, "project_id": body.project_id,
        "run_id": body.run_id, "expected_revision": body.expected_revision, "idempotency_key": body.idempotency_key,
    }
    if any(transition.get(key) != value for key, value in expected.items()):
        raise ApiError("ERR_TENANT_ISOLATION", 409, "Transition command identity does not match the command envelope.", True)
    nested_step = transition.get("step_id")
    if nested_step is not None and nested_step != body.step_id:
        raise ApiError("ERR_TENANT_ISOLATION", 409, "Transition step identity does not match the command envelope.", True)
    expected_operation = {"start": "start", "approve": "approve", "resume": "retry"}[body.command]
    if transition.get("operation") != expected_operation:
        raise ApiError("ERR_TRANSITION_NOT_ALLOWED", 409, "Transition operation does not match command verb.", True)


def _assert_recovery_matches(
    recovery: dict[str, JsonValue], body: CommandRequest, record_type: str, record_id: str,
    record: dict[str, JsonValue], schemas: dict[str, JsonValue],
) -> None:
    stored_record = recovery.get("record")
    schema = schemas.get(f"{record_type}.schema")
    if (
        recovery.get("record_type") != record_type or recovery.get("record_id") != record_id
        or recovery.get("command_id") != body.command_id or not isinstance(stored_record, dict)
        or not isinstance(schema, dict) or list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(stored_record))
        or json.dumps(stored_record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        != json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    ):
        raise ApiError("ERR_IDEMPOTENCY_CONFLICT", 409, "Recovery record conflicts with the command.", True)


def _repair_operator_record(
    repository: ProjectRepository, app: FastAPI, tenant_id: str, project_id: str, record_type: str,
    record_id: str, body: CommandRequest, event: dict[str, JsonValue], replay: bool = True,
) -> CommandResult:
    try:
        repository.finalize_operator_recovery(tenant_id, project_id, record_type, record_id)
        app.state.projection_rebuild_needed = repository.has_any_operator_recoveries()
    except RepositoryError as error:
        app.state.projection_rebuild_needed = True
        raise ApiError(error.code, 503, "Operator record projection is temporarily unavailable.", True) from error
    return CommandResult(command_id=body.command_id, correlation_id=body.correlation_id, replay=replay, event=event)
