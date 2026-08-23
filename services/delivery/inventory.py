from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Final

from .contract_validation import JsonValue
from .record_normalization import CanonicalRecord, DeliveryInventoryError, FrozenJsonValue, normalize, normalize_collection, validate_release_bindings


INITIAL_STEPS: Final = ("0", "1", "1b", "1c", "2", "3", "4a", "4b")
_DELIVERABLES: Final = {"1": ("strategy", "project_management"), "1b": ("architecture", "developer"), "1c": ("design", "developer"), "2": ("keyword-research", "project_management"), "3": ("roadmap", "project_management"), "4a": ("copywriter-handoff", "copywriter"), "4b": ("developer-handoff", "developer")}


@dataclass(frozen=True, slots=True)
class WorkspaceRegistration:
    tenant_id: str
    project_id: str
    workspace_root: Path


@dataclass(frozen=True, slots=True)
class SelectedWorkspaceFile:
    source_path: str
    output_path: str
    source_sha256: str
    artifact_id: str


@dataclass(frozen=True, slots=True)
class CanonicalDeliveryRecords:
    project_v2: Mapping[str, JsonValue]
    workflow: Mapping[str, JsonValue]
    runs: Sequence[Mapping[str, JsonValue]] = ()
    artifacts: Sequence[Mapping[str, JsonValue]] = ()
    releases: Sequence[Mapping[str, JsonValue]] = ()
    gates: Sequence[Mapping[str, JsonValue]] = ()
    tasks: Sequence[Mapping[str, JsonValue]] = ()
    assignments: Sequence[Mapping[str, JsonValue]] = ()
    reviews: Sequence[Mapping[str, JsonValue]] = ()
    blockers: Sequence[Mapping[str, JsonValue]] = ()
    reports: Sequence[Mapping[str, JsonValue]] = ()


@dataclass(frozen=True, slots=True)
class DeliveryInventoryRequest:
    workspace: WorkspaceRegistration
    records: CanonicalDeliveryRecords
    selected_files: Sequence[SelectedWorkspaceFile]
    include_drafts: bool = False


@dataclass(frozen=True, slots=True)
class InventoryFile:
    artifact_id: str
    output_path: str
    content_sha256: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class Deliverable:
    deliverable_id: str
    artifact_id: str
    step_id: str
    role: str
    release_status: str
    output_path: str | None
    content_sha256: str | None


@dataclass(frozen=True, slots=True)
class DeliveryInventory:
    tenant_id: str
    project_id: str
    project_v2: CanonicalRecord
    workflow: CanonicalRecord
    runs: tuple[CanonicalRecord, ...]
    artifacts: tuple[CanonicalRecord, ...]
    releases: tuple[CanonicalRecord, ...]
    gates: tuple[CanonicalRecord, ...]
    tasks: tuple[CanonicalRecord, ...]
    assignments: tuple[CanonicalRecord, ...]
    reviews: tuple[CanonicalRecord, ...]
    blockers: tuple[CanonicalRecord, ...]
    reports: tuple[CanonicalRecord, ...]
    files: tuple[InventoryFile, ...]
    deliverables: tuple[Deliverable, ...]


def collect_inventory(request: DeliveryInventoryRequest) -> DeliveryInventory:
    tenant_id, project_id = request.workspace.tenant_id, request.workspace.project_id
    project, workflow = normalize("project", request.records.project_v2, tenant_id, project_id), normalize("workflow", request.records.workflow, tenant_id, project_id)
    collections = tuple(normalize_collection(kind, values, tenant_id, project_id) for kind, values in (("run", request.records.runs), ("artifact", request.records.artifacts), ("release", request.records.releases), ("gate", request.records.gates), ("task", request.records.tasks), ("assignment", request.records.assignments), ("review", request.records.reviews), ("blocker", request.records.blockers), ("report", request.records.reports)))
    files = _files(request.workspace.workspace_root, request.selected_files, collections[1])
    released = validate_release_bindings(collections[1], collections[2])
    return DeliveryInventory(tenant_id, project_id, project, workflow, collections[0], collections[1], collections[2], collections[3], collections[4], collections[5], collections[6], collections[7], collections[8], files, _deliverables(collections[1], released, files, request.include_drafts))


def _files(root: Path, selected: Sequence[SelectedWorkspaceFile], artifacts: tuple[CanonicalRecord, ...]) -> tuple[InventoryFile, ...]:
    from .path_safety import collect_files
    return collect_files(root, selected, artifacts)


def _deliverables(artifacts: tuple[CanonicalRecord, ...], released: frozenset[str], files: tuple[InventoryFile, ...], include_drafts: bool) -> tuple[Deliverable, ...]:
    outputs = {item.artifact_id: item for item in files}
    rows: list[Deliverable] = []
    for artifact in artifacts:
        if artifact.step_id not in _DELIVERABLES:
            continue
        if artifact.record_id not in released and not include_drafts:
            continue
        deliverable_id, role = _DELIVERABLES[artifact.step_id]
        file = outputs.get(artifact.record_id)
        rows.append(Deliverable(deliverable_id, artifact.record_id, artifact.step_id, role, "released" if artifact.record_id in released else "draft", file.output_path if file else None, artifact.content_sha256))
    return tuple(sorted(rows, key=lambda item: (INITIAL_STEPS.index(item.step_id), item.deliverable_id, item.artifact_id)))


__all__ = ["CanonicalDeliveryRecords", "CanonicalRecord", "DeliveryInventory", "DeliveryInventoryError", "DeliveryInventoryRequest", "Deliverable", "FrozenJsonValue", "InventoryFile", "SelectedWorkspaceFile", "WorkspaceRegistration", "collect_inventory"]
