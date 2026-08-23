from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Final

from .repository import RepositoryError, WorkspaceRegistration, WorkspaceRegistry


_FAMILIES: Final = (
    "projection-recovery",
    "transition-recovery",
    "runtime-recovery",
    "artifact-recovery",
    "next-run-recovery",
    "delivery-recovery",
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
        return tuple(sorted(records, key=lambda item: (item.tenant_id, item.project_id, item.family, item.relative_path)))

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
        workspace = self._workspace_root(registration)
        root = workspace
        for component in ("v2", "operator"):
            root = root / component
            if not self._directory(root, workspace):
                return ()
        records: list[RecoverySidecar] = []
        for family in _FAMILIES:
            directory = root
            for component in PurePosixPath(self._family_directory(family)).parts:
                directory = directory / component
                if not self._directory(directory, root):
                    break
            else:
                try:
                    entries = tuple(sorted(os.scandir(directory), key=lambda entry: entry.name))
                except OSError as exc:
                    raise self._invalid_inventory() from exc
                for entry in entries:
                    path = directory / entry.name
                    self._regular_file(path, root)
                    try:
                        relative_path = path.relative_to(root).as_posix()
                    except ValueError as exc:
                        raise self._invalid_inventory() from exc
                    records.append(RecoverySidecar(registration.tenant_id, registration.project_id, family, relative_path))
        return tuple(records)

    def _workspace_root(self, registration: WorkspaceRegistration) -> Path:
        try:
            return self.resolver.resolve(registration.tenant_id, registration.project_id)
        except RepositoryError as exc:
            raise self._invalid_inventory() from exc

    @classmethod
    def _directory(cls, path: Path, containment_root: Path) -> bool:
        metadata = cls._lstat(path, absent_allowed=True)
        if metadata is None:
            return False
        if cls._link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
            raise cls._invalid_inventory()
        cls._resolved_path(path, containment_root, metadata)
        return True

    @classmethod
    def _regular_file(cls, path: Path, containment_root: Path) -> None:
        metadata = cls._lstat(path, absent_allowed=False)
        if metadata is None or cls._link_or_reparse(metadata) or not stat.S_ISREG(metadata.st_mode):
            raise cls._invalid_inventory()
        cls._resolved_path(path, containment_root, metadata)

    @classmethod
    def _resolved_path(cls, path: Path, containment_root: Path, metadata: os.stat_result) -> None:
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(containment_root)
            current = os.stat(path)
        except (OSError, RuntimeError, ValueError) as exc:
            raise cls._invalid_inventory() from exc
        if resolved != path.absolute() or (current.st_dev, current.st_ino) != (metadata.st_dev, metadata.st_ino):
            raise cls._invalid_inventory()

    @staticmethod
    def _lstat(path: Path, absent_allowed: bool) -> os.stat_result | None:
        try:
            return os.lstat(path)
        except FileNotFoundError as exc:
            if absent_allowed:
                return None
            raise RecoveryInventory._invalid_inventory() from exc
        except OSError as exc:
            raise RecoveryInventory._invalid_inventory() from exc

    @staticmethod
    def _link_or_reparse(metadata: os.stat_result) -> bool:
        return stat.S_ISLNK(metadata.st_mode) or bool(getattr(metadata, "st_file_attributes", 0) & 0x400)

    @staticmethod
    def _invalid_inventory() -> RepositoryError:
        return RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator API recovery inventory is invalid.")

    @staticmethod
    def _family_directory(family: str) -> str:
        return "delivery/recovery" if family == "delivery-recovery" else family
