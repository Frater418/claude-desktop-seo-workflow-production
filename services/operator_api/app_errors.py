"""HTTP error boundaries for the Operator API."""

from __future__ import annotations

from typing import Final

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response

from services.operator_routing import route_error

from .artifact_revisions import ArtifactRevisionError
from .delivery_composer import DeliveryCompositionError
from .delivery_persistence import DeliveryPersistenceError
from .diagnostic_trace_store import DiagnosticTraceStoreError
from .event_store import EventStoreError
from .models import ErrorEnvelope
from .package4 import Package4Error
from .project_deletion import ProjectDeletionError
from .repository import RepositoryError


_DELIVERY_OPERATION_IDS: Final = frozenset(
    (
        "previewDelivery",
        "createDeliveryExport",
        "listDeliveryExports",
        "getDeliveryExport",
        "downloadDeliveryExport",
    )
)
_DIAGNOSTIC_OPERATION_IDS: Final = frozenset(("createDiagnosticTrace", "appendDiagnosticTraceEntry", "closeDiagnosticTrace"))
_PROJECT_DELETION_OPERATION_IDS: Final = frozenset(("previewProjectDeletion", "confirmProjectDeletion"))


class ApiError(RuntimeError):
    """Path-free HTTP boundary error."""

    def __init__(self, code: str, status_code: int, message: str, routed: bool = False) -> None:
        self.code = code
        self.status_code = status_code
        self.message = message
        self.routed = routed
        super().__init__(message)


def register_error_handlers(app: FastAPI) -> None:
    """Register the API's single error translation boundary."""

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(request: Request, error: RequestValidationError) -> Response:
        if request.scope["route"].operation_id in _DELIVERY_OPERATION_IDS:
            return JSONResponse(
                status_code=422,
                content=ErrorEnvelope(
                    code="ERROR_DELIVERY_REQUEST_INVALID",
                    message="Delivery request validation failed.",
                ).model_dump(),
            )
        if request.scope["route"].operation_id in _DIAGNOSTIC_OPERATION_IDS:
            return JSONResponse(
                status_code=422,
                content=ErrorEnvelope(
                    code="ERROR_DIAGNOSTIC_TRACE_REQUEST_INVALID",
                    message="Diagnostic trace request validation failed.",
                ).model_dump(),
            )
        if request.scope["route"].operation_id in _PROJECT_DELETION_OPERATION_IDS:
            return JSONResponse(
                status_code=422,
                content=ErrorEnvelope(
                    code="ERROR_PROJECT_DELETE_CONFIRMATION_INVALID",
                    message="Project deletion requires the exact confirmation text LOESCHEN.",
                ).model_dump(),
            )
        return await request_validation_exception_handler(request, error)

    @app.exception_handler(DiagnosticTraceStoreError)
    async def diagnostic_trace_error(_: Request, error: DiagnosticTraceStoreError) -> JSONResponse:
        status = 422 if error.code == "ERROR_DIAGNOSTIC_RECORD_SIZE_LIMIT" else 404 if error.code == "ERROR_DIAGNOSTIC_TRACE_UNAVAILABLE" else 507 if error.code in {"ERROR_DIAGNOSTIC_OPERATION_LIMIT", "ERROR_DIAGNOSTIC_RUN_SIZE_LIMIT", "ERROR_DIAGNOSTIC_INDEX_SIZE_LIMIT", "ERROR_DIAGNOSTIC_RETENTION_LIMIT"} else 409 if error.code in {"ERROR_DIAGNOSTIC_TRACE_CONFLICT", "ERROR_DIAGNOSTIC_TRACE_CLOSED", "ERROR_DIAGNOSTIC_TRACE_STATE_INVALID"} else 503
        return JSONResponse(status_code=status, content=ErrorEnvelope(code=error.code, message=error.message).model_dump())

    @app.exception_handler(ProjectDeletionError)
    async def project_deletion_error(_: Request, error: ProjectDeletionError) -> JSONResponse:
        if error.code == "ERROR_PROJECT_DELETE_NOT_MANAGED":
            status = 403
        elif error.code == "ERROR_PROJECT_DELETE_NOT_FOUND":
            status = 404
        elif error.code == "ERROR_PROJECT_DELETE_CONFIRMATION_INVALID":
            status = 422
        elif error.code == "ERROR_PROJECT_DELETE_AUDIT_FAILED":
            status = 507
        elif error.code in {
            "ERR_IDEMPOTENCY_CONFLICT",
            "ERROR_PROJECT_DELETE_ACTIVE_RUN",
            "ERROR_PROJECT_DELETE_PREVIEW_STALE",
            "ERROR_PROJECT_DELETE_RECOVERY_REQUIRED",
        }:
            status = 409
        else:
            status = 503
        return JSONResponse(status_code=status, content=ErrorEnvelope(code=error.code, message=error.message).model_dump())

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

    @app.exception_handler(Package4Error)
    async def package4_error(_: Request, error: Package4Error) -> JSONResponse:
        if error.code in {"ERROR_DOMAIN_REFERENCE_UNKNOWN", "ERROR_PRODUCTION_EXECUTION_NOT_FOUND"}:
            status = 404
        elif error.code == "ERR_STALE_REVISION":
            status = 409
        elif error.code == "ERROR_LLM_BACKEND_TIMEOUT":
            status = 504
        elif error.code == "ERROR_LLM_BACKEND_RESPONSE_INVALID":
            status = 502
        elif error.code.startswith("ERROR_LLM_BACKEND_"):
            status = 503
        else:
            status = 422
        return JSONResponse(status_code=status, content=ErrorEnvelope(code=error.code, message=error.message).model_dump())

    @app.exception_handler(ArtifactRevisionError)
    async def artifact_revision_error(_: Request, error: ArtifactRevisionError) -> JSONResponse:
        status = 404 if error.code in {"ERROR_DOMAIN_REFERENCE_UNKNOWN", "ERROR_DOMAIN_CONTRACT_FILE_MISSING", "ERR_TENANT_ISOLATION"} else 409 if error.code in {"ERR_STALE_REVISION", "ERR_IDEMPOTENCY_CONFLICT"} else 422
        return JSONResponse(status_code=status, content=ErrorEnvelope(code=error.code, message=error.message).model_dump())

    @app.exception_handler(DeliveryCompositionError)
    async def delivery_composition_error(_: Request, error: DeliveryCompositionError) -> JSONResponse:
        status = 409 if error.code == "DELIVERY_FINAL_POLICY_REJECTED" else 422
        return JSONResponse(status_code=status, content=ErrorEnvelope(code=error.code, message=error.message).model_dump())

    @app.exception_handler(DeliveryPersistenceError)
    async def delivery_persistence_error(_: Request, error: DeliveryPersistenceError) -> JSONResponse:
        status = 404 if error.code == "ERROR_DOMAIN_REFERENCE_UNKNOWN" else 409 if error.code in {"ERR_CONCURRENT_DELIVERY_CONFLICT", "ERR_IDEMPOTENCY_CONFLICT"} else 503
        return JSONResponse(status_code=status, content=ErrorEnvelope(code=error.code, message=error.message).model_dump())
