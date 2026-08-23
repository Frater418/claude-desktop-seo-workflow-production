"""Write-only local diagnostic trace HTTP adapter."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .app_errors import ApiError
from .diagnostic_trace_api_models import (
    DiagnosticTraceCloseRequest,
    DiagnosticTraceCloseResponse,
    DiagnosticTraceEntryResponse,
    DiagnosticTraceStartResponse,
)
from .diagnostic_trace_models import DiagnosticTrace, DiagnosticTraceOperation, DiagnosticTraceStart
from .diagnostic_trace_store import DiagnosticTraceStore
from .models import ErrorEnvelope
from .repository import ProjectRepository, RepositoryError

_PREFIX = "/v1/tenants/{tenant_id}/projects/{project_id}/diagnostic-traces"
_ERRORS = {404: {"model": ErrorEnvelope}, 409: {"model": ErrorEnvelope}, 422: {"model": ErrorEnvelope}, 503: {"model": ErrorEnvelope}, 507: {"model": ErrorEnvelope}}


def register_diagnostic_trace_routes(app: FastAPI, repository: ProjectRepository, root: Path) -> None:

    @app.post(f"{_PREFIX}", response_model=DiagnosticTraceStartResponse, status_code=201, responses={200: {"model": DiagnosticTraceStartResponse}, **_ERRORS}, operation_id="createDiagnosticTrace")
    def create(tenant_id: str, project_id: str, request: DiagnosticTraceStart) -> JSONResponse:
        _require_start_identity(tenant_id, project_id, request)
        _require_canonical_run(repository, tenant_id, project_id, request.run_id)
        store = _create_store(root)
        stored = store.create(request)
        return _response(DiagnosticTraceStartResponse.from_trace(stored, store.replay), 200 if store.replay else 201)

    @app.post(f"{_PREFIX}/{{trace_id}}/entries", response_model=DiagnosticTraceEntryResponse, status_code=201, responses={200: {"model": DiagnosticTraceEntryResponse}, **_ERRORS}, operation_id="appendDiagnosticTraceEntry")
    def append(tenant_id: str, project_id: str, trace_id: str, request: DiagnosticTraceOperation) -> JSONResponse:
        store = _existing_store(root)
        _require_trace_identity(tenant_id, project_id, store.trace(trace_id))
        recorded = store.append(trace_id, request)
        return _response(DiagnosticTraceEntryResponse.from_operation(trace_id, recorded, store.replay), 200 if store.replay else 201)

    @app.post(f"{_PREFIX}/{{trace_id}}/close", response_model=DiagnosticTraceCloseResponse, status_code=200, responses=_ERRORS, operation_id="closeDiagnosticTrace")
    def close(tenant_id: str, project_id: str, trace_id: str, request: DiagnosticTraceCloseRequest) -> JSONResponse:
        store = _existing_store(root)
        _require_trace_identity(tenant_id, project_id, store.trace(trace_id))
        stored = store.close(trace_id, close_id=request.close_id, closed_at=request.closed_at)
        return _response(DiagnosticTraceCloseResponse.from_trace(stored, store.replay), 200)


def _diagnostic_root(root: Path) -> Path:
    try:
        absolute = root.absolute()
        if ".." in root.parts or absolute != absolute.resolve(strict=False):
            raise ApiError("ERROR_DIAGNOSTIC_TRACE_ROOT_INVALID", 503, "Diagnostic trace root is inaccessible.")
        if absolute.exists():
            if absolute.is_symlink() or not absolute.is_dir():
                raise ApiError("ERROR_DIAGNOSTIC_TRACE_ROOT_INVALID", 503, "Diagnostic trace root is inaccessible.")
    except OSError as exc:
        raise ApiError("ERROR_DIAGNOSTIC_TRACE_ROOT_INVALID", 503, "Diagnostic trace root is inaccessible.") from exc
    return absolute


def _create_store(root: Path) -> DiagnosticTraceStore:
    absolute = _diagnostic_root(root)
    try:
        absolute.mkdir(parents=True, mode=0o700, exist_ok=True)
    except OSError as exc:
        raise ApiError("ERROR_DIAGNOSTIC_TRACE_ROOT_INVALID", 503, "Diagnostic trace root is inaccessible.") from exc
    return DiagnosticTraceStore(absolute)


def _existing_store(root: Path) -> DiagnosticTraceStore:
    absolute = _diagnostic_root(root)
    if not absolute.exists():
        raise ApiError("ERROR_DIAGNOSTIC_TRACE_UNAVAILABLE", 404, "Diagnostic trace is unavailable.")
    return DiagnosticTraceStore(absolute)


def _require_start_identity(tenant_id: str, project_id: str, request: DiagnosticTraceStart) -> None:
    if (request.tenant_id, request.project_id) != (tenant_id, project_id):
        raise ApiError("ERR_DIAGNOSTIC_TRACE_IDENTITY_CONFLICT", 409, "Diagnostic trace request identity does not match the route.")


def _require_trace_identity(tenant_id: str, project_id: str, trace: DiagnosticTrace) -> None:
    if (trace.tenant_id, trace.project_id) != (tenant_id, project_id):
        raise ApiError("ERR_DIAGNOSTIC_TRACE_IDENTITY_CONFLICT", 409, "Diagnostic trace identity does not match the route.")


def _require_canonical_run(repository: ProjectRepository, tenant_id: str, project_id: str, run_id: str) -> None:
    try:
        repository.run(tenant_id, project_id, run_id)
    except RepositoryError as exc:
        if exc.code == "ERROR_DOMAIN_CONTRACT_FILE_MISSING":
            raise ApiError(exc.code, 404, exc.message) from exc
        raise


def _response(content: DiagnosticTraceStartResponse | DiagnosticTraceEntryResponse | DiagnosticTraceCloseResponse, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=content.model_dump(mode="json"))
