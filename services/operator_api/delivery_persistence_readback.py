from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .delivery_models import DeliveryCreateRequest, DeliveryExportResult, DeliveryPackageRecord
from .delivery_persistence_values import (
    DeliveryIdempotencyRecord,
    DeliveryPersistedExport,
    DeliveryPersistenceError,
    DeliveryRecoverySidecar,
    canonical_json_bytes,
    sha256,
)
from .repository import ProjectRepository


ModelT = TypeVar("ModelT", bound=BaseModel)


class DeliveryPersistenceReadback:
    def __init__(self, project: ProjectRepository) -> None:
        self._project = project

    def list_results(self, tenant_id: str, project_id: str) -> tuple[DeliveryExportResult, ...]:
        exports = tuple(self.completed_export(tenant_id, project_id, index.export_id) for index in self.completed_indexes(tenant_id, project_id))
        if len({item.result.export_id for item in exports}) != len(exports):
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery idempotency collection is duplicated.")
        return tuple(sorted((item.result for item in exports), key=lambda item: (item.created_at, item.export_id)))

    def completed_indexes(self, tenant_id: str, project_id: str) -> tuple[DeliveryIdempotencyRecord, ...]:
        root = self._project._path(tenant_id, project_id, "delivery/idempotency")
        if not root.exists():
            return ()
        if root.is_symlink() or not root.is_dir():
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery idempotency collection is invalid.")
        try:
            paths = tuple(sorted(path for path in root.iterdir() if path.suffix == ".json"))
        except OSError as error:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery idempotency collection is unreadable.") from error
        indexes = tuple(self.read_model(path, DeliveryIdempotencyRecord) for path in paths)
        if any(index.tenant_id != tenant_id or index.project_id != project_id for index in indexes):
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery idempotency collection is invalid.")
        return indexes

    def completed_export(self, tenant_id: str, project_id: str, export_id: str) -> DeliveryPersistedExport:
        return self._export(tenant_id, project_id, export_id, require_sidecar_absent=True)

    def recovery_export(self, tenant_id: str, project_id: str, export_id: str) -> DeliveryPersistedExport:
        return self._export(tenant_id, project_id, export_id, require_sidecar_absent=False)

    def _export(self, tenant_id: str, project_id: str, export_id: str, require_sidecar_absent: bool) -> DeliveryPersistedExport:
        indexes = tuple(index for index in self.completed_indexes(tenant_id, project_id) if index.export_id == export_id)
        if not indexes:
            if self._incomplete_exists(tenant_id, project_id, export_id):
                raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery export is incomplete.")
            raise DeliveryPersistenceError("ERROR_DOMAIN_REFERENCE_UNKNOWN", "The delivery export is unavailable.")
        if len(indexes) != 1:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery idempotency collection is duplicated.")
        index = indexes[0]
        if require_sidecar_absent and self._has_recovery(tenant_id, project_id, export_id):
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery export recovery is incomplete.")
        request, request_bytes = self._read_export_model(tenant_id, project_id, export_id, "request.json", DeliveryCreateRequest)
        result, result_bytes = self._read_export_model(tenant_id, project_id, export_id, "result.json", DeliveryExportResult)
        record, record_bytes = self._read_export_model(tenant_id, project_id, export_id, "delivery-package-record.json", DeliveryPackageRecord)
        archive = self.read_regular(self._export_path(tenant_id, project_id, export_id, "archive.zip"), "ERROR_DELIVERY_PERSISTENCE")
        self._validate(index, request, result, record, request_bytes, result_bytes, record_bytes, archive, tenant_id, project_id, export_id)
        return DeliveryPersistedExport(result=result, package_record=record)

    def archive_bytes(self, tenant_id: str, project_id: str, export_id: str) -> bytes:
        export = self.completed_export(tenant_id, project_id, export_id)
        archive = self.read_regular(self._export_path(tenant_id, project_id, export_id, "archive.zip"), "ERROR_DELIVERY_PERSISTENCE")
        if sha256(archive) != export.result.zip_sha256 or len(archive) != export.result.zip_size_bytes:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery archive bindings are invalid.")
        return archive

    def read_model(self, path: Path, model: type[ModelT]) -> ModelT:
        try:
            return model.model_validate(json.loads(self.read_regular(path, "ERROR_DELIVERY_PERSISTENCE").decode("utf-8")))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery persisted JSON is invalid.") from error

    def read_regular(self, path: Path, missing_code: str) -> bytes:
        try:
            if path.is_symlink() or not path.is_file():
                raise DeliveryPersistenceError(missing_code, "The delivery persisted file is unavailable.")
            content = path.read_bytes()
        except OSError as error:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery persisted file is unreadable.") from error
        try:
            value = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return content
        if canonical_json_bytes(value) != content:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery persisted JSON is not canonical.")
        return content

    def _validate(self, index: DeliveryIdempotencyRecord, request: DeliveryCreateRequest, result: DeliveryExportResult, record: DeliveryPackageRecord, request_bytes: bytes, result_bytes: bytes, record_bytes: bytes, archive: bytes, tenant_id: str, project_id: str, export_id: str) -> None:
        material_matches = (
            index.request_sha256 == sha256(request_bytes)
            and index.result_sha256 == sha256(result_bytes)
            and index.package_record_sha256 == sha256(record_bytes)
            and index.archive_sha256 == sha256(archive)
            and index.archive_size_bytes == len(archive)
        )
        identities_match = (
            result.tenant_id == record.tenant_id == request.export_request.tenant_id == tenant_id
            and result.project_id == record.project_id == request.export_request.project_id == project_id
            and result.export_id == record.export_id == request.export_id == export_id
            and result.delivery_package_id == record.delivery_package_id == request.delivery_package_id == index.delivery_package_id
            and result.delivery_export_result_id == request.delivery_export_result_id == index.delivery_export_result_id
            and result.delivery_export_request_id == request.export_request.delivery_export_request_id == index.delivery_export_request_id
            and index.role_handoff_manifest_ids == tuple(item.role_handoff_manifest_id for item in request.role_package_requests)
            and tuple(item.manifest_id for item in result.role_handoff_manifests) == index.role_handoff_manifest_ids
            and tuple(item.role_handoff_manifest_id for item in record.role_packages) == index.role_handoff_manifest_ids
            and result.notion_import_manifest.manifest_id == request.notion_import_request.notion_import_manifest_id == record.notion_import_manifest.notion_import_manifest_id == index.notion_import_manifest_id
            and result.source_snapshot_revision == record.source_snapshot_revision == request.export_request.source_snapshot_revision
            and result.created_at == record.created_at == request.export_request.created_at
            and record.package_revision == request.package_revision
            and result.replay_state == "created"
            and result.zip_sha256 == record.zip_sha256 == index.archive_sha256
            and result.package_sha256 == record.package_sha256
        )
        request_identity = sha256(canonical_json_bytes({"project_id": project_id, "request": request.model_dump(mode="json"), "tenant_id": tenant_id}))
        if not material_matches or not identities_match or index.idempotency_request_sha256 != request_identity:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery completed export is invalid.")

    def _incomplete_exists(self, tenant_id: str, project_id: str, export_id: str) -> bool:
        root = self._project._path(tenant_id, project_id, f"delivery/exports/{export_id}")
        if root.exists() or root.is_symlink():
            return True
        for recovery in (
            self._project._path(tenant_id, project_id, "delivery/recovery"),
            self._project._path(tenant_id, project_id, "delivery/delivery/recovery"),
        ):
            if not recovery.exists():
                continue
            if recovery.is_symlink() or not recovery.is_dir():
                raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery recovery collection is invalid.")
            try:
                sidecars = tuple(path for path in recovery.iterdir() if path.suffix == ".json")
            except OSError as error:
                raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery recovery collection is unreadable.") from error
            for path in sidecars:
                sidecar = self.read_model(path, DeliveryRecoverySidecar)
                if sidecar.result.export_id == export_id or sidecar.create_request.export_id == export_id:
                    return True
        return False

    def _read_export_model(self, tenant_id: str, project_id: str, export_id: str, name: str, model: type[ModelT]) -> tuple[ModelT, bytes]:
        path = self._export_path(tenant_id, project_id, export_id, name)
        return self.read_model(path, model), self.read_regular(path, "ERROR_DELIVERY_PERSISTENCE")

    def _export_path(self, tenant_id: str, project_id: str, export_id: str, name: str) -> Path:
        return self._project._path(tenant_id, project_id, f"delivery/exports/{export_id}/{name}")

    def _has_recovery(self, tenant_id: str, project_id: str, export_id: str) -> bool:
        recovery = self._project._path(tenant_id, project_id, "delivery/recovery")
        if not recovery.exists():
            return False
        if recovery.is_symlink() or not recovery.is_dir():
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery recovery collection is invalid.")
        try:
            paths = tuple(path for path in recovery.iterdir() if path.suffix == ".json")
        except OSError as error:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery recovery collection is unreadable.") from error
        return any(self.read_model(path, DeliveryRecoverySidecar).result.export_id == export_id for path in paths)
