from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
import hashlib
import json
from typing import Final

from services.delivery.archive import ArchiveBuildRequest, ArchiveEntry, ArchiveIdentity, ArchiveResult, build_archive
from services.delivery.archive_validation import validate_archive
from services.delivery.contract_validation import JsonValue, validate_delivery_contracts
from services.delivery.inventory import DeliveryInventory, collect_inventory
from services.delivery.notion_import import (
    NotionImplementationTask,
    NotionImportBuildContext,
    NotionImportRequest,
    PublicationRegistryRecord,
    build_notion_import_pack,
)
from services.delivery.notion_import_pack import NotionImportPack, plain_json
from services.delivery.policy import DeliveryPolicyResult, evaluate_checkpoint, evaluate_final
from services.delivery.record_normalization import DeliveryInventoryError
from services.delivery.renderers import RenderedRoleFile, render_role_package
from services.delivery.role_packages import RoleHandoffBuildContext, RolePackage, build_role_package

from .delivery_models import (
    DeliveryCreateRequest,
    DeliveryDeliverableResponse,
    DeliveryExportRequest,
    DeliveryExportResult,
    DeliveryManifestReference,
    DeliveryNotionManifestReference,
    DeliveryPackageDeliverable,
    DeliveryPackageRecord,
    DeliveryPolicyErrorResponse,
    DeliveryPreviewResponse,
    DeliveryQualitySummary,
    DeliveryReleaseStatus,
    DeliveryRole,
    DeliveryRolePackageReference,
    DeliveryScope,
    DeliverySourceRecord,
)
from .delivery_repository import DeliverySnapshot


_INTEGRITY_PATHS: Final = ("export-manifest.json", "checksums.sha256")
_SUPPORTED_ROLES: Final = frozenset((DeliveryRole.COPYWRITER, DeliveryRole.DEVELOPER))


class DeliveryCompositionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class DeliveryComposition:
    request: DeliveryCreateRequest
    preview: DeliveryPreviewResponse
    role_packages: tuple[RolePackage, ...]
    notion_pack: NotionImportPack
    archive: ArchiveResult
    package_record: DeliveryPackageRecord
    result: DeliveryExportResult


def preview_delivery(snapshot: DeliverySnapshot, request: DeliveryCreateRequest | DeliveryExportRequest | DeliveryScope) -> DeliveryPreviewResponse:
    """Collect inventory and report scope policy without rendering package output."""
    try:
        if isinstance(request, DeliveryScope):
            inventory = collect_inventory(snapshot.inventory_request())
            return _preview(inventory, _policy(inventory, request))
        export_request = request.export_request if isinstance(request, DeliveryCreateRequest) else request
        inventory = collect_inventory(snapshot.inventory_request(include_drafts=export_request.draft_inclusion_policy.value == "include_explicit_drafts"))
        return _preview(inventory, _policy(inventory, export_request.scope))
    except DeliveryInventoryError as error:
        raise DeliveryCompositionError(error.code, "Delivery composition failed.") from None


