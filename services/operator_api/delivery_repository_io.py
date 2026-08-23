from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
from types import MappingProxyType
from typing import Final

from services.delivery.contract_validation import JsonValue
from services.delivery.inventory import SelectedWorkspaceFile

from .delivery_snapshot_values import freeze_mapping
from .repository_types import RepositoryError


_STEP_FOLDERS: Final = MappingProxyType(
    {
        "1": "strategy",
        "1b": "architecture",
        "1c": "design",
        "2": "keyword-research",
        "3": "roadmap",
        "4a": "copywriter-handoff",
        "4b": "developer-handoff",
    }
)


@dataclass(frozen=True, slots=True)
class SelectedArtifactContent:
    artifact_id: str
    source_path: str
    output_path: str
    source_sha256: str
    content: bytes


def _project_v2(value: Mapping[str, JsonValue], tenant_id: str, project_id: str) -> Mapping[str, JsonValue]:
    tenant = value.get("tenant")
    if value.get("project_id") != project_id or not isinstance(tenant, Mapping) or tenant.get("tenant_id") != tenant_id:
        _invalid("identity is mismatched")
    return _freeze_mapping(value)


def _record(value: Mapping[str, JsonValue], tenant_id: str, project_id: str) -> Mapping[str, JsonValue]:
    if value.get("tenant_id") != tenant_id:
        _isolation("tenant identity is mismatched")
    stored_project_id = value.get("project_id")
    if stored_project_id is not None and stored_project_id != project_id:
        _isolation("project identity is mismatched")
    return _freeze_mapping(value)


def _collection(path: Path, identifier: str, tenant_id: str, project_id: str, *, required: bool) -> tuple[Mapping[str, JsonValue], ...]:
    if not path.exists():
        if required:
            _missing("collection is unavailable")
        return ()
    value = _json_value(path)
    if not isinstance(value, list):
        _invalid("collection is malformed")
    records = tuple(_record(item, tenant_id, project_id) for item in value if isinstance(item, Mapping))
    if len(records) != len(value):
        _invalid("collection contains a non-object record")
    return _sorted_records(records, identifier)


def _directory_records(path: Path, identifier: str, tenant_id: str, project_id: str, *, required: bool) -> tuple[Mapping[str, JsonValue], ...]:
    if not path.exists():
        if required:
            _missing("record collection is unavailable")
        return ()
    _directory(path, required=True)
    try:
        paths = tuple(sorted(path.glob("*.json")))
    except OSError as error:
        raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical delivery record collection is unreadable.") from error
    records: list[Mapping[str, JsonValue]] = []
    for record_path in paths:
        record = _record(_json_object(record_path, required=True), tenant_id, project_id)
        record_id = record.get(identifier)
        if not isinstance(record_id, str) or record_id != record_path.stem:
            _invalid("record filename identity is malformed")
        records.append(record)
    return _sorted_records(tuple(records), identifier)


def _selected_artifact_files(root: Path, operator_root: Path, artifacts: tuple[Mapping[str, JsonValue], ...]) -> tuple[tuple[SelectedWorkspaceFile, ...], tuple[SelectedArtifactContent, ...]]:
    _directory(operator_root / "artifact-content", required=True)
    selections: list[SelectedWorkspaceFile] = []
    contents: list[SelectedArtifactContent] = []
    outputs: set[str] = set()
    for artifact in artifacts:
        step_id = artifact.get("step_id")
        folder = _STEP_FOLDERS.get(step_id) if isinstance(step_id, str) else None
        if folder is None:
            continue
        artifact_id, source_sha256 = artifact.get("artifact_id"), artifact.get("content_sha256")
        if not isinstance(artifact_id, str) or not isinstance(source_sha256, str):
            _invalid("artifact identity or hash is malformed")
        source = operator_root / "artifact-content" / f"{artifact_id}.md"
        content = _bytes(source)
        actual_sha256 = hashlib.sha256(content).hexdigest()
        if actual_sha256 != source_sha256:
            _invalid("artifact content hash is mismatched")
        output_path = f"{folder}/{artifact_id}.md"
        if output_path in outputs:
            _invalid("artifact output path is duplicated")
        outputs.add(output_path)
        source_path = source.relative_to(root).as_posix()
        selections.append(SelectedWorkspaceFile(source_path, output_path, actual_sha256, artifact_id))
        contents.append(SelectedArtifactContent(artifact_id, source_path, output_path, actual_sha256, content))
    return tuple(selections), tuple(contents)


def _json_object(path: Path, *, required: bool) -> Mapping[str, JsonValue]:
    if not path.exists():
        if required:
            _missing("projection is unavailable")
        _invalid("optional object projection is unavailable")
    value = _json_value(path)
    if not isinstance(value, Mapping):
        _invalid("projection is malformed")
    return value


def _json_value(path: Path) -> JsonValue:
    _regular_file(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical delivery projection is unreadable.") from error


def _bytes(path: Path) -> bytes:
    _regular_file(path)
    try:
        return path.read_bytes()
    except OSError as error:
        raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical delivery artifact content is unreadable.") from error


def _directory(path: Path, *, required: bool) -> None:
    if not path.exists():
        if required:
            _missing("directory is unavailable")
        return
    try:
        metadata = os.lstat(path)
    except OSError as error:
        raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical delivery directory is unreadable.") from error
    if not stat.S_ISDIR(metadata.st_mode) or _reparse(metadata):
        _invalid("directory is unsafe")


def _regular_file(path: Path) -> None:
    try:
        metadata = os.lstat(path)
    except OSError as error:
        raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical delivery file is unavailable.") from error
    if not stat.S_ISREG(metadata.st_mode) or _reparse(metadata):
        _invalid("file is unsafe or non-regular")


def _reparse(metadata: os.stat_result) -> bool:
    return bool(getattr(metadata, "st_file_attributes", 0) & 0x400)


def _sorted_records(records: tuple[Mapping[str, JsonValue], ...], identifier: str) -> tuple[Mapping[str, JsonValue], ...]:
    values: list[tuple[str, str, Mapping[str, JsonValue]]] = []
    for record in records:
        record_id = record.get(identifier)
        if not isinstance(record_id, str) or not record_id:
            _invalid("record identity is malformed")
        step_id = record.get("step_id")
        values.append((step_id if isinstance(step_id, str) else "", record_id, record))
    if len({record_id for _, record_id, _ in values}) != len(values):
        _invalid("record identity is duplicated")
    return tuple(record for _, _, record in sorted(values))


def _freeze_mapping(value: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
    return freeze_mapping(value)


def _missing(detail: str) -> None:
    raise RepositoryError("ERROR_DOMAIN_CONTRACT_FILE_MISSING", f"Canonical delivery {detail}.")


def _invalid(detail: str) -> None:
    raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", f"Canonical delivery {detail}.")


def _isolation(detail: str) -> None:
    raise RepositoryError("ERR_TENANT_ISOLATION", f"Canonical delivery {detail}.")
