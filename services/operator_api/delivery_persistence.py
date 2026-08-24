from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError
from pydantic_core import PydanticCustomError

from services.owned_file_lock import OwnedFileLock, OwnedFileLockError

from .delivery_models import DeliveryCreateRequest, DeliveryExportResult, DeliveryPackageRecord
from .delivery_persistence_values import (
    DeliveryFailureBoundary,
    DeliveryIdempotencyRecord,
    DeliveryPersistRequest,
    DeliveryPersistedExport,
    DeliveryPersistenceError,
    DeliveryRecoverySidecar,
    canonical_model_bytes,
    canonical_package_record_bytes,
    sha256,
)
from .delivery_persistence_readback import DeliveryPersistenceReadback
from .delivery_replay_recovery import DeliveryReplayDependencies, DeliveryReplayRecovery
from .delivery_persistence_storage import _atomic_write_once
from .repository import ProjectRepository


ModelT = TypeVar("ModelT", bound=BaseModel)


class DeliveryExportRepository:
    def __init__(
        self,
        project: ProjectRepository,
        failure_injector: Callable[[DeliveryFailureBoundary], None] | None = None,
    ) -> None:
        self._project = project
        self._failure_injector = failure_injector
        self._readback = DeliveryPersistenceReadback(project)
        self._replay = DeliveryReplayRecovery(
            DeliveryReplayDependencies(
                project,
                lambda path: self._readback.read_model(path, DeliveryIdempotencyRecord),
                lambda path: self._readback.read_model(path, DeliveryRecoverySidecar),
                self._readback.recovery_export,
                self._sidecar_request,
                self._materialize,
                self._inject,
            )
        )

    @contextmanager
    def lock(self, tenant_id: str, project_id: str) -> Iterator[None]:
        path = self._project._path(tenant_id, project_id, "delivery/locks/project.lock")
        try:
            with OwnedFileLock(path, grace_seconds=0):
                yield
        except OwnedFileLockError as error:
            raise DeliveryPersistenceError("ERR_CONCURRENT_DELIVERY_CONFLICT", "A delivery export is already in progress.") from error

    def lookup_idempotency(self, request: DeliveryPersistRequest) -> DeliveryPersistedExport | None:
        return self._replay.lookup(request)

    def replay_or_recover(self, request: DeliveryCreateRequest) -> DeliveryPersistedExport | None:
        return self._replay.replay_or_recover(request)

    def completed_replay(self, request: DeliveryCreateRequest) -> DeliveryPersistedExport | None:
        return self._replay.completed_replay(request)

    def recover(self, request: DeliveryPersistRequest) -> DeliveryPersistedExport | None:
        sidecar = self._optional_model(request, self._recovery_path(request), DeliveryRecoverySidecar)
        existing = self.lookup_idempotency(request)
        if sidecar is None:
            return existing
        recovered = self._sidecar_request(sidecar)
        if sidecar.idempotency_request_sha256 != recovered.idempotency_request_sha256 or recovered.idempotency_request_sha256 != request.idempotency_request_sha256:
            raise DeliveryPersistenceError("ERR_IDEMPOTENCY_CONFLICT", "The delivery recovery conflicts with the requested output.")
        if existing is None:
            self._materialize(recovered)
        elif existing.result.export_id != recovered.result.export_id:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery recovery index is invalid.")
        self._inject(DeliveryFailureBoundary.BEFORE_SIDECAR_REMOVAL)
        self._project._remove(request.tenant_id, request.project_id, self._recovery_path(request))
        return self.lookup_idempotency(request)

    def persist(self, request: DeliveryPersistRequest) -> DeliveryPersistedExport:
        recovered = self.recover(request)
        if recovered is not None:
            return recovered.replayed()
        self._assert_identifiers_available(request)
        self._write_once_json(request, self._recovery_path(request), DeliveryRecoverySidecar.from_request(request))
        self._inject(DeliveryFailureBoundary.SIDECAR_WRITTEN)
        self._materialize(request)
        stored = self.lookup_idempotency(request)
        if stored is None:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery idempotency index is unavailable.")
        self._inject(DeliveryFailureBoundary.BEFORE_SIDECAR_REMOVAL)
        self._project._remove(request.tenant_id, request.project_id, self._recovery_path(request))
        return stored

    def list_results(self, tenant_id: str, project_id: str) -> tuple[DeliveryExportResult, ...]:
        return self._readback.list_results(tenant_id, project_id)

    def package_record(self, tenant_id: str, project_id: str, export_id: str) -> DeliveryPackageRecord:
        return self._readback.completed_export(tenant_id, project_id, export_id).package_record

    def archive_bytes(self, tenant_id: str, project_id: str, export_id: str) -> bytes:
        return self._readback.archive_bytes(tenant_id, project_id, export_id)

    def _materialize(self, request: DeliveryPersistRequest) -> None:
        self._write_once_json(request, self._export_relative(request, "request.json"), request.create_request)
        self._write_once_bytes(request, self._export_relative(request, "archive.zip"), request.archive_bytes)
        self._inject(DeliveryFailureBoundary.ARCHIVE_WRITTEN)
        self._write_once_json(request, self._export_relative(request, "delivery-package-record.json"), request.package_record)
        self._inject(DeliveryFailureBoundary.PACKAGE_RECORD_WRITTEN)
        self._write_once_json(request, self._export_relative(request, "result.json"), request.result)
        self._inject(DeliveryFailureBoundary.RESULT_WRITTEN)
        self._inject(DeliveryFailureBoundary.BEFORE_IDEMPOTENCY)
        self._write_once_json(
            request,
            self._idempotency_path(request),
            DeliveryIdempotencyRecord(
                tenant_id=request.tenant_id,
                project_id=request.project_id,
                request_sha256=request.request_sha256,
                idempotency_request_sha256=request.idempotency_request_sha256,
                result_sha256=sha256(canonical_model_bytes(request.result)),
                package_record_sha256=sha256(canonical_package_record_bytes(request.package_record)),
                archive_sha256=sha256(request.archive_bytes),
                archive_size_bytes=len(request.archive_bytes),
                export_id=request.result.export_id,
                delivery_package_id=request.result.delivery_package_id,
                delivery_export_result_id=request.result.delivery_export_result_id,
                delivery_export_request_id=request.result.delivery_export_request_id,
                role_handoff_manifest_ids=tuple(item.role_handoff_manifest_id for item in request.create_request.role_package_requests),
                notion_import_manifest_id=request.create_request.notion_import_request.notion_import_manifest_id,
            ),
        )

    def _assert_identifiers_available(self, request: DeliveryPersistRequest) -> None:
        direct = self._export_path(request.tenant_id, request.project_id, request.result.export_id, "result.json")
        if direct.is_symlink() or direct.exists():
            raise DeliveryPersistenceError("ERR_IDEMPOTENCY_CONFLICT", "The delivery export identity is already in use.")
        identities = self._caller_identities(request)
        for stored in self._readback.completed_indexes(request.tenant_id, request.project_id):
            if identities.intersection(self._index_identities(stored)):
                raise DeliveryPersistenceError("ERR_IDEMPOTENCY_CONFLICT", "A delivery caller identity is already in use.")

    def _sidecar_request(self, sidecar: DeliveryRecoverySidecar) -> DeliveryPersistRequest:
        try:
            return sidecar.to_request()
        except (PydanticCustomError, ValidationError) as error:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery recovery record is invalid.") from error

    def _optional_model(self, request: DeliveryPersistRequest, relative: str, model: type[ModelT]) -> ModelT | None:
        path = self._project._path(request.tenant_id, request.project_id, relative)
        if path.is_symlink():
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery persisted file is invalid.")
        if not path.exists():
            return None
        return self._readback.read_model(path, model)

    def _write_once_json(self, request: DeliveryPersistRequest, relative: str, value: DeliveryCreateRequest | DeliveryExportResult | DeliveryPackageRecord | DeliveryRecoverySidecar | DeliveryIdempotencyRecord) -> None:
        content = canonical_package_record_bytes(value) if isinstance(value, DeliveryPackageRecord) else canonical_model_bytes(value)
        self._write_once_bytes(request, relative, content)

    def _write_once_bytes(self, request: DeliveryPersistRequest, relative: str, content: bytes) -> None:
        path = self._project._path(request.tenant_id, request.project_id, relative)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.is_symlink() or path.exists():
                if path.is_symlink() or not path.is_file() or path.read_bytes() != content:
                    raise DeliveryPersistenceError("ERR_IDEMPOTENCY_CONFLICT", "Immutable delivery material conflicts with stored output.")
                return
            _atomic_write_once(path, content)
        except OSError as error:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery export cannot be written.") from error

    def _inject(self, boundary: DeliveryFailureBoundary) -> None:
        if self._failure_injector is not None:
            try:
                self._failure_injector(boundary)
            except OSError as error:
                raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery export was interrupted.") from error

    @staticmethod
    def _export_relative(request: DeliveryPersistRequest, name: str) -> str:
        return f"delivery/exports/{request.result.export_id}/{name}"

    def _export_path(self, tenant_id: str, project_id: str, export_id: str, name: str) -> Path:
        return self._project._path(tenant_id, project_id, f"delivery/exports/{export_id}/{name}")

    @staticmethod
    def _idempotency_path(request: DeliveryPersistRequest) -> str:
        return DeliveryReplayRecovery.idempotency_relative(request.idempotency_key)

    @staticmethod
    def _recovery_path(request: DeliveryPersistRequest) -> str:
        return DeliveryReplayRecovery.recovery_relative(request.idempotency_key)

    @staticmethod
    def _caller_identities(request: DeliveryPersistRequest) -> set[str]:
        return {
            request.result.export_id,
            request.result.delivery_package_id,
            request.result.delivery_export_result_id,
            request.result.delivery_export_request_id,
            request.create_request.notion_import_request.notion_import_manifest_id,
            *(item.role_handoff_manifest_id for item in request.create_request.role_package_requests),
        }

    @staticmethod
    def _index_identities(index: DeliveryIdempotencyRecord) -> set[str]:
        return {
            index.export_id,
            index.delivery_package_id,
            index.delivery_export_result_id,
            index.delivery_export_request_id,
            index.notion_import_manifest_id,
            *index.role_handoff_manifest_ids,
        }
