"""Contained workspace registry and deterministic Operator projections."""

from __future__ import annotations

import copy
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from .models import JsonValue

_IDENTIFIER: Final = re.compile(r"^(tenant|project|run)-[a-z0-9][a-z0-9-]{2,63}$")
_COLLECTIONS: Final = frozenset({
    "steps", "artifacts", "gates", "tasks", "tickets", "assignments", "context-packages",
    "llm-runs", "performance-checkpoints", "metrics", "adjustment-proposals", "integrations-status",
})
_OPERATOR_RECORD_IDENTITIES: Final = {
    "operator-task": ("task_id", re.compile(r"^task-[a-z0-9][a-z0-9-]{7,63}$"), "run_id"),
    "blocker-record": ("blocker_id", re.compile(r"^blocker-[a-z0-9][a-z0-9-]{7,63}$"), "run_id"),
    "revision-request": ("revision_request_id", re.compile(r"^revision-[a-z0-9][a-z0-9-]{7,63}$"), "run_id"),
    "workflow-defect": ("defect_id", re.compile(r"^defect-[a-z0-9][a-z0-9-]{7,63}$"), "affected_run_id"),
    "escalation-record": ("escalation_id", re.compile(r"^escalation-[a-z0-9][a-z0-9-]{7,63}$"), "run_id"),
    "resolution-record": ("resolution_id", re.compile(r"^resolution-[a-z0-9][a-z0-9-]{7,63}$"), "run_id"),
}


