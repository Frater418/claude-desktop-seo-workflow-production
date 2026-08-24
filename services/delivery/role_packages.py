from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Final

from jsonschema import Draft202012Validator, FormatChecker

from .contract_validation import JsonValue
from .inventory import Deliverable, DeliveryInventory, InventoryFile
from .record_normalization import CanonicalRecord, DeliveryInventoryError, FrozenJsonValue


_ROLE_STEPS: Final = {"copywriter": ("2", "3", "4a"), "developer": ("1b", "1c", "3", "4b")}
MANIFEST_HASH_RULE: Final = "sha256 of UTF-8 canonical JSON with manifest_sha256 omitted"
_SCHEMA: Final = json.loads((Path(__file__).resolve().parents[2] / "standards" / "delivery" / "role-handoff-manifest.schema.json").read_text(encoding="utf-8"))
_VALIDATOR: Final = Draft202012Validator(_SCHEMA, format_checker=FormatChecker())


@dataclass(frozen=True, slots=True)
class RoleHandoffBuildContext:
    export_id: str
    delivery_package_id: str
    source_snapshot_revision: int
    created_at: str
    role: str
    role_handoff_manifest_id: str


@dataclass(frozen=True, slots=True)
class RoleArtifactReference:
    artifact_id: str
    step_id: str
    release_status: str
    output_path: str
    content_sha256: str


@dataclass(frozen=True, slots=True)
class RoleSourceRecord:
    tenant_id: str
    project_id: str
    source_record_id: str
    source_sha256: str

    def to_json(self) -> dict[str, str]:
        return {"tenant_id": self.tenant_id, "project_id": self.project_id, "source_record_id": self.source_record_id, "source_sha256": self.source_sha256}


@dataclass(frozen=True, slots=True)
class RoleHandoffManifest:
    context: RoleHandoffBuildContext
    tenant_id: str
    project_id: str
    source_records: tuple[RoleSourceRecord, ...]
    included_paths: tuple[str, ...]
    unresolved_assignee_ids: tuple[str, ...]
    manifest_sha256: str

    def to_json(self, include_hash: bool = True) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "role_handoff_manifest_id": self.context.role_handoff_manifest_id,
            "schema_version": "1.0.0",
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "export_id": self.context.export_id,
            "delivery_package_id": self.context.delivery_package_id,
            "role": self.context.role,
            "handoff_mode": "manual_package",
            "source_snapshot_revision": self.context.source_snapshot_revision,
            "source_records": [item.to_json() for item in self.source_records],
            "included_paths": list(self.included_paths),
            "unresolved_assignee_ids": list(self.unresolved_assignee_ids),
            "created_at": self.context.created_at,
        }
        if include_hash:
            value["manifest_sha256"] = self.manifest_sha256
        return value


@dataclass(frozen=True, slots=True)
class RolePackage:
    role: str
    artifacts: tuple[RoleArtifactReference, ...]
    tasks: tuple[CanonicalRecord, ...]
    assignments: tuple[CanonicalRecord, ...]
    reviews: tuple[CanonicalRecord, ...]
    blockers: tuple[CanonicalRecord, ...]
    handoff_manifest: RoleHandoffManifest

    @property
    def manifest(self) -> dict[str, JsonValue]:
        return self.handoff_manifest.to_json()


