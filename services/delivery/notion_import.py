from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Final
import re

from jsonschema import Draft202012Validator, FormatChecker

from .contract_validation import JsonValue, validate_delivery_contracts
from .inventory import DeliveryInventory
from .notion_import_pack import NotionImportPack, complete_json_bytes, manifest_preimage_bytes, plain_json
from .notion_import_renderers import CSV_HEADERS, RenderedNotionImportFile, import_order, property_mapping, render_csv, user_mapping
from .record_normalization import CanonicalRecord, DeliveryInventoryError
from .notion_import_security import assert_no_credentials


_SCHEMA: Final = json.loads((Path(__file__).resolve().parents[2] / "standards" / "delivery" / "notion-import-manifest.schema.json").read_text(encoding="utf-8"))
_VALIDATOR: Final = Draft202012Validator(_SCHEMA, format_checker=FormatChecker())
_ROLES: Final = {"strategy": "strategy", "architecture": "architecture", "roadmap": "roadmap", "copywriter": "copywriter", "developer": "developer", "project_management": "concept", "concept": "concept"}
_NOTION_USER_ID: Final = re.compile(r"^notion-user-[a-z0-9][a-z0-9-]{7,63}$")


@dataclass(frozen=True, slots=True)
class NotionImportBuildContext:
    notion_import_manifest_id: str
    export_id: str
    delivery_package_id: str
    source_snapshot_revision: int
    created_at: str
    customer_external_id: str


@dataclass(frozen=True, slots=True)
class NotionImplementationTask:
    task_id: str
    assignment_id: str
    title: str
    status: str
    comments: str
    source_assignee: str
    priority: str
    deadline: str
    role: str
    dependencies: tuple[str, ...]
    artifact_relations: tuple[str, ...] = ()
    notion_user_id: str | None = None


@dataclass(frozen=True, slots=True)
class PublicationRegistryRecord:
    record_id: str
    payload: Mapping[str, JsonValue]


@dataclass(frozen=True, slots=True)
class NotionImportRequest:
    context: NotionImportBuildContext
    inventory: DeliveryInventory
    implementation_tasks: tuple[NotionImplementationTask, ...]
    publication_registry: PublicationRegistryRecord
    delivery_safe: bool = False


def build_notion_import_pack(request: NotionImportRequest) -> NotionImportPack:
    inventory, context = request.inventory, request.context
    artifacts = _artifacts(inventory)
    tasks = _ordered_tasks(request.implementation_tasks)
    implementation = _implementation_rows(tasks, inventory.tenant_id, inventory.project_id)
    history = _history_rows(inventory.tasks, inventory.tenant_id, inventory.project_id)
    reviews, blockers = _core_rows(inventory.reviews, inventory.blockers, inventory.project_id, artifacts)
    approvals = _approvals(inventory, artifacts)
    rows = _rows(inventory, context, artifacts, history, implementation, tasks, reviews, approvals, blockers, request.publication_registry)
    rendered = _render(rows, request.delivery_safe)
    manifest = _manifest(inventory, context, rows, rendered)
    _validate(inventory, manifest)
    all_files = {item.path: item.content for item in rendered}
    all_files["notion-import/notion-import-manifest.json"] = complete_json_bytes(manifest)
    assert_no_credentials(all_files)
    return NotionImportPack(manifest, all_files)


