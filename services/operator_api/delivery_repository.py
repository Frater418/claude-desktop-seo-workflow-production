from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from services.delivery.inventory import (
    CanonicalDeliveryRecords,
    DeliveryInventoryRequest,
    SelectedWorkspaceFile,
    WorkspaceRegistration as DeliveryWorkspaceRegistration,
)

from .delivery_repository_io import (
    SelectedArtifactContent,
    _collection,
    _directory,
    _directory_records,
    _json_object,
    _project_v2,
    _record,
    _selected_artifact_files,
)
from .repository_types import WorkspaceRegistry


_REQUIRED_COLLECTIONS: Final = ("artifacts", "gates", "tasks", "assignments")
_OPTIONAL_COLLECTIONS: Final = ("reviews", "blockers", "reports")
_COLLECTION_IDENTIFIERS: Final = MappingProxyType(
    {
        "artifacts": "artifact_id",
        "gates": "quality_gate_run_id",
        "tasks": "task_id",
        "assignments": "assignment_id",
        "reviews": "review_id",
        "blockers": "blocker_id",
        "reports": "report_id",
    }
)


@dataclass(frozen=True, slots=True)
class DeliverySnapshot:
    workspace: DeliveryWorkspaceRegistration
    records: CanonicalDeliveryRecords
    selected_files: tuple[SelectedWorkspaceFile, ...]
    artifact_contents: tuple[SelectedArtifactContent, ...]

    def inventory_request(self, *, include_drafts: bool = False) -> DeliveryInventoryRequest:
        return DeliveryInventoryRequest(self.workspace, self.records, self.selected_files, include_drafts)


class DeliverySnapshotRepository:
    def __init__(self, registry: WorkspaceRegistry) -> None:
        self._registry = registry

    def snapshot(self, tenant_id: str, project_id: str) -> DeliverySnapshot:
        root = self._registry.resolve(tenant_id, project_id)
        v2_root = root / "v2"
        _directory(v2_root, required=True)
        operator_root = v2_root / "operator"
        _directory(operator_root, required=True)
        project_v2 = _project_v2(_json_object(operator_root / "project-v2.json", required=True), tenant_id, project_id)
        workflow = _record(_json_object(operator_root / "workflow.json", required=True), tenant_id, project_id)
        runs = _directory_records(operator_root / "runs", "run_id", tenant_id, project_id, required=True)
        releases = _directory_records(operator_root / "releases", "release_id", tenant_id, project_id, required=False)
        collections = {
            name: _collection(operator_root / f"{name}.json", _COLLECTION_IDENTIFIERS[name], tenant_id, project_id, required=True)
            for name in _REQUIRED_COLLECTIONS
        }
        optional = {
            name: _collection(operator_root / f"{name}.json", _COLLECTION_IDENTIFIERS[name], tenant_id, project_id, required=False)
            for name in _OPTIONAL_COLLECTIONS
        }
        artifacts = collections["artifacts"]
        selected_files, artifact_contents = _selected_artifact_files(root, operator_root, artifacts)
        records = CanonicalDeliveryRecords(
            project_v2=project_v2,
            workflow=workflow,
            runs=runs,
            artifacts=artifacts,
            releases=releases,
            gates=collections["gates"],
            tasks=collections["tasks"],
            assignments=collections["assignments"],
            reviews=optional["reviews"],
            blockers=optional["blockers"],
            reports=optional["reports"],
        )
        return DeliverySnapshot(
            DeliveryWorkspaceRegistration(tenant_id, project_id, root),
            records,
            selected_files,
            artifact_contents,
        )


__all__ = ["DeliverySnapshot", "DeliverySnapshotRepository", "SelectedArtifactContent"]
