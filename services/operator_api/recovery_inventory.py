from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from .repository import RepositoryError, WorkspaceRegistration, WorkspaceRegistry


_FAMILIES: Final = (
    "projection-recovery",
    "transition-recovery",
    "runtime-recovery",
    "artifact-recovery",
    "next-run-recovery",
)


@dataclass(frozen=True, slots=True)
class RecoverySidecar:
    tenant_id: str
    project_id: str
    family: str
    relative_path: str


@dataclass(frozen=True, slots=True)
class RecoveryReplayIdentity:
    tenant_id: str
    project_id: str
    family: str
    relative_path: str

    def sidecar(self) -> RecoverySidecar:
        return RecoverySidecar(self.tenant_id, self.project_id, self.family, self.relative_path)


@dataclass(frozen=True, slots=True)
class RecoveryAuthorization:
    replay: RecoveryReplayIdentity | None


@dataclass(frozen=True, slots=True)
class RecoveryInventory:
    resolver: WorkspaceRegistry

    def sidecars(self) -> tuple[RecoverySidecar, ...]:
        records: list[RecoverySidecar] = []
        for registration in self._workspaces():
            records.extend(self._workspace_sidecars(registration))
        return tuple(records)

    def blocked(self) -> bool:
        return bool(self.sidecars())

    def authorize(self, replay: RecoveryReplayIdentity | None = None) -> RecoveryAuthorization:
        pending = self.sidecars()
        if not pending:
            return RecoveryAuthorization(None)
        if replay is None or pending != (replay.sidecar(),):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator API recovery is pending.")
        return RecoveryAuthorization(replay)

    def _workspaces(self) -> tuple[WorkspaceRegistration, ...]:
        all_projects = getattr(self.resolver, "all_projects", None)
        if callable(all_projects):
            return all_projects()
        return self.resolver.registrations

    def _workspace_sidecars(self, registration: WorkspaceRegistration) -> tuple[RecoverySidecar, ...]:
        root = self.resolver.resolve(registration.tenant_id, registration.project_id) / "v2" / "operator"
        records: list[RecoverySidecar] = []
        for family in _FAMILIES:
            directory = root / family
            try:
                if directory.exists() and not directory.is_dir():
                    raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Recovery directory is invalid.")
                if directory.exists():
                    records.extend(
                        RecoverySidecar(registration.tenant_id, registration.project_id, family, str(path.relative_to(root)))
                        for path in directory.iterdir()
                        if path.is_file() and not path.is_symlink()
                    )
            except OSError as exc:
                raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Recovery records are unreadable.") from exc
        return tuple(records)