def _artifacts(inventory: DeliveryInventory) -> tuple[dict[str, JsonValue], ...]:
    by_id = {item.record_id: item for item in inventory.artifacts}
    files = {item.artifact_id: item for item in inventory.files}
    releases = {str(item.payload.get("artifact_id")): item for item in inventory.releases}
    rows: list[dict[str, JsonValue]] = []
    for item in sorted(inventory.deliverables, key=lambda value: value.artifact_id):
        artifact, file, release = by_id.get(item.artifact_id), files.get(item.artifact_id), releases.get(item.artifact_id)
        if item.release_status != "released":
            raise DeliveryInventoryError("NOTION_ARTIFACT_NOT_RELEASED", "Draft artifacts cannot be exported as released concepts.")
        if artifact is None or file is None or release is None or item.output_path != file.output_path or item.content_sha256 != file.content_sha256:
            raise DeliveryInventoryError("NOTION_RELEASE_BINDING_INVALID", "Released artifact binding is incomplete or mismatched.")
        if release.payload.get("artifact_sha256") != artifact.content_sha256:
            raise DeliveryInventoryError("NOTION_RELEASE_BINDING_INVALID", "Release hash does not bind its canonical artifact.")
        role = _ROLES.get(item.role)
        if role is None:
            raise DeliveryInventoryError("NOTION_ARTIFACT_ROLE_INVALID", "Artifact deliverable role is unsupported by the closed schema.")
        rows.append({"external_id": artifact.record_id, "project_external_id": inventory.project_id, "tenant_id": inventory.tenant_id, "project_id": inventory.project_id, "content_sha256": artifact.content_sha256 or "", "revision": artifact.revision or 0, "relative_path": file.output_path, "role": role, "read_only": True})
    if len(rows) < 5:
        raise DeliveryInventoryError("NOTION_ARTIFACT_MINIMUM", "At least five released artifact bindings are required.")
    if len({str(row["external_id"]) for row in rows}) != len(rows):
        raise DeliveryInventoryError("NOTION_ARTIFACT_DUPLICATE", "Artifact IDs must be unique.")
    return tuple(rows)


def _history_rows(tasks: Sequence[CanonicalRecord], tenant_id: str, project_id: str) -> tuple[dict[str, JsonValue], ...]:
    return tuple({"external_id": item.record_id, "tenant_id": tenant_id, "project_id": project_id, "task_class": "core_history", "title": str(item.payload.get("title") or item.record_id), "history_only": True} for item in sorted(tasks, key=lambda value: value.record_id))


def _implementation_rows(tasks: Sequence[NotionImplementationTask], tenant_id: str, project_id: str) -> tuple[dict[str, JsonValue], ...]:
    if not tasks:
        raise DeliveryInventoryError("NOTION_IMPLEMENTATION_TASKS_MISSING", "Caller-supplied implementation work is required.")
    ids = [item.task_id for item in tasks] + [item.assignment_id for item in tasks]
    if len(set(ids)) != len(ids):
        raise DeliveryInventoryError("NOTION_STABLE_ID_CONFLICT", "Task and assignment stable IDs conflict.")
    return tuple({"external_id": item.task_id, "tenant_id": tenant_id, "project_id": project_id, "task_class": "notion_implementation", "title": item.title, "status": item.status, "comments": item.comments, "assignee": item.notion_user_id or "unassigned", "priority": item.priority, "deadline": item.deadline, "core_effect": "none"} for item in tasks)


def _core_rows(reviews: Sequence[CanonicalRecord], blockers: Sequence[CanonicalRecord], project_id: str, artifacts: Sequence[Mapping[str, JsonValue]]) -> tuple[tuple[dict[str, JsonValue], ...], tuple[dict[str, JsonValue], ...]]:
    known = {str(row["external_id"]) for row in artifacts}
    def rows(records: Sequence[CanonicalRecord]) -> tuple[dict[str, JsonValue], ...]:
        output: list[dict[str, JsonValue]] = []
        for item in sorted(records, key=lambda value: value.record_id):
            artifact_id = item.payload.get("artifact_id")
            if not isinstance(artifact_id, str) or artifact_id not in known:
                raise DeliveryInventoryError("NOTION_CORE_ROW_ARTIFACT_MISSING", "Core review and blocker rows require an included artifact.")
            output.append({"external_id": item.record_id, "project_external_id": project_id, "artifact_external_id": artifact_id, "source_sha256": _hash(item.payload), "read_only": True})
        return tuple(output)
    result = rows(reviews), rows(blockers)
    if not result[0] or not result[1]:
        raise DeliveryInventoryError("NOTION_CORE_ROWS_MISSING", "At least one review and blocker are required.")
    return result