def compose_delivery(snapshot: DeliverySnapshot, request: DeliveryCreateRequest) -> DeliveryComposition:
    """Create immutable delivery material entirely in memory from a validated request and snapshot."""
    try:
        inventory = collect_inventory(snapshot.inventory_request(include_drafts=request.export_request.draft_inclusion_policy.value == "include_explicit_drafts"))
        policy = _policy(inventory, request.export_request.scope)
        preview = _preview(inventory, policy)
        if not policy.eligible:
            raise DeliveryCompositionError("DELIVERY_FINAL_POLICY_REJECTED", "Final delivery policy must pass before package composition.")
        role_packages = _role_packages(request, inventory)
        notion_pack = _notion_pack(request, inventory)
        entries = (*_entries(snapshot, inventory, role_packages, notion_pack, policy), ArchiveEntry("project-summary.json", _canonical_bytes({"project_id": inventory.project_id, "source_snapshot_revision": request.export_request.source_snapshot_revision, "tenant_id": inventory.tenant_id})))
        archive = build_archive(
            ArchiveBuildRequest(
                ArchiveIdentity(
                    f"{request.export_request.project_id}-{request.export_request.scope.value}-r{request.package_revision}",
                    request.export_request.tenant_id,
                    request.export_request.project_id,
                    request.export_id,
                    request.delivery_package_id,
                    request.export_request.scope.value,
                    request.package_revision,
                    request.export_request.created_at,
                ),
                entries,
            )
        )
        validate_archive(archive.zip_bytes)
        record = _package_record(request, inventory, role_packages, notion_pack, archive)
        contracts = validate_delivery_contracts(
            record.model_dump(mode="json", exclude_none=True),
            tuple(package.manifest for package in role_packages),
            notion_pack.manifest,
        )
        if not contracts.valid:
            raise DeliveryCompositionError("DELIVERY_CONTRACT_INVALID", "Delivery package manifests fail cross-contract validation.")
        result = _export_result(request, archive, role_packages, notion_pack)
        return DeliveryComposition(request, preview, role_packages, notion_pack, archive, record, result)
    except DeliveryInventoryError as error:
        raise DeliveryCompositionError(error.code, "Delivery composition failed.") from None


def _policy(inventory: DeliveryInventory, scope: DeliveryScope) -> DeliveryPolicyResult:
    match scope:
        case DeliveryScope.CHECKPOINT:
            return evaluate_checkpoint(inventory)
        case DeliveryScope.FINAL:
            return evaluate_final(inventory)


def _preview(inventory: DeliveryInventory, policy: DeliveryPolicyResult) -> DeliveryPreviewResponse:
    return DeliveryPreviewResponse(
        scope=DeliveryScope(policy.scope),
        policy_eligible=policy.eligible,
        missing_deliverable_ids=policy.missing_deliverable_ids,
        errors=tuple(DeliveryPolicyErrorResponse(code=item.code, message=item.message) for item in policy.errors),
        selected_deliverables=tuple(
            DeliveryDeliverableResponse(
                deliverable_id=item.deliverable_id,
                artifact_id=item.artifact_id,
                step_id=item.step_id,
                role=DeliveryRole(item.role),
                release_status=DeliveryReleaseStatus(item.release_status),
                output_path=item.output_path,
                content_sha256=item.content_sha256,
            )
            for item in inventory.deliverables
        ),
    )


def _role_packages(request: DeliveryCreateRequest, inventory: DeliveryInventory) -> tuple[RolePackage, ...]:
    packages: list[RolePackage] = []
    for role_request in request.role_package_requests:
        if role_request.role not in _SUPPORTED_ROLES:
            raise DeliveryCompositionError("ROLE_UNSUPPORTED", "Only copywriter and developer role packages are available.")
        packages.append(
            build_role_package(
                RoleHandoffBuildContext(
                    request.export_id,
                    request.delivery_package_id,
                    request.export_request.source_snapshot_revision,
                    request.export_request.created_at,
                    role_request.role.value,
                    role_request.role_handoff_manifest_id,
                ),
                inventory,
            )
        )
    return tuple(sorted(packages, key=lambda item: item.role))


def _notion_pack(request: DeliveryCreateRequest, inventory: DeliveryInventory) -> NotionImportPack:
    notion = request.notion_import_request
    tasks = tuple(
        NotionImplementationTask(
            item.task_id, item.assignment_id, item.title, item.status, item.comments, item.source_assignee,
            item.priority, item.deadline, item.role.value, item.dependencies, item.artifact_relations, item.notion_user_id,
        )
        for item in notion.implementation_tasks
    )
    registry = PublicationRegistryRecord(
        notion.publication_registry.publication_registry_record_id,
        {
            "publication_registry_record_id": notion.publication_registry.publication_registry_record_id,
            "urls": list(notion.publication_registry.urls),
        },
    )
    return build_notion_import_pack(
        NotionImportRequest(
            NotionImportBuildContext(notion.notion_import_manifest_id, request.export_id, request.delivery_package_id, request.export_request.source_snapshot_revision, request.export_request.created_at, notion.customer_external_id),
            _notion_inventory(inventory),
            tasks,
            registry,
            delivery_safe=True,
        )
    )


