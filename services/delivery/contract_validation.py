from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from typing import TypeAlias


JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | Mapping[str, "JsonValue"] | Sequence["JsonValue"]


@dataclass(frozen=True, slots=True)
class DeliveryContractError:
    code: str
    path: tuple[str | int, ...]
    message: str


@dataclass(frozen=True, slots=True)
class DeliveryContractValidationResult:
    errors: tuple[DeliveryContractError, ...]

    @property
    def valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True, slots=True)
class DeliveryReplayValidationResult:
    errors: tuple[DeliveryContractError, ...]
    idempotent: bool

    @property
    def valid(self) -> bool:
        return not self.errors


def _error(code: str, path: tuple[str | int, ...], message: str) -> DeliveryContractError:
    return DeliveryContractError(code, path, message)


def _records(value: JsonValue | None) -> Sequence[JsonValue]:
    return value if isinstance(value, Sequence) and not isinstance(value, str) else ()


def _mapping(value: JsonValue | None) -> Mapping[str, JsonValue] | None:
    return value if isinstance(value, Mapping) else None


def _scope_errors(document: Mapping[str, JsonValue], path: tuple[str | int, ...], tenant_id: str, project_id: str) -> list[DeliveryContractError]:
    errors: list[DeliveryContractError] = []
    if document.get("tenant_id") != tenant_id or document.get("project_id") != project_id:
        errors.append(_error("DELIVERY_SOURCE_SCOPE_INVALID", path, "Nested delivery identity must match the package tenant and project."))
    return errors


def _source_errors(document: Mapping[str, JsonValue], prefix: tuple[str | int, ...], tenant_id: str, project_id: str) -> list[DeliveryContractError]:
    errors: list[DeliveryContractError] = []
    for index, raw_source in enumerate(_records(document.get("source_records"))):
        source = _mapping(raw_source)
        if source is not None:
            errors.extend(_scope_errors(source, prefix + ("source_records", index), tenant_id, project_id))
    return errors


def _duplicate_errors(rows: Sequence[JsonValue], key: str, prefix: tuple[str | int, ...]) -> list[DeliveryContractError]:
    seen: set[str] = set()
    errors: list[DeliveryContractError] = []
    for index, raw_row in enumerate(rows):
        row = _mapping(raw_row)
        value = row.get(key) if row is not None else None
        if isinstance(value, str):
            if value in seen:
                errors.append(_error("DELIVERY_DUPLICATE_EXTERNAL_ID", prefix + (index, key), "Stable external IDs must be unique."))
            seen.add(value)
    return errors


def _relation_errors(notion: Mapping[str, JsonValue], record_ids: set[str]) -> list[DeliveryContractError]:
    edges: set[tuple[str, str, str]] = set()
    errors: list[DeliveryContractError] = []
    for index, raw_relation in enumerate(_records(notion.get("relations"))):
        relation = _mapping(raw_relation)
        if relation is None:
            continue
        from_id = relation.get("from_record_id")
        to_id = relation.get("to_record_id")
        relation_type = relation.get("relation_type")
        if isinstance(from_id, str) and isinstance(to_id, str) and isinstance(relation_type, str):
            edge = (from_id, to_id, relation_type)
            if edge in edges:
                errors.append(_error("DELIVERY_DUPLICATE_RELATION", ("relations", index), "Relation triples must be unique."))
            edges.add(edge)
            if from_id not in record_ids or to_id not in record_ids:
                errors.append(_error("DELIVERY_RELATION_DANGLING", ("relations", index), "Relation endpoints must exist in the import manifest."))
    return errors


def _performance_errors(notion: Mapping[str, JsonValue]) -> list[DeliveryContractError]:
    rows = _records(notion.get("performance_checkpoint_rows"))
    days = {row.get("day_after_publication") for raw_row in rows if (row := _mapping(raw_row)) is not None}
    errors: list[DeliveryContractError] = []
    if days != {30, 60, 90}:
        errors.append(_error("DELIVERY_PERFORMANCE_CHECKPOINTS_INVALID", ("performance_checkpoint_rows",), "Exactly days 30, 60, and 90 are required."))
    for index, raw_row in enumerate(rows):
        row = _mapping(raw_row)
        if row is not None and any(not isinstance(row.get(name), str) for name in ("released_strategy_artifact_id", "released_plan_artifact_id", "publication_registry_record_id")):
            errors.append(_error("DELIVERY_PERFORMANCE_REFERENCE_INVALID", ("performance_checkpoint_rows", index), "Performance checkpoints require released strategy, plan, and publication references."))
    return errors