def build_role_package(context: RoleHandoffBuildContext, inventory: DeliveryInventory) -> RolePackage:
    steps = _steps(context.role)
    artifacts = _artifacts(inventory, steps)
    if not artifacts:
        raise DeliveryInventoryError("ROLE_PACKAGE_EMPTY", "No selected canonical artifacts are available for the requested role.")
    task_by_id = {item.record_id: item for item in inventory.tasks}
    assignments = _assignments(inventory.assignments, context.role, task_by_id)
    tasks = _assigned_tasks(assignments, task_by_id)
    selected_artifact_ids = frozenset(item.artifact_id for item in artifacts)
    selected_task_ids = frozenset(item.record_id for item in tasks)
    reviews = _related(inventory.reviews, selected_artifact_ids, selected_task_ids, context.role)
    blockers = _related(inventory.blockers, selected_artifact_ids, selected_task_ids, context.role)
    records = _sources(inventory.tenant_id, inventory.project_id, artifacts, tasks, assignments, reviews, blockers)
    paths = tuple(sorted(item.output_path for item in artifacts))
    unresolved = tuple(item.record_id for item in assignments if _text(item.payload, "assignee_id") is None)
    blank = RoleHandoffManifest(context, inventory.tenant_id, inventory.project_id, records, paths, unresolved, "")
    digest = hashlib.sha256(_canonical_bytes(blank.to_json(include_hash=False))).hexdigest()
    manifest = RoleHandoffManifest(context, inventory.tenant_id, inventory.project_id, records, paths, unresolved, digest)
    errors = tuple(_VALIDATOR.iter_errors(manifest.to_json()))
    if errors:
        raise DeliveryInventoryError("ROLE_MANIFEST_INVALID", "Derived role handoff manifest violates its schema.")
    return RolePackage(context.role, artifacts, tasks, assignments, reviews, blockers, manifest)


def _steps(role: str) -> tuple[str, ...]:
    steps = _ROLE_STEPS.get(role)
    if steps is None:
        raise DeliveryInventoryError("ROLE_UNSUPPORTED", "Only copywriter and developer role packages are supported.")
    return steps


def _artifacts(inventory: DeliveryInventory, steps: tuple[str, ...]) -> tuple[RoleArtifactReference, ...]:
    selected = tuple(item for item in inventory.deliverables if item.step_id in steps and item.output_path is not None)
    artifacts = {item.record_id: item for item in inventory.artifacts}
    rows = tuple(_artifact_reference(item, inventory.files, artifacts) for item in selected)
    if len({item.output_path for item in rows}) != len(rows) or len({item.artifact_id for item in rows}) != len(rows):
        raise DeliveryInventoryError("ROLE_DELIVERABLE_DUPLICATE", "Role package deliverable bindings must be unique.")
    if any(not _safe_path(item.output_path) for item in rows):
        raise DeliveryInventoryError("ROLE_OUTPUT_PATH_INVALID", "Role package artifact paths must be safe relative POSIX paths.")
    return tuple(sorted(rows, key=lambda item: (steps.index(item.step_id), item.output_path, item.artifact_id)))


def _artifact_reference(deliverable: Deliverable, files: tuple[InventoryFile, ...], artifacts: Mapping[str, CanonicalRecord]) -> RoleArtifactReference:
    artifact_id = deliverable.artifact_id
    artifact = artifacts.get(artifact_id)
    if artifact is None:
        raise DeliveryInventoryError("ROLE_DELIVERABLE_ARTIFACT_UNKNOWN", "Selected deliverable references an unknown canonical artifact.")
    if artifact.step_id != deliverable.step_id or artifact.content_sha256 != deliverable.content_sha256:
        raise DeliveryInventoryError("ROLE_DELIVERABLE_ARTIFACT_MISMATCH", "Selected deliverable does not bind its canonical artifact.")
    bound = tuple(item for item in files if item.artifact_id == artifact_id)
    if not bound:
        raise DeliveryInventoryError("ROLE_DELIVERABLE_FILE_MISSING", "Selected deliverable has no selected artifact file.")
    if len(bound) != 1:
        raise DeliveryInventoryError("ROLE_DELIVERABLE_FILE_DUPLICATE", "Selected deliverable has multiple selected artifact files.")
    file = bound[0]
    if file.output_path != deliverable.output_path:
        raise DeliveryInventoryError("ROLE_DELIVERABLE_FILE_PATH_MISMATCH", "Selected file path does not bind the deliverable.")
    if file.content_sha256 != deliverable.content_sha256:
        raise DeliveryInventoryError("ROLE_DELIVERABLE_FILE_HASH_MISMATCH", "Selected file hash does not bind the deliverable.")
    return RoleArtifactReference(artifact_id, deliverable.step_id, deliverable.release_status, file.output_path, file.content_sha256)


