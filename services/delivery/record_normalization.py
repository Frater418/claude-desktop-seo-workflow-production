from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
from types import MappingProxyType
from typing import TypeAlias

from jsonschema import Draft202012Validator, FormatChecker

from .contract_validation import JsonValue
from .release_contract import ReleaseRecord


FrozenJsonValue: TypeAlias = str | int | float | bool | None | Mapping[str, "FrozenJsonValue"] | tuple["FrozenJsonValue", ...]


class DeliveryInventoryError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class CanonicalRecord:
    kind: str
    record_id: str
    step_id: str | None
    revision: int | None
    content_sha256: str | None
    payload: Mapping[str, FrozenJsonValue]


_IDENTIFIERS = {"run": "run_id", "artifact": "artifact_id", "release": "release_id", "gate": "quality_gate_run_id", "task": "task_id", "assignment": "assignment_id", "review": "review_id", "blocker": "blocker_id", "report": "report_id"}
_STEPS = frozenset(("0", "1", "1b", "1c", "2", "3", "3b", "4a", "4b"))
_SCOPED_KINDS = frozenset(("run", "artifact", "release", "task", "assignment", "review", "blocker", "report"))
_ARTIFACT_SCHEMA = json.loads((Path(__file__).resolve().parents[2] / "standards" / "runtime" / "artifact-record.schema.json").read_text(encoding="utf-8"))
_TASK_SCHEMA = json.loads((Path(__file__).resolve().parents[2] / "standards" / "operator" / "operator-task.schema.json").read_text(encoding="utf-8"))
_ARTIFACT_VALIDATOR = Draft202012Validator(_ARTIFACT_SCHEMA, format_checker=FormatChecker())
_TASK_VALIDATOR = Draft202012Validator(_TASK_SCHEMA, format_checker=FormatChecker())


def normalize(kind: str, value: Mapping[str, JsonValue], tenant_id: str, project_id: str) -> CanonicalRecord:
    if not isinstance(value, Mapping):
        raise DeliveryInventoryError("DELIVERY_SOURCE_RECORD_MALFORMED", "Injected source record is not an object.")
    if kind == "project":
        return _project(value, tenant_id, project_id)
    if kind == "workflow":
        return _workflow(value, tenant_id, project_id)
    identifier = _IDENTIFIERS[kind]
    record_id = _text(value.get(identifier))
    actual_tenant = _text(value.get("tenant_id"))
    if not record_id:
        raise DeliveryInventoryError("DELIVERY_SOURCE_RECORD_MALFORMED", "Canonical source identity is incomplete.")
    if actual_tenant != tenant_id:
        raise DeliveryInventoryError("DELIVERY_SOURCE_SCOPE_INVALID", "Canonical source identity is mismatched.")
    actual_project = _text(value.get("project_id"))
    if kind in _SCOPED_KINDS and actual_project != project_id:
        raise DeliveryInventoryError("DELIVERY_SOURCE_SCOPE_INVALID", "Canonical source project is mismatched.")
    _step(value, kind)
    revision = _revision(value, "revision") if kind in {"run", "artifact"} else _revision(value, "artifact_revision") if kind == "release" else None
    if kind == "artifact":
        if any(_ARTIFACT_VALIDATOR.iter_errors(value)):
            raise DeliveryInventoryError("DELIVERY_SOURCE_RECORD_MALFORMED", "Canonical artifact shape is invalid.")
    if kind == "release":
        try:
            ReleaseRecord.model_validate(value)
        except ValueError as exc:
            raise DeliveryInventoryError("DELIVERY_RELEASE_MALFORMED", "Canonical release shape is invalid.") from exc
    if kind == "task":
        if any(_TASK_VALIDATOR.iter_errors(value)):
            raise DeliveryInventoryError("DELIVERY_SOURCE_RECORD_MALFORMED", "Canonical operator task shape is invalid.")
    content_hash = _text(value.get("content_sha256")) or _text(value.get("artifact_sha256"))
    return CanonicalRecord(kind, record_id, _text(value.get("step_id")), revision, content_hash, _freeze_mapping(value))