def _approvals(inventory: DeliveryInventory, artifacts: Sequence[Mapping[str, JsonValue]]) -> tuple[dict[str, JsonValue], ...]:
    releases = {str(item.payload.get("artifact_id")): item for item in inventory.releases}
    rows = tuple({"external_id": str(releases[str(row["external_id"])].payload.get("approval_id", "")), "project_external_id": inventory.project_id, "artifact_external_id": row["external_id"], "source_sha256": _hash(releases[str(row["external_id"])].payload), "read_only": True} for row in artifacts)
    if any(not str(row["external_id"]) for row in rows) or len({str(row["external_id"]) for row in rows}) != len(rows):
        raise DeliveryInventoryError("NOTION_APPROVAL_BINDING_INVALID", "Every canonical release requires one unique approval ID.")
    return rows


def _rows(inventory: DeliveryInventory, context: NotionImportBuildContext, artifacts: tuple[dict[str, JsonValue], ...], history: tuple[dict[str, JsonValue], ...], implementation: tuple[dict[str, JsonValue], ...], tasks: tuple[NotionImplementationTask, ...], reviews: tuple[dict[str, JsonValue], ...], approvals: tuple[dict[str, JsonValue], ...], blockers: tuple[dict[str, JsonValue], ...], registry: PublicationRegistryRecord) -> dict[str, JsonValue]:
    artifact_ids = {str(row["external_id"]) for row in artifacts}
    by_task = {item.task_id: item for item in tasks}
    for task in tasks:
        if any(dependency not in by_task for dependency in task.dependencies) or any(artifact not in artifact_ids for artifact in task.artifact_relations):
            raise DeliveryInventoryError("NOTION_RELATION_DANGLING", "Implementation relations must use included stable IDs.")
    assignments = tuple({"external_id": item.assignment_id, "task_external_id": item.task_id, "assignee": item.notion_user_id or "unassigned"} for item in tasks)
    relations = [{"from_record_id": inventory.project_id, "to_record_id": artifact_id, "relation_type": "belongs_to"} for artifact_id in sorted(artifact_ids)]
    relations.extend({"from_record_id": item.task_id, "to_record_id": inventory.project_id, "relation_type": "belongs_to"} for item in tasks)
    relations.extend({"from_record_id": item.assignment_id, "to_record_id": item.task_id, "relation_type": "assigned_to"} for item in tasks)
    relations.extend({"from_record_id": item.task_id, "to_record_id": dependency, "relation_type": "depends_on"} for item in tasks for dependency in item.dependencies)
    relations.extend({"from_record_id": item.task_id, "to_record_id": artifact, "relation_type": "depends_on"} for item in tasks for artifact in item.artifact_relations)
    ordered_relations = tuple(sorted(relations, key=lambda value: (str(value["from_record_id"]), str(value["to_record_id"]), str(value["relation_type"]))))
    if len({(row["from_record_id"], row["to_record_id"], row["relation_type"]) for row in ordered_relations}) != len(ordered_relations):
        raise DeliveryInventoryError("NOTION_RELATION_DUPLICATE", "Relations must be unique.")
    sources = _sources(inventory, artifacts, tasks, registry)
    unresolved = tuple(item.assignment_id for item in tasks if item.notion_user_id is None)
    return {"customer_rows": [{"external_id": context.customer_external_id, "source_sha256": _hash({"external_id": context.customer_external_id})}], "project_rows": [{"external_id": inventory.project_id, "customer_external_id": context.customer_external_id, "tenant_id": inventory.tenant_id, "project_id": inventory.project_id, "source_sha256": _hash(inventory.project_v2.payload)}], "artifact_rows": list(artifacts), "review_rows": list(reviews), "approval_rows": list(approvals), "blocker_rows": list(blockers), "task_rows": [*history, *implementation], "assignment_rows": list(assignments), "priority_rows": [{"task_external_id": item.task_id, "value": item.priority} for item in tasks], "deadline_rows": [{"task_external_id": item.task_id, "value": item.deadline} for item in tasks], "relations": list(ordered_relations), "performance_checkpoint_rows": [{"day_after_publication": day, "released_strategy_artifact_id": _artifact_for_role(artifacts, "strategy"), "released_plan_artifact_id": _artifact_for_role(artifacts, "roadmap"), "publication_registry_record_id": registry.record_id, "performance_data_status": "pending_verified_data"} for day in (30, 60, 90)], "source_records": list(sources), "unresolved_assignee_ids": list(unresolved), "user_mapping_rows": [{"assignment_external_id": item.assignment_id, "source_assignee": item.source_assignee} for item in tasks if item.notion_user_id is None]}