def _notion_inventory(inventory: DeliveryInventory) -> DeliveryInventory:
    deliverables = tuple(
        replace(item, role=item.deliverable_id) if item.deliverable_id in {"strategy", "roadmap"} else item
        for item in inventory.deliverables
    )
    return replace(inventory, deliverables=deliverables)


def _entries(snapshot: DeliverySnapshot, inventory: DeliveryInventory, packages: tuple[RolePackage, ...], notion: NotionImportPack, policy: DeliveryPolicyResult) -> tuple[ArchiveEntry, ...]:
    content = {item.artifact_id: item for item in snapshot.artifact_contents}
    source_entries: list[ArchiveEntry] = []
    for deliverable in inventory.deliverables:
        if deliverable.output_path is None or deliverable.content_sha256 is None:
            continue
        item = content.get(deliverable.artifact_id)
        if item is None or item.output_path != deliverable.output_path or item.source_sha256 != deliverable.content_sha256 or hashlib.sha256(item.content).hexdigest() != item.source_sha256:
            raise DeliveryCompositionError("DELIVERY_SOURCE_BINDING_INVALID", "Snapshot artifact bytes do not bind the selected inventory deliverable.")
        source_entries.append(ArchiveEntry(item.output_path, item.content))
    rendered = tuple(file for package in packages for file in render_role_package(package))
    summary = _canonical_bytes({"eligible": policy.eligible, "errors": [item.code for item in policy.errors], "missing_deliverable_ids": list(policy.missing_deliverable_ids), "scope": policy.scope})
    generated = (*_archive_entries(rendered), *(ArchiveEntry(path, data) for path, data in notion.files.items()), ArchiveEntry("quality-reports/summary.json", summary))
    return tuple((*source_entries, *generated))


def _archive_entries(files: tuple[RenderedRoleFile, ...]) -> tuple[ArchiveEntry, ...]:
    return tuple(ArchiveEntry(item.path, item.content) for item in files)


def _package_record(request: DeliveryCreateRequest, inventory: DeliveryInventory, packages: tuple[RolePackage, ...], notion: NotionImportPack, archive: ArchiveResult) -> DeliveryPackageRecord:
    paths = tuple(sorted((*tuple(item.relative_path for item in archive.manifest.files), *_INTEGRITY_PATHS)))
    role_refs = tuple(
        DeliveryRolePackageReference(role=DeliveryRole(package.role), role_handoff_manifest_id=package.handoff_manifest.context.role_handoff_manifest_id, manifest_path=f"{package.role}-handoff/role-handoff-manifest.json", manifest_sha256=package.handoff_manifest.manifest_sha256)
        for package in packages
    )
    notion_manifest = notion.manifest
    quality_path = "quality-reports/summary.json"
    return DeliveryPackageRecord(
        delivery_package_id=request.delivery_package_id, schema_version="1.0.0", tenant_id=inventory.tenant_id, project_id=inventory.project_id, export_id=request.export_id, scope=request.export_request.scope, source_snapshot_revision=request.export_request.source_snapshot_revision,
        source_records=_source_records(inventory, request.export_request.source_snapshot_revision),
        required_deliverables=tuple(DeliveryPackageDeliverable(deliverable_id=item.deliverable_id, source_record_id=item.artifact_id, source_sha256=item.content_sha256, package_path=item.output_path, release_status=DeliveryReleaseStatus(item.release_status)) for item in inventory.deliverables if item.output_path is not None and item.content_sha256 is not None),
        missing_deliverables=_policy(inventory, request.export_request.scope).missing_deliverable_ids, package_paths=paths, package_sha256=archive.package_sha256, zip_sha256=archive.zip_sha256, role_packages=role_refs,
        notion_import_manifest=DeliveryNotionManifestReference(notion_import_manifest_id=request.notion_import_request.notion_import_manifest_id, manifest_path="notion-import/notion-import-manifest.json", manifest_sha256=str(notion_manifest["manifest_sha256"])), created_at=request.export_request.created_at, package_revision=request.package_revision, derived_status="archived",
        task_assignment_manifest_path="notion-import/tasks.csv" if request.export_request.scope is DeliveryScope.FINAL else None, quality_summary=DeliveryQualitySummary(summary_path=quality_path, content_sha256=_archive_hash(archive, quality_path)) if request.export_request.scope is DeliveryScope.FINAL else None, export_manifest_path="export-manifest.json" if request.export_request.scope is DeliveryScope.FINAL else None, checksums_path="checksums.sha256" if request.export_request.scope is DeliveryScope.FINAL else None,
    )


