from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from .delivery_models import DeliveryCreateRequest
from .delivery_persistence_values import (
    DeliveryFailureBoundary,
    DeliveryIdempotencyRecord,
    DeliveryPersistRequest,
    DeliveryPersistedExport,
    DeliveryPersistenceError,
    DeliveryRecoverySidecar,
    canonical_json_bytes,
)
from .recovery_inventory import RecoveryReplayIdentity
from .repository import ProjectRepository


@dataclass(frozen=True, slots=True)
class DeliveryReplayDependencies:
    project: ProjectRepository
    read_index: Callable[[Path], DeliveryIdempotencyRecord]
    read_sidecar: Callable[[Path], DeliveryRecoverySidecar]
    read_export: Callable[[str, str, str], DeliveryPersistedExport]
    sidecar_request: Callable[[DeliveryRecoverySidecar], DeliveryPersistRequest]
    materialize: Callable[[DeliveryPersistRequest], None]
    inject: Callable[[DeliveryFailureBoundary], None]


class DeliveryReplayRecovery:
    def __init__(self, dependencies: DeliveryReplayDependencies) -> None:
        self._dependencies = dependencies

    def lookup(self, request: DeliveryPersistRequest) -> DeliveryPersistedExport | None:
        return self._lookup(
            request.tenant_id,
            request.project_id,
            request.idempotency_request_sha256,
            request.idempotency_key,
        )

    def replay_or_recover(self, request: DeliveryCreateRequest) -> DeliveryPersistedExport | None:
        tenant_id = request.export_request.tenant_id
        project_id = request.export_request.project_id
        request_sha256 = self._create_request_sha256(request)
        key = request.export_request.idempotency_key
        existing = self._lookup(tenant_id, project_id, request_sha256, key)
        path = self._dependencies.project._path(tenant_id, project_id, self.recovery_relative(key))
        if path.is_symlink():
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery persisted file is invalid.")
        if not path.exists():
            return existing
        sidecar = self._dependencies.read_sidecar(path)
        recovered = self._dependencies.sidecar_request(sidecar)
        if sidecar.idempotency_request_sha256 != request_sha256 or recovered.idempotency_request_sha256 != request_sha256:
            raise DeliveryPersistenceError("ERR_IDEMPOTENCY_CONFLICT", "The delivery recovery conflicts with the requested output.")
        if existing is None:
            self._dependencies.materialize(recovered)
        elif existing.result.export_id != recovered.result.export_id:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery recovery index is invalid.")
        self._dependencies.inject(DeliveryFailureBoundary.BEFORE_SIDECAR_REMOVAL)
        self._dependencies.project._remove(tenant_id, project_id, self.recovery_relative(key))
        return self._lookup(tenant_id, project_id, request_sha256, key)

    def completed_replay(self, request: DeliveryCreateRequest) -> DeliveryPersistedExport | None:
        return self._lookup(
            request.export_request.tenant_id,
            request.export_request.project_id,
            self._create_request_sha256(request),
            request.export_request.idempotency_key,
        )

    def _lookup(self, tenant_id: str, project_id: str, request_sha256: str, idempotency_key: str) -> DeliveryPersistedExport | None:
        path = self._dependencies.project._path(tenant_id, project_id, self.idempotency_relative(idempotency_key))
        if path.is_symlink():
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery persisted file is invalid.")
        if not path.exists():
            return None
        index = self._dependencies.read_index(path)
        if index.tenant_id != tenant_id or index.project_id != project_id or index.idempotency_request_sha256 != request_sha256:
            raise DeliveryPersistenceError("ERR_IDEMPOTENCY_CONFLICT", "The delivery idempotency key conflicts with stored output.")
        export = self._dependencies.read_export(tenant_id, project_id, index.export_id)
        if export.result.delivery_package_id != index.delivery_package_id or export.result.delivery_export_result_id != index.delivery_export_result_id or export.result.delivery_export_request_id != index.delivery_export_request_id or export.result.export_id != index.export_id:
            raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "The delivery idempotency index is invalid.")
        return export

    @staticmethod
    def idempotency_relative(idempotency_key: str) -> str:
        return f"delivery/idempotency/{hashlib.sha256(idempotency_key.encode('utf-8')).hexdigest()}.json"

    @staticmethod
    def recovery_relative(idempotency_key: str) -> str:
        return f"delivery/recovery/{hashlib.sha256(idempotency_key.encode('utf-8')).hexdigest()}.json"

    @staticmethod
    def recovery_identity(tenant_id: str, project_id: str, idempotency_key: str) -> RecoveryReplayIdentity:
        return RecoveryReplayIdentity(
            tenant_id,
            project_id,
            "delivery-recovery",
            DeliveryReplayRecovery.recovery_relative(idempotency_key),
        )

    @staticmethod
    def _create_request_sha256(request: DeliveryCreateRequest) -> str:
        return hashlib.sha256(canonical_json_bytes({"project_id": request.export_request.project_id, "request": request.model_dump(mode="json"), "tenant_id": request.export_request.tenant_id})).hexdigest()
