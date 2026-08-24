from __future__ import annotations

from datetime import datetime
from enum import StrEnum
import re
from typing import Annotated, Literal, TypeAlias

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError


TenantId: TypeAlias = Annotated[str, Field(pattern=r"^tenant-[a-z0-9][a-z0-9-]{2,63}$")]
ProjectId: TypeAlias = Annotated[str, Field(pattern=r"^project-[a-z0-9][a-z0-9-]{2,63}$")]
ExportId: TypeAlias = Annotated[str, Field(pattern=r"^delivery-export-[a-z0-9][a-z0-9-]{7,63}$")]
RequestId: TypeAlias = Annotated[str, Field(pattern=r"^delivery-export-request-[a-z0-9][a-z0-9-]{7,63}$")]
ResultId: TypeAlias = Annotated[str, Field(pattern=r"^delivery-export-result-[a-z0-9][a-z0-9-]{7,63}$")]
PackageId: TypeAlias = Annotated[str, Field(pattern=r"^delivery-package-[a-z0-9][a-z0-9-]{7,63}$")]
RoleManifestId: TypeAlias = Annotated[str, Field(pattern=r"^role-handoff-[a-z0-9][a-z0-9-]{7,63}$")]
NotionManifestId: TypeAlias = Annotated[str, Field(pattern=r"^notion-import-[a-z0-9][a-z0-9-]{7,63}$")]
Sha256: TypeAlias = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Timestamp: TypeAlias = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")]
PositiveRevision: TypeAlias = Annotated[int, Field(strict=True, ge=1)]