class RepositoryError(RuntimeError):
    """Path-free repository failure."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class WorkspaceRegistration:
    """Server-owned tenant-project workspace binding."""

    tenant_id: str
    project_id: str
    workspace: Path


class WorkspaceRegistry:
    """Immutable allowlist of resolved tenant-project workspaces."""

    def __init__(self, registrations: tuple[WorkspaceRegistration, ...]) -> None:
        self._registrations = registrations
        keys = {(item.tenant_id, item.project_id) for item in registrations}
        if len(keys) != len(registrations):
            raise RepositoryError("ERROR_DOMAIN_CONTRACT_INVALID", "Workspace registry has duplicate identities.")

    def resolve(self, tenant_id: str, project_id: str) -> Path:
        self._validate_id(tenant_id, "tenant")
        self._validate_id(project_id, "project")
        for registration in self._registrations:
            if registration.tenant_id == tenant_id and registration.project_id == project_id:
                return self._safe_root(registration.workspace)
        raise RepositoryError("ERR_TENANT_ISOLATION", "Tenant and project are not configured.")

    def projects(self, tenant_id: str) -> tuple[WorkspaceRegistration, ...]:
        self._validate_id(tenant_id, "tenant")
        return tuple(item for item in self._registrations if item.tenant_id == tenant_id)

    @property
    def registrations(self) -> tuple[WorkspaceRegistration, ...]:
        return self._registrations

    @staticmethod
    def _validate_id(value: str, prefix: str) -> None:
        if _IDENTIFIER.fullmatch(value) is None or not value.startswith(f"{prefix}-"):
            raise RepositoryError("ERR_TENANT_ISOLATION", "Tenant or project identity is invalid.")

    @staticmethod
    def _safe_root(workspace: Path) -> Path:
        try:
            root = workspace.resolve(strict=True)
        except OSError as exc:
            raise RepositoryError("ERROR_DOMAIN_CONTRACT_FILE_MISSING", "Configured workspace is inaccessible.") from exc
        if workspace.is_symlink() or not root.is_dir():
            raise RepositoryError("ERROR_OUTPUT_ROOT_INVALID", "Configured workspace is unsafe.")
        return root


class ProjectRepository:
    """Read and write controlled records below one registered workspace."""

    def __init__(self, registry: WorkspaceRegistry) -> None:
        self._registry = registry

    def list_projects(self, tenant_id: str) -> list[dict[str, JsonValue]]:
        projects: list[dict[str, JsonValue]] = []
        for registration in self._registry.projects(tenant_id):
            projects.append(self.project(registration.tenant_id, registration.project_id))
        return projects

    def project(self, tenant_id: str, project_id: str) -> dict[str, JsonValue]:
        return self._required(tenant_id, project_id, "project.json")

    def logical_session(self, tenant_id: str, project_id: str) -> dict[str, JsonValue]:
        return self._required(tenant_id, project_id, "logical-session.json")

    def workflow(self, tenant_id: str, project_id: str) -> dict[str, JsonValue]:
        return self._required(tenant_id, project_id, "workflow.json")

    def run(self, tenant_id: str, project_id: str, run_id: str) -> dict[str, JsonValue]:
        WorkspaceRegistry._validate_id(run_id, "run")
        return self._required(tenant_id, project_id, f"runs/{run_id}.json")

    def collection(self, tenant_id: str, project_id: str, name: str) -> list[dict[str, JsonValue]]:
        if name not in _COLLECTIONS:
            raise RepositoryError("ERROR_DOMAIN_CONTRACT_INVALID", "Requested projection collection is invalid.")
        value = self._optional(tenant_id, project_id, f"{name}.json", [])
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Projection collection is malformed.")
        return copy.deepcopy(value)

    def run_history(self, tenant_id: str, project_id: str, run_id: str) -> list[dict[str, JsonValue]]:
        return [item for item in self.collection(tenant_id, project_id, "llm-runs") if item.get("run_id") == run_id]

    def write_run(self, tenant_id: str, project_id: str, run: dict[str, JsonValue]) -> None:
        run_id = run.get("run_id")
        if not isinstance(run_id, str):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Derived run projection is malformed.")
        self._write(tenant_id, project_id, f"runs/{run_id}.json", run)

    def write_release(self, tenant_id: str, project_id: str, release: dict[str, JsonValue]) -> None:
        release_id = release.get("release_id")
        if not isinstance(release_id, str):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Release projection is malformed.")
        self._write(tenant_id, project_id, f"releases/{release_id}.json", release)

    def write_operator_record(self, tenant_id: str, project_id: str, record_type: str, record: dict[str, JsonValue]) -> None:
        identifier = self.operator_record_id(record_type, record)
        self._write(tenant_id, project_id, f"operator-records/{record_type}/{identifier}.json", record)

    @staticmethod
    def operator_record_id(record_type: str, record: dict[str, JsonValue]) -> str:
        identity = _OPERATOR_RECORD_IDENTITIES.get(record_type)
        if identity is None:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator record type is invalid.")
        field, pattern, _ = identity
        identifier = record.get(field)
        if not isinstance(identifier, str) or pattern.fullmatch(identifier) is None:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator record identity is invalid.")
        return identifier

    @staticmethod
    def operator_record_run_field(record_type: str) -> str:
        identity = _OPERATOR_RECORD_IDENTITIES.get(record_type)
        if identity is None:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator record type is invalid.")
        return identity[2]

    def write_operator_recovery(self, tenant_id: str, project_id: str, record_type: str, command_id: str, record: dict[str, JsonValue]) -> str:
        record_id = self.operator_record_id(record_type, record)
        self._write(
            tenant_id,
            project_id,
            f"projection-recovery/{record_type}--{record_id}.json",
            {"record_type": record_type, "record_id": record_id, "command_id": command_id, "record": record},
        )
        return record_id

    def operator_recovery(self, tenant_id: str, project_id: str, record_type: str, record_id: str) -> dict[str, JsonValue] | None:
        payload = self._optional(tenant_id, project_id, f"projection-recovery/{record_type}--{record_id}.json", None)
        if payload is None:
            return None
        if not isinstance(payload, dict) or payload.get("record_type") != record_type or payload.get("record_id") != record_id:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator recovery record is invalid.")
        record = payload.get("record")
        if not isinstance(payload.get("command_id"), str) or not isinstance(record, dict) or self.operator_record_id(record_type, record) != record_id:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator recovery record is invalid.")
        return copy.deepcopy(payload)

    def finalize_operator_recovery(self, tenant_id: str, project_id: str, record_type: str, record_id: str) -> None:
        recovery = self.operator_recovery(tenant_id, project_id, record_type, record_id)
        if recovery is None:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator recovery record is unavailable.")
        record = recovery["record"]
        if not isinstance(record, dict):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator recovery record is invalid.")
        self.write_operator_record(tenant_id, project_id, record_type, record)
        self._remove(tenant_id, project_id, f"projection-recovery/{record_type}--{record_id}.json")

    def remove_operator_recovery(self, tenant_id: str, project_id: str, record_type: str, record_id: str) -> None:
        self._remove(tenant_id, project_id, f"projection-recovery/{record_type}--{record_id}.json")

    def has_operator_recoveries(self, tenant_id: str, project_id: str) -> bool:
        recovery_root = self._path(tenant_id, project_id, "projection-recovery")
        if not recovery_root.exists():
            return False
        try:
            return any(recovery_root.iterdir())
        except OSError as exc:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator recovery records are unreadable.") from exc

    def has_any_operator_recoveries(self) -> bool:
        return any(
            self.has_operator_recoveries(registration.tenant_id, registration.project_id)
            for registration in self._registry.registrations
        )

    def _required(self, tenant_id: str, project_id: str, relative: str) -> dict[str, JsonValue]:
        value = self._optional(tenant_id, project_id, relative, None)
        if not isinstance(value, dict):
            raise RepositoryError("ERROR_DOMAIN_CONTRACT_FILE_MISSING", "Required projection is unavailable.")
        self._assert_identity(value, tenant_id, project_id)
        return copy.deepcopy(value)

    def _optional(self, tenant_id: str, project_id: str, relative: str, default: JsonValue | None) -> JsonValue | None:
        path = self._path(tenant_id, project_id, relative)
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Configured workspace projection is unreadable.") from exc

    def _write(self, tenant_id: str, project_id: str, relative: str, value: dict[str, JsonValue]) -> None:
        path = self._path(tenant_id, project_id, relative)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            os.replace(temporary, path)
        except OSError as exc:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Configured workspace projection cannot be written.") from exc

    def _remove(self, tenant_id: str, project_id: str, relative: str) -> None:
        path = self._path(tenant_id, project_id, relative)
        try:
            path.unlink()
        except OSError as exc:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Configured workspace recovery cannot be removed.") from exc

    def _path(self, tenant_id: str, project_id: str, relative: str) -> Path:
        root = self._registry.resolve(tenant_id, project_id)
        path = root / "v2/operator" / relative
        current = root
        for component in path.relative_to(root).parts:
            current = current / component
            if current.exists() and (current.is_symlink() or current.resolve() != current.absolute()):
                raise RepositoryError("ERR_TENANT_ISOLATION", "Configured workspace traverses a link or reparse point.")
        try:
            path.resolve(strict=False).relative_to(root)
        except ValueError as exc:
            raise RepositoryError("ERR_TENANT_ISOLATION", "Configured workspace path escapes its root.") from exc
        return path

    @staticmethod
    def _assert_identity(value: dict[str, JsonValue], tenant_id: str, project_id: str) -> None:
        if value.get("tenant_id") != tenant_id or value.get("project_id") != project_id:
            raise RepositoryError("ERR_TENANT_ISOLATION", "Workspace projection identity is mismatched.")
