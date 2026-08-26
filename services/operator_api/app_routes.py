"""Read-only Operator API route registration."""

from __future__ import annotations

from fastapi import FastAPI

from .app_errors import ApiError
from .models import CurrentRunResponse, DataEnvelope, JsonValue
from .repository import ProjectRepository


def register_read_routes(app: FastAPI, repository: ProjectRepository) -> None:
    """Register stable read projections in their documented OpenAPI order."""

    @app.get("/healthz", response_model=DataEnvelope, operation_id="healthz")
    def healthz() -> DataEnvelope:
        return DataEnvelope(data={"status": "alive"})

    @app.get("/readyz", response_model=DataEnvelope, operation_id="readyz")
    def readyz() -> DataEnvelope:
        if not app.state.ready or app.state.recovery_inventory.blocked():
            raise ApiError("ERROR_DOMAIN_CONTRACT_FILE_MISSING", 503, "Operator API is not ready.")
        data: dict[str, JsonValue] = {"status": "ready"}
        service = getattr(app.state, "operator_service", None)
        fingerprint = getattr(app.state, "operator_runtime_fingerprint", None)
        process_id = getattr(app.state, "operator_process_id", None)
        if isinstance(service, str) and isinstance(fingerprint, str) and isinstance(process_id, int) and not isinstance(process_id, bool):
            data.update({"service": service, "runtime_fingerprint": fingerprint, "process_id": process_id})
        return DataEnvelope(data=data)

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
        record = next((item for item in repository.collection(tenant_id, project_id, "steps") if item.get("step_id") == step_id), None)
        if record is None:
            raise ApiError("ERROR_DOMAIN_REFERENCE_UNKNOWN", 404, "Requested projection is unavailable.")
        return _envelope(record)

    for collection, suffix, operation in (
        ("artifacts", "artifacts", "listArtifacts"), ("gates", "gates", "listGates"), ("tasks", "tasks", "listTasks"),
        ("tickets", "tickets", "listTickets"), ("assignments", "assignments", "listAssignments"),
        ("context-packages", "context-packages", "listContextPackages"), ("performance-checkpoints", "performance-checkpoints", "listPerformanceCheckpoints"),
        ("metrics", "metrics", "listMetrics"), ("adjustment-proposals", "adjustment-proposals", "listAdjustmentProposals"),
        ("integrations-status", "integrations/status", "getIntegrationStatus"), ("approvals", "approvals", "listApprovals"),
    ):
        app.add_api_route(
            f"/v1/tenants/{{tenant_id}}/projects/{{project_id}}/{suffix}",
            _collection_handler(repository, collection), methods=["GET"], response_model=DataEnvelope, operation_id=operation,
        )

    @app.get("/v1/tenants/{tenant_id}/projects/{project_id}/releases", response_model=DataEnvelope, operation_id="listReleases")
    def releases(tenant_id: str, project_id: str) -> DataEnvelope:
        return _envelope(repository.releases(tenant_id, project_id))

    @app.get("/v1/tenants/{tenant_id}/projects/{project_id}/runs/current", response_model=CurrentRunResponse, operation_id="getCurrentRun")
    def current_run(tenant_id: str, project_id: str) -> CurrentRunResponse:
        return repository.current_run(tenant_id, project_id)

    @app.get("/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}", response_model=DataEnvelope, operation_id="getRun")
    def run(tenant_id: str, project_id: str, run_id: str) -> DataEnvelope:
        return _envelope(repository.run(tenant_id, project_id, run_id))

    @app.get("/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}/history", response_model=DataEnvelope, operation_id="getRunHistory")
    def run_history(tenant_id: str, project_id: str, run_id: str) -> DataEnvelope:
        return _envelope(repository.run_history(tenant_id, project_id, run_id))


def _envelope(value: JsonValue) -> DataEnvelope:
    return DataEnvelope(data=value)


def _collection_handler(repository: ProjectRepository, collection: str):
    def handler(tenant_id: str, project_id: str) -> DataEnvelope:
        if collection == "artifacts":
            return _envelope(repository.artifacts(tenant_id, project_id))
        if collection == "gates":
            return _envelope(repository.quality_gate_runs(tenant_id, project_id))
        return _envelope(repository.collection(tenant_id, project_id, collection))
    return handler