def _row_reference_errors(notion: Mapping[str, JsonValue], record_ids: set[str]) -> list[DeliveryContractError]:
    errors: list[DeliveryContractError] = []
    references = (("project_rows", "customer_external_id"), ("artifact_rows", "project_external_id"), ("assignment_rows", "task_external_id"), ("priority_rows", "task_external_id"), ("deadline_rows", "task_external_id"), ("review_rows", "artifact_external_id"), ("approval_rows", "artifact_external_id"), ("blocker_rows", "artifact_external_id"))
    for collection, field in references:
        for index, raw_row in enumerate(_records(notion.get(collection))):
            row = _mapping(raw_row)
            reference = row.get(field) if row is not None else None
            if isinstance(reference, str) and reference not in record_ids:
                errors.append(_error("DELIVERY_ROW_REFERENCE_DANGLING", (collection, index, field), "Imported row references must resolve to a stable external ID."))
    return errors


def validate_delivery_contracts(package: Mapping[str, JsonValue], role_manifests: Sequence[Mapping[str, JsonValue]], notion_manifest: Mapping[str, JsonValue]) -> DeliveryContractValidationResult:
    tenant_id = package.get("tenant_id")
    project_id = package.get("project_id")
    if not isinstance(tenant_id, str) or not isinstance(project_id, str):
        return DeliveryContractValidationResult((_error("DELIVERY_PACKAGE_SCOPE_INVALID", (), "Package tenant and project are required."),))
    errors = _source_errors(package, (), tenant_id, project_id)
    for index, role_manifest in enumerate(role_manifests):
        errors.extend(_scope_errors(role_manifest, ("role_manifests", index), tenant_id, project_id))
        errors.extend(_source_errors(role_manifest, ("role_manifests", index), tenant_id, project_id))
    errors.extend(_scope_errors(notion_manifest, ("notion_manifest",), tenant_id, project_id))
    errors.extend(_source_errors(notion_manifest, ("notion_manifest",), tenant_id, project_id))
    task_rows = _records(notion_manifest.get("task_rows"))
    record_ids = {tenant_id, project_id}
    for collection in ("customer_rows", "project_rows", "artifact_rows", "review_rows", "approval_rows", "blocker_rows", "task_rows", "assignment_rows"):
        rows = _records(notion_manifest.get(collection))
        errors.extend(_duplicate_errors(rows, "external_id", (collection,)))
        for raw_row in rows:
            row = _mapping(raw_row)
            external_id = row.get("external_id") if row is not None else None
            if isinstance(external_id, str):
                record_ids.add(external_id)
    for raw_source in _records(notion_manifest.get("source_records")):
        source = _mapping(raw_source)
        source_id = source.get("source_record_id") if source is not None else None
        if isinstance(source_id, str):
            record_ids.add(source_id)
    errors.extend(_row_reference_errors(notion_manifest, record_ids))
    errors.extend(_relation_errors(notion_manifest, record_ids))
    errors.extend(_performance_errors(notion_manifest))
    return DeliveryContractValidationResult(tuple(sorted(errors, key=lambda error: (error.code, error.path, error.message))))


def validate_notion_import_replay(existing: Mapping[str, JsonValue], replay: Mapping[str, JsonValue]) -> DeliveryReplayValidationResult:
    def errors_for(document: Mapping[str, JsonValue], label: str) -> list[DeliveryContractError]:
        tenant_id = document.get("tenant_id")
        project_id = document.get("project_id")
        if not isinstance(tenant_id, str) or not isinstance(project_id, str):
            return [_error("DELIVERY_REPLAY_CONFLICT", (label,), "Replay manifest requires tenant and project identity.")]
        errors = _source_errors(document, (label,), tenant_id, project_id)
        record_ids = {tenant_id, project_id}
        for collection in ("customer_rows", "project_rows", "artifact_rows", "review_rows", "approval_rows", "blocker_rows", "task_rows", "assignment_rows"):
            rows = _records(document.get(collection))
            errors.extend(_duplicate_errors(rows, "external_id", (label, collection)))
            for raw_row in rows:
                row = _mapping(raw_row)
                external_id = row.get("external_id") if row is not None else None
                if isinstance(external_id, str):
                    record_ids.add(external_id)
        errors.extend(_row_reference_errors(document, record_ids))
        errors.extend(_relation_errors(document, record_ids))
        errors.extend(_performance_errors(document))
        return errors
    errors = [*errors_for(existing, "existing"), *errors_for(replay, "replay")]
    identity = ("notion_import_manifest_id", "source_snapshot_revision")
    if any(existing.get(field) != replay.get(field) for field in identity) or json.dumps(existing, sort_keys=True, separators=(",", ":")) != json.dumps(replay, sort_keys=True, separators=(",", ":")):
        errors.append(_error("DELIVERY_REPLAY_CONFLICT", (), "A replay must preserve the import revision and every stable row payload."))
    ordered = tuple(sorted(errors, key=lambda error: (error.code, error.path, error.message)))
    return DeliveryReplayValidationResult(ordered, not ordered)