def _sources(inventory: DeliveryInventory, artifacts: Sequence[Mapping[str, JsonValue]], tasks: Sequence[NotionImplementationTask], registry: PublicationRegistryRecord) -> tuple[dict[str, JsonValue], ...]:
    rows = [{"tenant_id": inventory.tenant_id, "project_id": inventory.project_id, "source_record_id": inventory.project_id, "source_sha256": _hash(inventory.project_v2.payload)}]
    rows.extend({"tenant_id": inventory.tenant_id, "project_id": inventory.project_id, "source_record_id": str(item["external_id"]), "source_sha256": str(item["content_sha256"])} for item in artifacts)
    rows.extend({"tenant_id": inventory.tenant_id, "project_id": inventory.project_id, "source_record_id": item.task_id, "source_sha256": _hash(_task_json(item))} for item in tasks)
    rows.extend({"tenant_id": inventory.tenant_id, "project_id": inventory.project_id, "source_record_id": item.assignment_id, "source_sha256": _hash({"task_id": item.task_id, "assignment_id": item.assignment_id, "source_assignee": item.source_assignee, "notion_user_id": item.notion_user_id})} for item in tasks)
    rows.extend({"tenant_id": inventory.tenant_id, "project_id": inventory.project_id, "source_record_id": item.record_id, "source_sha256": _hash(item.payload)} for item in inventory.tasks)
    rows.extend({"tenant_id": inventory.tenant_id, "project_id": inventory.project_id, "source_record_id": item.record_id, "source_sha256": _hash(item.payload)} for item in inventory.assignments)
    if registry.payload.get("publication_registry_record_id") != registry.record_id or len(registry.payload) < 2:
        raise DeliveryInventoryError("NOTION_PUBLICATION_REFERENCE_INVALID", "Publication registry payload identity must match its stable record ID.")
    rows.append({"tenant_id": inventory.tenant_id, "project_id": inventory.project_id, "source_record_id": registry.record_id, "source_sha256": _hash(registry.payload)})
    indexed: dict[str, dict[str, JsonValue]] = {}
    for row in rows:
        record_id = str(row["source_record_id"])
        previous = indexed.get(record_id)
        if previous is not None and previous["source_sha256"] != row["source_sha256"]:
            raise DeliveryInventoryError("NOTION_SOURCE_ID_CONFLICT", "Source identity has conflicting canonical hashes.")
        indexed[record_id] = row
    return tuple(sorted(indexed.values(), key=lambda value: str(value["source_record_id"])))


def _render(rows: Mapping[str, JsonValue], delivery_safe: bool) -> tuple[RenderedNotionImportFile, ...]:
    columns = CSV_HEADERS
    files: list[RenderedNotionImportFile] = []
    for name, (collection, headers) in columns.items():
        values = rows[collection]
        if name == "projects.csv":
            customers = rows["customer_rows"]
            values = ([{"record_type": "customer", "customer_external_id": item["external_id"], "external_id": item["external_id"], "source_sha256": item["source_sha256"]} for item in customers] + [{"record_type": "project", **item} for item in values]) if isinstance(customers, list) and isinstance(values, list) else []
        if not isinstance(values, list):
            raise DeliveryInventoryError("NOTION_RENDER_ROWS_INVALID", "Manifest rows are malformed.")
        output = tuple(tuple(str(value.get(header, "")) for header in headers) for value in values if isinstance(value, Mapping))
        files.append(render_csv(name, headers, output))
    unresolved = rows["unresolved_assignee_ids"]
    mappings = rows["user_mapping_rows"]
    mapping_rows = tuple((str(item["assignment_external_id"]), str(item["source_assignee"]), "") for item in mappings) if isinstance(mappings, list) else ()
    return tuple([*files, import_order(), property_mapping(delivery_safe), user_mapping(mapping_rows)])