def _source_records(inventory: DeliveryInventory, snapshot_revision: int) -> tuple[DeliverySourceRecord, ...]:
    records = (("project", inventory.project_v2), *((item.kind, item) for values in (inventory.runs, inventory.artifacts, inventory.releases) for item in values))
    return tuple(DeliverySourceRecord(tenant_id=inventory.tenant_id, project_id=inventory.project_id, source_kind=kind, source_record_id=item.record_id, source_revision=snapshot_revision, source_sha256=_hash_payload(item.payload)) for kind, item in records)


def _export_result(request: DeliveryCreateRequest, archive: ArchiveResult, packages: tuple[RolePackage, ...], notion: NotionImportPack) -> DeliveryExportResult:
    role_manifests = tuple(DeliveryManifestReference(manifest_id=package.handoff_manifest.context.role_handoff_manifest_id, relative_path=f"{package.role}-handoff/role-handoff-manifest.json", content_sha256=_hash_role_manifest(package)) for package in packages)
    return DeliveryExportResult(delivery_export_result_id=request.delivery_export_result_id, schema_version="1.0.0", tenant_id=request.export_request.tenant_id, project_id=request.export_request.project_id, delivery_export_request_id=request.export_request.delivery_export_request_id, export_id=request.export_id, delivery_package_id=request.delivery_package_id, source_snapshot_revision=request.export_request.source_snapshot_revision, replay_state="created", export_path=f"delivery/exports/{request.export_id}", zip_path=f"delivery/exports/{request.export_id}/archive.zip", package_sha256=archive.package_sha256, zip_sha256=archive.zip_sha256, zip_size_bytes=len(archive.zip_bytes), delivery_manifest=DeliveryManifestReference(manifest_id=request.delivery_package_id, relative_path="export-manifest.json", content_sha256=hashlib.sha256(archive.manifest_bytes).hexdigest()), role_handoff_manifests=role_manifests, notion_import_manifest=DeliveryManifestReference(manifest_id=request.notion_import_request.notion_import_manifest_id, relative_path="notion-import/notion-import-manifest.json", content_sha256=hashlib.sha256(notion.files["notion-import/notion-import-manifest.json"]).hexdigest()), created_at=request.export_request.created_at)


def _hash_role_manifest(package: RolePackage) -> str:
    return hashlib.sha256(next(item.content for item in render_role_package(package) if item.path.endswith("role-handoff-manifest.json"))).hexdigest()


def _archive_hash(archive: ArchiveResult, path: str) -> str:
    return next(item.sha256 for item in archive.manifest.files if item.relative_path == path)


def _hash_payload(payload: Mapping[str, JsonValue]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _canonical_bytes(value: Mapping[str, JsonValue]) -> bytes:
    return json.dumps(plain_json(value), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


__all__ = ["DeliveryComposition", "DeliveryCompositionError", "compose_delivery", "preview_delivery"]