def _assignments(assignments: tuple[CanonicalRecord, ...], role: str, tasks: Mapping[str, CanonicalRecord]) -> tuple[CanonicalRecord, ...]:
    selected: list[CanonicalRecord] = []
    for item in assignments:
        assigned_role = _assignment_role(item)
        if assigned_role != role:
            continue
        task_id = _text(item.payload, "task_id")
        if task_id is None or task_id not in tasks:
            raise DeliveryInventoryError("ROLE_ASSIGNMENT_TASK_DANGLING", "Role assignment must reference an existing canonical task.")
        selected.append(item)
    return tuple(sorted(selected, key=lambda item: item.record_id))


def _assigned_tasks(assignments: tuple[CanonicalRecord, ...], tasks: Mapping[str, CanonicalRecord]) -> tuple[CanonicalRecord, ...]:
    selected: dict[str, CanonicalRecord] = {}
    for assignment in assignments:
        task_id = _text(assignment.payload, "task_id")
        if task_id is None:
            raise DeliveryInventoryError("ROLE_ASSIGNMENT_TASK_DANGLING", "Role assignment must reference an existing canonical task.")
        selected[task_id] = tasks[task_id]
    return tuple(sorted(selected.values(), key=lambda item: item.record_id))


def _related(records: tuple[CanonicalRecord, ...], artifact_ids: frozenset[str], task_ids: frozenset[str], role: str) -> tuple[CanonicalRecord, ...]:
    return tuple(item for item in records if _references(item.payload, artifact_ids, task_ids, role))


def _references(payload: Mapping[str, FrozenJsonValue], artifact_ids: frozenset[str], task_ids: frozenset[str], role: str) -> bool:
    artifact = _text(payload, "artifact_id")
    nested = payload.get("artifact")
    nested_artifact = nested.get("artifact_id") if isinstance(nested, Mapping) else None
    artifacts = frozenset(item for item in (artifact, nested_artifact) if isinstance(item, str))
    tasks = frozenset(item for item in (_text(payload, "task_id"),) if isinstance(item, str))
    if artifacts or tasks:
        return artifacts.issubset(artifact_ids) and tasks.issubset(task_ids)
    return _text(payload, "role") == role or _text(payload, "assigned_role") == role


def _sources(tenant_id: str, project_id: str, artifacts: tuple[RoleArtifactReference, ...], *collections: tuple[CanonicalRecord, ...]) -> tuple[RoleSourceRecord, ...]:
    rows = [RoleSourceRecord(tenant_id, project_id, item.artifact_id, item.content_sha256) for item in artifacts]
    rows.extend(RoleSourceRecord(tenant_id, project_id, item.record_id, hashlib.sha256(_canonical_bytes(_json_value(item.payload))).hexdigest()) for collection in collections for item in collection)
    by_id: dict[str, RoleSourceRecord] = {}
    for item in rows:
        existing = by_id.get(item.source_record_id)
        if existing is not None and existing.source_sha256 != item.source_sha256:
            raise DeliveryInventoryError("ROLE_SOURCE_ID_CONFLICT", "One source record identity has conflicting content hashes.")
        by_id[item.source_record_id] = item
    return tuple(sorted(by_id.values(), key=lambda item: item.source_record_id))


def _json_value(value: FrozenJsonValue) -> JsonValue:
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value


def _canonical_bytes(value: JsonValue) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _text(payload: Mapping[str, FrozenJsonValue], name: str) -> str | None:
    value = payload.get(name)
    return value if isinstance(value, str) and value else None


def _assignment_role(record: CanonicalRecord) -> str | None:
    assigned_role = _text(record.payload, "assigned_role")
    role = _text(record.payload, "role")
    if assigned_role is not None and role is not None and assigned_role != role:
        raise DeliveryInventoryError("ROLE_ASSIGNMENT_ROLE_CONFLICT", "Assignment role fields conflict.")
    return assigned_role or role


def _safe_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and "\\" not in value and not value.lower().startswith("file:")


__all__ = ["MANIFEST_HASH_RULE", "RoleArtifactReference", "RoleHandoffBuildContext", "RoleHandoffManifest", "RolePackage", "RoleSourceRecord", "build_role_package"]