def _manifest(inventory: DeliveryInventory, context: NotionImportBuildContext, rows: Mapping[str, JsonValue], rendered: Sequence[RenderedNotionImportFile]) -> dict[str, JsonValue]:
    descriptors = [{"file_name": item.path.rsplit("/", 1)[1], "relative_path": item.path, "content_sha256": hashlib.sha256(item.content).hexdigest(), "row_count": item.row_count} for item in rendered]
    manifest: dict[str, JsonValue] = {"notion_import_manifest_id": context.notion_import_manifest_id, "schema_version": "1.0.0", "tenant_id": inventory.tenant_id, "project_id": inventory.project_id, "export_id": context.export_id, "delivery_package_id": context.delivery_package_id, "integration_mode": "manual_import", "source_snapshot_revision": context.source_snapshot_revision, "files": descriptors, "user_mapping_template_path": "notion-import/USER_MAPPING_TEMPLATE.csv", "created_at": context.created_at, **{key: value for key, value in rows.items() if key != "user_mapping_rows"}}
    manifest["manifest_sha256"] = hashlib.sha256(manifest_preimage_bytes(manifest)).hexdigest()
    return manifest


def _validate(inventory: DeliveryInventory, manifest: Mapping[str, JsonValue]) -> None:
    if any(_VALIDATOR.iter_errors(manifest)):
        raise DeliveryInventoryError("NOTION_MANIFEST_INVALID", "Generated manifest violates the closed Notion import schema.")
    package: dict[str, JsonValue] = {"tenant_id": inventory.tenant_id, "project_id": inventory.project_id, "source_records": manifest["source_records"]}
    if not validate_delivery_contracts(package, (), manifest).valid:
        raise DeliveryInventoryError("NOTION_MANIFEST_SEMANTICS_INVALID", "Generated manifest violates delivery semantics.")


def _artifact_for_role(artifacts: Sequence[Mapping[str, JsonValue]], role: str) -> str:
    matches = [str(item["external_id"]) for item in artifacts if item.get("role") == role]
    if len(matches) != 1:
        raise DeliveryInventoryError("NOTION_PERFORMANCE_REFERENCE_MISSING", "Exactly one released strategy and roadmap artifact are required.")
    return matches[0]


def _task_json(task: NotionImplementationTask) -> dict[str, JsonValue]:
    return {"task_id": task.task_id, "assignment_id": task.assignment_id, "title": task.title, "status": task.status, "comments": task.comments, "source_assignee": task.source_assignee, "notion_user_id": task.notion_user_id, "priority": task.priority, "deadline": task.deadline, "role": task.role, "dependencies": sorted(task.dependencies), "artifact_relations": sorted(task.artifact_relations)}


def _ordered_tasks(tasks: Sequence[NotionImplementationTask]) -> tuple[NotionImplementationTask, ...]:
    if any(len(set(item.dependencies)) != len(item.dependencies) or len(set(item.artifact_relations)) != len(item.artifact_relations) for item in tasks):
        raise DeliveryInventoryError("NOTION_RELATION_DUPLICATE", "Task dependency and artifact relations must be unique.")
    if any(item.notion_user_id is not None and _NOTION_USER_ID.fullmatch(item.notion_user_id) is None for item in tasks):
        raise DeliveryInventoryError("NOTION_USER_ID_INVALID", "Verified Notion user IDs must use the explicit notion-user prefix.")
    return tuple(sorted(tasks, key=lambda item: item.task_id))


def _hash(value: Mapping[str, JsonValue]) -> str:
    return hashlib.sha256(json.dumps(plain_json(value), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
