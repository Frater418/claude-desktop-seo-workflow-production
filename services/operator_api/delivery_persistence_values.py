from __future__ import annotations

import base64
import binascii
import hashlib
import json
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

from .delivery_models import (
    DeliveryCreateRequest,
    DeliveryExportResult,
    DeliveryPackageRecord,
    ExportId,
    NotionManifestId,
    PackageId,
    ProjectId,
    RequestId,
    ResultId,
    RoleManifestId,
    Sha256,
    TenantId,
)
from .models import JsonValue
from .repository import RepositoryError


class DeliveryPersistenceValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class DeliveryPersistenceError(RepositoryError):
    pass


class DeliveryPersistRequest(DeliveryPersistenceValue):
    tenant_id: TenantId
    project_id: ProjectId
    create_request: DeliveryCreateRequest
    result: DeliveryExportResult
    package_record: DeliveryPackageRecord
    archive_bytes: bytes

    @model_validator(mode="after")
    def require_bound_material(self) -> DeliveryPersistRequest:
        request = self.create_request
        result = self.result
        record = self.package_record
        identities_match = (
            request.export_request.tenant_id == self.tenant_id
            and request.export_request.project_id == self.project_id
            and result.tenant_id == self.tenant_id
            and result.project_id == self.project_id
            and record.tenant_id == self.tenant_id
            and record.project_id == self.project_id
            and result.export_id == request.export_id == record.export_id
            and result.delivery_package_id == request.delivery_package_id == record.delivery_package_id
            and result.delivery_export_result_id == request.delivery_export_result_id
        )
        if not identities_match:
            raise PydanticCustomError("delivery_persist_identity", "delivery persistence identities must match")
        archive_sha256 = hashlib.sha256(self.archive_bytes).hexdigest()
        if archive_sha256 != result.zip_sha256 or archive_sha256 != record.zip_sha256 or len(self.archive_bytes) != result.zip_size_bytes:
            raise PydanticCustomError("delivery_persist_archive", "delivery archive bindings must match")
        return self

    @property
    def request_sha256(self) -> str:
        return sha256(canonical_model_bytes(self.create_request))

    @property
    def idempotency_request_sha256(self) -> str:
        return sha256(
            canonical_json_bytes(
                {
                    "project_id": self.project_id,
                    "request": self.create_request.model_dump(mode="json"),
                    "tenant_id": self.tenant_id,
                }
            )
        )

    @property
    def idempotency_key(self) -> str:
        return self.create_request.export_request.idempotency_key


class DeliveryPersistedExport(DeliveryPersistenceValue):
    result: DeliveryExportResult
    package_record: DeliveryPackageRecord

    def replayed(self) -> DeliveryPersistedExport:
        return self.model_copy(update={"result": self.result.model_copy(update={"replay_state": "replayed"})})


class DeliveryRecoverySidecar(DeliveryPersistenceValue):
    idempotency_request_sha256: Sha256
    create_request_sha256: Sha256
    result_sha256: Sha256
    package_record_sha256: Sha256
    archive_sha256: Sha256
    create_request: DeliveryCreateRequest
    result: DeliveryExportResult
    package_record: DeliveryPackageRecord
    archive_base64: str = Field(pattern=r"^[A-Za-z0-9+/]*={0,2}$")

    @classmethod
    def from_request(cls, request: DeliveryPersistRequest) -> DeliveryRecoverySidecar:
        return cls(
            idempotency_request_sha256=request.idempotency_request_sha256,
            create_request_sha256=request.request_sha256,
            result_sha256=sha256(canonical_model_bytes(request.result)),
            package_record_sha256=sha256(canonical_package_record_bytes(request.package_record)),
            archive_sha256=sha256(request.archive_bytes),
            create_request=request.create_request,
            result=request.result,
            package_record=request.package_record,
            archive_base64=base64.b64encode(request.archive_bytes).decode("ascii"),
        )

    def to_request(self) -> DeliveryPersistRequest:
        try:
            archive_bytes = base64.b64decode(self.archive_base64, validate=True)
        except (ValueError, binascii.Error) as error:
            raise PydanticCustomError("delivery_recovery_archive", "delivery recovery archive is invalid") from error
        if (
            self.create_request_sha256 != sha256(canonical_model_bytes(self.create_request))
            or self.result_sha256 != sha256(canonical_model_bytes(self.result))
            or self.package_record_sha256 != sha256(canonical_package_record_bytes(self.package_record))
            or self.archive_sha256 != sha256(archive_bytes)
        ):
            raise PydanticCustomError("delivery_recovery_integrity", "delivery recovery material hashes are invalid")
        request = DeliveryPersistRequest(
            tenant_id=self.result.tenant_id,
            project_id=self.result.project_id,
            create_request=self.create_request,
            result=self.result,
            package_record=self.package_record,
            archive_bytes=archive_bytes,
        )
        if request.idempotency_request_sha256 != self.idempotency_request_sha256:
            raise PydanticCustomError("delivery_recovery_identity", "delivery recovery request identity is invalid")
        return request


class DeliveryIdempotencyRecord(DeliveryPersistenceValue):
    tenant_id: TenantId
    project_id: ProjectId
    request_sha256: Sha256
    idempotency_request_sha256: Sha256
    result_sha256: Sha256
    package_record_sha256: Sha256
    archive_sha256: Sha256
    archive_size_bytes: int = Field(gt=0)
    export_id: ExportId
    delivery_package_id: PackageId
    delivery_export_result_id: ResultId
    delivery_export_request_id: RequestId
    role_handoff_manifest_ids: tuple[RoleManifestId, ...] = Field(strict=False, min_length=1)
    notion_import_manifest_id: NotionManifestId


class DeliveryFailureBoundary(StrEnum):
    SIDECAR_WRITTEN = "sidecar_written"
    ARCHIVE_WRITTEN = "archive_written"
    PACKAGE_RECORD_WRITTEN = "package_record_written"
    RESULT_WRITTEN = "result_written"
    BEFORE_IDEMPOTENCY = "before_idempotency"
    BEFORE_SIDECAR_REMOVAL = "before_sidecar_removal"


def canonical_json_bytes(value: JsonValue) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def canonical_model_bytes(value: BaseModel) -> bytes:
    return canonical_json_bytes(value.model_dump(mode="json"))


def canonical_package_record_bytes(value: DeliveryPackageRecord) -> bytes:
    return canonical_json_bytes(value.model_dump(mode="json", exclude_none=True))


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
