from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, TypedDict

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


JsonScalar = None | bool | int | float | str
JsonValue = JsonScalar | list["JsonValue"] | Mapping[str, "JsonValue"]
JsonDocument = Mapping[str, JsonValue]


class NotionGraphTarget(StrEnum):
    PROJECTION = "projection"
    SNAPSHOT = "snapshot"


class NotionGraphSchemas(TypedDict):
    record_map: JsonDocument
    projection: JsonDocument
    snapshot: JsonDocument


@dataclass(frozen=True, slots=True)
class NotionGraphError:
    code: str
    message: str
    path: tuple[str | int, ...]


@dataclass(frozen=True, slots=True)
class NotionGraphValidationResult:
    valid: bool
    target_kind: NotionGraphTarget
    record_count: int
    errors: tuple[NotionGraphError, ...]


@dataclass(frozen=True, slots=True)
class NotionGraphValidationError(ValueError):
    error: NotionGraphError

    def __str__(self) -> str:
        return f"{self.error.code}: {self.error.message}"


RELATION_PREFIXES: Final[dict[str, str]] = {
    "customer": "customer-",
    "project": "project-",
    "run": "run-",
    "step": "step-",
    "task": "task-",
    "assignment": "assignment-",
    "artifact": "artifact-",
    "gate": "gate-",
    "review": "review-",
    "approval": "approval-",
    "blocker": "blocker-",
    "defect": "defect-",
    "escalation": "escalation-",
    "performance_checkpoint": "performance-checkpoint-",
    "metric": "metric-",
    "adjustment_proposal": "adjustment-proposal-",
    "integration_status": "integration-status-",
}


def _registry(schemas: NotionGraphSchemas) -> Registry:
    registry = Registry()
    for schema_name in ("record_map", "projection", "snapshot"):
        schema = schemas[schema_name]
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str):
            message = f"V2 Notion schema '{schema_name}' has no string $id."
            raise NotionGraphValidationError(
                NotionGraphError(
                    "NOTION_GRAPH_SCHEMA_ID_INVALID",
                    message,
                    (schema_name, "$id"),
                )
            )
        registry = registry.with_resource(schema_id, Resource.from_contents(schema))
    return registry


def _schema_errors(
    document: JsonDocument,
    target_kind: NotionGraphTarget,
    schemas: NotionGraphSchemas,
) -> tuple[NotionGraphError, ...]:
    validator = Draft202012Validator(
        schemas[target_kind],
        registry=_registry(schemas),
        format_checker=FormatChecker(),
    )
    return tuple(
        NotionGraphError(
            "NOTION_GRAPH_SCHEMA_INVALID",
            error.message,
            tuple(error.absolute_path),
        )
        for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    )


def _semantic_errors(document: JsonDocument) -> tuple[NotionGraphError, ...]:
    records = document.get("records")
    if not isinstance(records, Mapping):
        return ()

    errors: list[NotionGraphError] = []
    for record_id, record in records.items():
        if not isinstance(record_id, str) or not isinstance(record, Mapping):
            continue
        subject_id = record.get("subject_id")
        if subject_id != record_id:
            errors.append(
                NotionGraphError(
                    "NOTION_GRAPH_SUBJECT_ID_MISMATCH",
                    "Record map key must equal the record subject_id.",
                    ("records", record_id, "subject_id"),
                )
            )
        relations = record.get("relations")
        if not isinstance(relations, list):
            continue
        edge_paths: set[tuple[str, str]] = set()
        for relation_index, relation in enumerate(relations):
            if not isinstance(relation, Mapping):
                continue
            relation_type = relation.get("relation_type")
            target_record_id = relation.get("target_record_id")
            if not isinstance(relation_type, str) or not isinstance(target_record_id, str):
                continue
            relation_path = ("records", record_id, "relations", relation_index)
            expected_prefix = RELATION_PREFIXES.get(relation_type)
            if expected_prefix is not None and not target_record_id.startswith(expected_prefix):
                errors.append(
                    NotionGraphError(
                        "NOTION_GRAPH_RELATION_TARGET_TYPE_MISMATCH",
                        "Relation type must match the target record ID prefix family.",
                        relation_path + ("target_record_id",),
                    )
                )
            if target_record_id not in records:
                errors.append(
                    NotionGraphError(
                        "NOTION_GRAPH_RELATION_TARGET_MISSING",
                        "Relation target must exist in the same records map.",
                        relation_path + ("target_record_id",),
                    )
                )
            edge = (relation_type, target_record_id)
            if edge in edge_paths:
                errors.append(
                    NotionGraphError(
                        "NOTION_GRAPH_DUPLICATE_EDGE",
                        "A relation type and target record ID pair may occur only once per record.",
                        relation_path,
                    )
                )
            edge_paths.add(edge)
    return tuple(errors)


def _record_count(document: JsonDocument) -> int:
    records = document.get("records")
    return len(records) if isinstance(records, Mapping) else 0


def validate_notion_graph(
    document: JsonDocument,
    target_kind: NotionGraphTarget,
    schemas: NotionGraphSchemas,
) -> NotionGraphValidationResult:
    errors = _schema_errors(document, target_kind, schemas) + _semantic_errors(document)
    return NotionGraphValidationResult(
        valid=not errors,
        target_kind=target_kind,
        record_count=_record_count(document),
        errors=errors,
    )


def assert_notion_graph_valid(
    document: JsonDocument,
    target_kind: NotionGraphTarget,
    schemas: NotionGraphSchemas,
) -> NotionGraphValidationResult:
    result = validate_notion_graph(document, target_kind, schemas)
    if result.errors:
        raise NotionGraphValidationError(result.errors[0])
    return result