def normalize_collection(kind: str, values: Sequence[Mapping[str, JsonValue]], tenant_id: str, project_id: str) -> tuple[CanonicalRecord, ...]:
    records = tuple(normalize(kind, value, tenant_id, project_id) for value in values)
    if len({item.record_id for item in records}) != len(records):
        raise DeliveryInventoryError("DELIVERY_DUPLICATE_RECORD_ID", "Canonical collection has duplicate record identities.")
    return tuple(sorted(records, key=lambda item: ((item.step_id or ""), item.record_id, item.revision or 0)))


def validate_release_bindings(artifacts: tuple[CanonicalRecord, ...], releases: tuple[CanonicalRecord, ...]) -> frozenset[str]:
    artifact_by_id = {artifact.record_id: artifact for artifact in artifacts}
    bindings: set[str] = set()
    for release in releases:
        artifact_id = _text(release.payload.get("artifact_id"))
        artifact = artifact_by_id.get(artifact_id or "")
        if artifact is None:
            raise DeliveryInventoryError("DELIVERY_RELEASE_UNKNOWN_ARTIFACT", "Release references an unknown artifact.")
        if artifact_id in bindings:
            raise DeliveryInventoryError("DELIVERY_DUPLICATE_RELEASE_BINDING", "Multiple releases bind one artifact.")
        bindings.add(artifact_id)
        if release.revision != artifact.revision or release.content_sha256 != artifact.content_sha256 or release.step_id != artifact.step_id or _text(release.payload.get("run_id")) != _text(artifact.payload.get("run_id")):
            raise DeliveryInventoryError("DELIVERY_RELEASE_BINDING_MISMATCH", "Release does not exactly bind its artifact.")
    return frozenset(bindings)


def _project(value: Mapping[str, JsonValue], tenant_id: str, project_id: str) -> CanonicalRecord:
    tenant = value.get("tenant")
    if not isinstance(tenant, Mapping) or value.get("project_id") != project_id or tenant.get("tenant_id") != tenant_id or not _text(value.get("schema_version")):
        raise DeliveryInventoryError("DELIVERY_SOURCE_SCOPE_INVALID", "Project V2 identity is mismatched.")
    return CanonicalRecord("project", project_id, None, None, None, _freeze_mapping(value))


def _workflow(value: Mapping[str, JsonValue], tenant_id: str, project_id: str) -> CanonicalRecord:
    if value.get("tenant_id") != tenant_id or value.get("project_id") != project_id or not _sequence(value.get("initial_edges")) or not _sequence(value.get("sideflows")):
        raise DeliveryInventoryError("DELIVERY_SOURCE_RECORD_MALFORMED", "Provisioned workflow is malformed.")
    return CanonicalRecord("workflow", f"workflow:{project_id}", None, None, None, _freeze_mapping(value))


def _step(value: Mapping[str, JsonValue], kind: str) -> None:
    step = _text(value.get("step_id"))
    if kind in {"run", "artifact", "release", "gate", "task"} and step not in _STEPS:
        raise DeliveryInventoryError("DELIVERY_SOURCE_RECORD_MALFORMED", "Canonical record step is invalid.")


def _revision(value: Mapping[str, JsonValue], field: str) -> int:
    revision = value.get(field)
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise DeliveryInventoryError("DELIVERY_SOURCE_RECORD_MALFORMED", "Canonical record revision is invalid.")
    return revision


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str)


def _freeze_mapping(value: Mapping[str, JsonValue]) -> Mapping[str, FrozenJsonValue]:
    _host_paths(value)
    return MappingProxyType({key: _freeze(item) for key, item in sorted(value.items())})


def _host_paths(value: Mapping[str, JsonValue] | Sequence[JsonValue], context: str = "") -> None:
    values = ((f"{context}.{key}" if context else key, item) for key, item in value.items()) if isinstance(value, Mapping) else ((context, item) for item in value)
    for key, item in values:
        if isinstance(item, Mapping) or isinstance(item, Sequence) and not isinstance(item, str):
            _host_paths(item, key)
        elif isinstance(item, str) and _host_path(item, key):
            raise DeliveryInventoryError("DELIVERY_PATH_ABSOLUTE", "Canonical payload contains a host path.")


def _host_path(value: str, context: str) -> bool:
    if value.lower().startswith("file:"):
        return True
    return any(token in context.lower() for token in ("path", "workspace", "source", "output", "storage", "root", "directory")) and (value.startswith("/") or value.startswith("\\\\") or len(value) > 2 and value[1] == ":")


def _freeze(value: JsonValue) -> FrozenJsonValue:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(_freeze(item) for item in value)
    return value
