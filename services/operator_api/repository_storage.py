"""Contained filesystem JSON storage and path containment mechanics."""

from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path

from .models import JsonValue
from .repository_types import RepositoryError, WorkspaceRegistry


class RepositoryStorage:
    """Shared contained JSON storage implementation for repository mixins."""

    _registry: WorkspaceRegistry

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

    def _write(self, tenant_id: str, project_id: str, relative: str, value: JsonValue) -> None:
        path = self._path(tenant_id, project_id, relative)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                    output.write(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, path)
            except OSError:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass
                raise
        except OSError as exc:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Configured workspace projection cannot be written.") from exc

    def _remove(self, tenant_id: str, project_id: str, relative: str) -> None:
        try:
            self._path(tenant_id, project_id, relative).unlink()
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
