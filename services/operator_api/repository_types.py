"""Low-level workspace registry types for contained projections."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

_IDENTIFIER: Final = re.compile(r"^(tenant|project|run)-[a-z0-9][a-z0-9-]{2,63}$")


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
        if len({(item.tenant_id, item.project_id) for item in registrations}) != len(registrations):
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

    def all_projects(self) -> tuple[WorkspaceRegistration, ...]:
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
