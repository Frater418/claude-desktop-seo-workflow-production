"""HTTP error boundaries for the Operator API."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from services.operator_routing import route_error

from .artifact_revisions import ArtifactRevisionError
from .event_store import EventStoreError
from .models import ErrorEnvelope
from .package4 import Package4Error
from .repository import RepositoryError


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
        status = 404 if error.code == "ERROR_DOMAIN_REFERENCE_UNKNOWN" else 409 if error.code == "ERR_STALE_REVISION" else 422
        return JSONResponse(status_code=status, content=ErrorEnvelope(code=error.code, message=error.message).model_dump())

    @app.exception_handler(ArtifactRevisionError)
    async def artifact_revision_error(_: Request, error: ArtifactRevisionError) -> JSONResponse:
        status = 404 if error.code in {"ERROR_DOMAIN_REFERENCE_UNKNOWN", "ERROR_DOMAIN_CONTRACT_FILE_MISSING", "ERR_TENANT_ISOLATION"} else 409 if error.code == "ERR_STALE_REVISION" else 422
        return JSONResponse(status_code=status, content=ErrorEnvelope(code=error.code, message=error.message).model_dump())