def _require_safe_path(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", value) is None or "//" in value or any(part in {".", ".."} for part in value.split("/")):
        raise PydanticCustomError("delivery_safe_path", "value must be a safe relative path")
    return value


SafePath: TypeAlias = Annotated[str, AfterValidator(_require_safe_path)]


class DeliveryScope(StrEnum):
    CHECKPOINT = "checkpoint"
    FINAL = "final"


class DeliveryDraftPolicy(StrEnum):
    EXCLUDE_DRAFTS = "exclude_drafts"
    INCLUDE_EXPLICIT_DRAFTS = "include_explicit_drafts"


class DeliveryRole(StrEnum):
    COPYWRITER = "copywriter"
    DEVELOPER = "developer"
    PROJECT_MANAGEMENT = "project_management"
    REVIEWER = "reviewer"


class DeliveryReleaseStatus(StrEnum):
    RELEASED = "released"
    DRAFT = "draft"


class DeliveryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    @field_validator("created_at", check_fields=False)
    @classmethod
    def require_aware_rfc3339_timestamp(cls, value: str) -> str:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise PydanticCustomError("delivery_timestamp", "created_at must be a valid RFC3339 timestamp") from error
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise PydanticCustomError("delivery_timestamp", "created_at must include a timezone offset")
        return value


class DeliveryExportRequest(DeliveryModel):
    delivery_export_request_id: RequestId
    schema_version: Literal["1.0.0"]
    tenant_id: TenantId
    project_id: ProjectId
    scope: DeliveryScope = Field(strict=False)
    draft_inclusion_policy: DeliveryDraftPolicy = Field(strict=False)
    idempotency_key: Annotated[str, Field(pattern=r"^idem-[a-z0-9][a-z0-9-]{7,127}$")]
    created_at: Timestamp
    source_snapshot_revision: PositiveRevision
    requested_role_packages: tuple[Annotated[DeliveryRole, Field(strict=False)], ...] = Field(strict=False, min_length=1)

    @model_validator(mode="after")
    def require_valid_scope_policy_and_roles(self) -> DeliveryExportRequest:
        if self.scope is DeliveryScope.FINAL and self.draft_inclusion_policy is not DeliveryDraftPolicy.EXCLUDE_DRAFTS:
            raise ValueError("final delivery requires exclude_drafts")
        if len(set(self.requested_role_packages)) != len(self.requested_role_packages):
            raise ValueError("requested role packages must be unique")
        return self.model_copy(
            update={"requested_role_packages": tuple(sorted(self.requested_role_packages, key=lambda role: role.value))}
        )


class DeliveryRolePackageRequest(DeliveryModel):
    role: DeliveryRole = Field(strict=False)
    role_handoff_manifest_id: RoleManifestId


class DeliveryImplementationTask(DeliveryModel):
    task_id: Annotated[str, Field(pattern=r"^task-[a-z0-9][a-z0-9-]{7,63}$")]
    assignment_id: Annotated[str, Field(pattern=r"^assignment-[a-z0-9][a-z0-9-]{7,63}$")]
    title: Annotated[str, Field(min_length=1)]
    status: Literal["not_started", "in_progress", "blocked", "done"]
    comments: str
    source_assignee: str
    priority: Literal["low", "medium", "high"]
    deadline: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
    role: DeliveryRole = Field(strict=False)
    dependencies: tuple[Annotated[str, Field(pattern=r"^task-[a-z0-9][a-z0-9-]{7,63}$")], ...] = Field(strict=False)
    artifact_relations: tuple[Annotated[str, Field(pattern=r"^artifact-[a-z0-9][a-z0-9-]{7,63}$")], ...] = Field(strict=False)
    notion_user_id: Annotated[str, Field(pattern=r"^notion-user-[a-z0-9][a-z0-9-]{7,63}$")] | None = None

    @field_validator("deadline")
    @classmethod
    def require_rfc3339_date(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as error:
            raise PydanticCustomError("delivery_date", "deadline must be a valid RFC3339 date") from error
        return value

    @model_validator(mode="after")
    def require_unique_relations(self) -> DeliveryImplementationTask:
        if len(set(self.dependencies)) != len(self.dependencies) or len(set(self.artifact_relations)) != len(self.artifact_relations):
            raise ValueError("implementation task relations must be unique")
        return self


class DeliveryPublicationRegistry(DeliveryModel):
    publication_registry_record_id: Annotated[str, Field(pattern=r"^publication-registry-[a-z0-9][a-z0-9-]{2,63}$")]
    urls: tuple[Annotated[str, Field(pattern=r"^https://")], ...] = Field(strict=False, min_length=1)


class DeliveryNotionRequest(DeliveryModel):
    notion_import_manifest_id: NotionManifestId
    customer_external_id: Annotated[str, Field(pattern=r"^customer-[a-z0-9][a-z0-9-]{2,63}$")]
    implementation_tasks: tuple[DeliveryImplementationTask, ...] = Field(strict=False, min_length=1)
    publication_registry: DeliveryPublicationRegistry

    @model_validator(mode="after")
    def require_unique_task_and_assignment_ids(self) -> DeliveryNotionRequest:
        identities = tuple(item.task_id for item in self.implementation_tasks) + tuple(item.assignment_id for item in self.implementation_tasks)
        if len(set(identities)) != len(identities):
            raise ValueError("implementation task and assignment IDs must be unique")
        return self


class DeliveryCreateRequest(DeliveryModel):
    export_request: DeliveryExportRequest
    export_id: ExportId
    delivery_package_id: PackageId
    delivery_export_result_id: ResultId
    package_revision: PositiveRevision
    role_package_requests: tuple[DeliveryRolePackageRequest, ...] = Field(strict=False, min_length=1)
    notion_import_request: DeliveryNotionRequest

    @model_validator(mode="after")
    def require_role_package_correspondence(self) -> DeliveryCreateRequest:
        requested = set(self.export_request.requested_role_packages)
        provided = tuple(item.role for item in self.role_package_requests)
        manifest_ids = tuple(item.role_handoff_manifest_id for item in self.role_package_requests)
        if len(set(provided)) != len(provided) or len(set(manifest_ids)) != len(manifest_ids) or set(provided) != requested:
            raise ValueError("role package requests must exactly match requested role packages")
        return self.model_copy(
            update={"role_package_requests": tuple(sorted(self.role_package_requests, key=lambda request: request.role.value))}
        )


class DeliveryPolicyErrorResponse(DeliveryModel):
    code: str
    message: str


class DeliveryDeliverableResponse(DeliveryModel):
    deliverable_id: Literal["strategy", "architecture", "design", "keyword-research", "roadmap", "copywriter-handoff", "developer-handoff"]
    artifact_id: Annotated[str, Field(pattern=r"^artifact-[a-z0-9][a-z0-9-]{7,63}$")]
    step_id: Literal["1", "1b", "1c", "2", "3", "4a", "4b"]
    role: DeliveryRole = Field(strict=False)
    release_status: DeliveryReleaseStatus = Field(strict=False)
    output_path: SafePath | None
    content_sha256: Sha256 | None


class DeliveryPreviewResponse(DeliveryModel):
    scope: DeliveryScope = Field(strict=False)
    policy_eligible: bool
    missing_deliverable_ids: tuple[Literal["strategy", "architecture", "design", "keyword-research", "roadmap", "copywriter-handoff", "developer-handoff"], ...] = Field(strict=False)
    errors: tuple[DeliveryPolicyErrorResponse, ...] = Field(strict=False)
    selected_deliverables: tuple[DeliveryDeliverableResponse, ...] = Field(strict=False)


class DeliveryManifestReference(DeliveryModel):
    manifest_id: Annotated[str, Field(pattern=r"^(?:role-handoff|notion-import|delivery-package)-[a-z0-9][a-z0-9-]{7,63}$")]
    relative_path: SafePath
    content_sha256: Sha256


class DeliveryRolePackageReference(DeliveryModel):
    role: DeliveryRole = Field(strict=False)
    role_handoff_manifest_id: RoleManifestId
    manifest_path: SafePath
    manifest_sha256: Sha256


class DeliveryNotionManifestReference(DeliveryModel):
    notion_import_manifest_id: NotionManifestId
    manifest_path: SafePath
    manifest_sha256: Sha256


class DeliverySourceRecord(DeliveryModel):
    tenant_id: TenantId
    project_id: ProjectId
    source_kind: Literal["project", "workflow", "run", "artifact", "release", "task", "assignment", "review", "approval", "blocker", "report"]
    source_record_id: Annotated[str, Field(pattern=r"^(?:project|run|artifact|release|task|assignment|review|approval|blocker|report)-[a-z0-9][a-z0-9-]{2,63}$")]
    source_revision: PositiveRevision
    source_sha256: Sha256


class DeliveryPackageDeliverable(DeliveryModel):
    deliverable_id: Literal["strategy", "architecture", "design", "keyword-research", "roadmap", "copywriter-handoff", "developer-handoff"]
    source_record_id: Annotated[str, Field(pattern=r"^artifact-[a-z0-9][a-z0-9-]{7,63}$")]
    source_sha256: Sha256
    package_path: SafePath
    release_status: DeliveryReleaseStatus = Field(strict=False)


class DeliveryQualitySummary(DeliveryModel):
    summary_path: SafePath
    content_sha256: Sha256


class DeliveryPackageRecord(DeliveryModel):
    delivery_package_id: PackageId
    schema_version: Literal["1.0.0"]
    tenant_id: TenantId
    project_id: ProjectId
    export_id: ExportId
    scope: DeliveryScope = Field(strict=False)
    source_snapshot_revision: PositiveRevision
    source_records: tuple[DeliverySourceRecord, ...] = Field(strict=False, min_length=1)
    required_deliverables: tuple[DeliveryPackageDeliverable, ...] = Field(strict=False, min_length=1)
    missing_deliverables: tuple[Literal["strategy", "architecture", "design", "keyword-research", "roadmap", "copywriter-handoff", "developer-handoff"], ...] = Field(strict=False)
    package_paths: tuple[SafePath, ...] = Field(strict=False, min_length=1)
    package_sha256: Sha256
    zip_sha256: Sha256
    role_packages: tuple[DeliveryRolePackageReference, ...] = Field(strict=False, min_length=1)
    notion_import_manifest: DeliveryNotionManifestReference
    created_at: Timestamp
    package_revision: PositiveRevision
    derived_status: Literal["prepared", "archived"]
    task_assignment_manifest_path: SafePath | None = None
    quality_summary: DeliveryQualitySummary | None = None
    export_manifest_path: SafePath | None = None
    checksums_path: SafePath | None = None

    @model_validator(mode="after")
    def require_unique_and_final_complete(self) -> DeliveryPackageRecord:
        if len(set(self.package_paths)) != len(self.package_paths) or len({item.source_record_id for item in self.source_records}) != len(self.source_records) or len({item.deliverable_id for item in self.required_deliverables}) != len(self.required_deliverables) or len({item.role for item in self.role_packages}) != len(self.role_packages):
            raise ValueError("delivery package records require unique source, deliverable, path, and role entries")
        if self.scope is DeliveryScope.FINAL:
            required = frozenset(("strategy", "architecture", "design", "keyword-research", "roadmap", "copywriter-handoff", "developer-handoff"))
            paths = (self.task_assignment_manifest_path, self.quality_summary, self.export_manifest_path, self.checksums_path)
            if self.missing_deliverables or {item.deliverable_id for item in self.required_deliverables} != required or any(item.release_status is not DeliveryReleaseStatus.RELEASED for item in self.required_deliverables) or {item.role for item in self.role_packages} < {DeliveryRole.COPYWRITER, DeliveryRole.DEVELOPER} or any(path is None for path in paths):
                raise ValueError("final package record is incomplete")
        return self


class DeliveryExportResult(DeliveryModel):
    delivery_export_result_id: ResultId
    schema_version: Literal["1.0.0"]
    tenant_id: TenantId
    project_id: ProjectId
    delivery_export_request_id: RequestId
    export_id: ExportId
    delivery_package_id: PackageId
    source_snapshot_revision: PositiveRevision
    replay_state: Literal["created", "replayed"]
    export_path: SafePath
    zip_path: SafePath
    package_sha256: Sha256
    zip_sha256: Sha256
    zip_size_bytes: PositiveRevision
    delivery_manifest: DeliveryManifestReference
    role_handoff_manifests: tuple[DeliveryManifestReference, ...] = Field(strict=False, min_length=1)
    notion_import_manifest: DeliveryManifestReference
    created_at: Timestamp

    @model_validator(mode="after")
    def require_unique_role_manifest_references(self) -> DeliveryExportResult:
        if len({item.manifest_id for item in self.role_handoff_manifests}) != len(self.role_handoff_manifests):
            raise ValueError("role handoff manifest references must be unique")
        return self


class DeliveryExportHistoryResponse(DeliveryModel):
    data: tuple[DeliveryExportResult, ...] = Field(strict=False)
