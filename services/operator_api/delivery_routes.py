from __future__ import annotations

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import JsonValue

from .app_errors import ApiError
from .delivery_admission import DeliveryAdmission
from .delivery_composer import DeliveryCompositionError, compose_delivery, preview_delivery
from .delivery_models import (
    DeliveryCreateRequest,
    DeliveryExportHistoryResponse,
    DeliveryExportResult,
    DeliveryPackageRecord,
    DeliveryPreviewResponse,
    DeliveryScope,
    ExportId,
)
from .delivery_persistence import DeliveryExportRepository, DeliveryPersistenceError
from .delivery_persistence_values import DeliveryPersistRequest
from .delivery_replay_recovery import DeliveryReplayRecovery
from .delivery_repository import DeliverySnapshotRepository
from .models import ErrorEnvelope
from .recovery_inventory import RecoveryInventory


_PREFIX = "/v1/tenants/{tenant_id}/projects/{project_id}/delivery"
_READ_ERRORS = {
    404: {"model": ErrorEnvelope},
    422: {"model": ErrorEnvelope},
    503: {"model": ErrorEnvelope},
}


def register_delivery_routes(
    app: FastAPI,
    snapshots: DeliverySnapshotRepository,
    exports: DeliveryExportRepository,
    recovery_inventory: RecoveryInventory,
    admission: DeliveryAdmission,
) -> None:
    @app.get(
        f"{_PREFIX}/preview",
        response_model=DeliveryPreviewResponse,
        responses=_READ_ERRORS,
        operation_id="previewDelivery",
    )
    def preview(tenant_id: str, project_id: str, scope: DeliveryScope) -> DeliveryPreviewResponse:
        return preview_delivery(snapshots.snapshot(tenant_id, project_id), scope)

    @app.post(
        f"{_PREFIX}/exports",
        response_model=DeliveryExportResult,
        status_code=201,
        responses={
            200: {"model": DeliveryExportResult},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
            503: {"model": ErrorEnvelope},
        },
        operation_id="createDeliveryExport",
    )
    def create(tenant_id: str, project_id: str, request: DeliveryCreateRequest) -> JSONResponse:
        _require_route_identity(tenant_id, project_id, request)
        recovery = DeliveryReplayRecovery.recovery_identity(
            tenant_id,
            project_id,
            request.export_request.idempotency_key,
        )
        if recovery_inventory.sidecars():
            with admission.lock():
                authorization = recovery_inventory.authorize(recovery)
                if authorization.replay is not None:
                    with exports.lock(tenant_id, project_id):
                        recovery_inventory.authorize(recovery)
                        replay = exports.replay_or_recover(request)
                        if replay is None:
                            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The authorized delivery recovery is unavailable.")
                        return _result_response(replay.replayed().result, 200)
                replay = exports.completed_replay(request)
                if replay is not None:
                    return _result_response(replay.replayed().result, 200)

        replay = exports.completed_replay(request)
        if replay is not None:
            return _result_response(replay.replayed().result, 200)

        composition = compose_delivery(snapshots.snapshot(tenant_id, project_id), request)
        persist_request = DeliveryPersistRequest(
            tenant_id=tenant_id,
            project_id=project_id,
            create_request=request,
            result=composition.result,
            package_record=composition.package_record,
            archive_bytes=composition.archive.zip_bytes,
        )
        with admission.lock():
            with exports.lock(tenant_id, project_id):
                authorization = recovery_inventory.authorize(recovery)
                replay = exports.replay_or_recover(request)
                if replay is not None:
                    return _result_response(replay.replayed().result, 200)
                if authorization.replay is not None:
                    raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The authorized delivery recovery is unavailable.")
                return _result_response(exports.persist(persist_request).result, 201)

    @app.get(
        f"{_PREFIX}/exports",
        response_model=DeliveryExportHistoryResponse,
        responses={404: {"model": ErrorEnvelope}, 503: {"model": ErrorEnvelope}},
        operation_id="listDeliveryExports",
    )
    def list_exports(tenant_id: str, project_id: str) -> DeliveryExportHistoryResponse:
        return DeliveryExportHistoryResponse(data=exports.list_results(tenant_id, project_id))

    @app.get(
        f"{_PREFIX}/exports/{{export_id}}",
        response_model=DeliveryPackageRecord,
        response_model_exclude_none=True,
        responses=_READ_ERRORS,
        operation_id="getDeliveryExport",
    )
    def get_export(tenant_id: str, project_id: str, export_id: ExportId) -> DeliveryPackageRecord:
        return exports.package_record(tenant_id, project_id, export_id)

    @app.get(
        f"{_PREFIX}/exports/{{export_id}}/download",
        response_class=Response,
        responses={
            200: {
                "content": {"application/zip": {"schema": {"format": "binary", "type": "string"}}},
                "headers": {
                    "Content-Disposition": {"schema": {"type": "string"}},
                    "ETag": {"schema": {"type": "string"}},
                },
            },
            **_READ_ERRORS,
        },
        operation_id="downloadDeliveryExport",
    )
    def download(tenant_id: str, project_id: str, export_id: ExportId) -> Response:
        record = exports.package_record(tenant_id, project_id, export_id)
        archive = exports.archive_bytes(tenant_id, project_id, export_id)
        filename = f"{record.project_id}-{record.scope.value}-r{record.package_revision}.zip"
        return Response(
            content=archive,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "ETag": f'"{record.zip_sha256}"',
            },
        )

    default_openapi = app.openapi

    def openapi() -> dict[str, JsonValue]:
        document = default_openapi()
        document["paths"][f"{_PREFIX}/exports"]["get"]["responses"].pop("422", None)
        return document

    app.openapi = openapi


def _require_route_identity(tenant_id: str, project_id: str, request: DeliveryCreateRequest) -> None:
    export = request.export_request
    if export.tenant_id != tenant_id or export.project_id != project_id:
        raise ApiError("ERR_DELIVERY_IDENTITY_CONFLICT", 409, "Delivery request identity does not match the route.")


def _result_response(result: DeliveryExportResult, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=result.model_dump(mode="json"))
