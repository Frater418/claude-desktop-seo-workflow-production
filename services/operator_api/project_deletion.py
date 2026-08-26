"""Preview and confirm authority for destructive project deletion."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .clock import Clock
from .models import (
    ActionBlocker,
    JsonValue,
    ProjectDeletionConfirmRequest,
    ProjectDeletionPreviewData,
    ProjectDeletionResultData,
)
from .package4 import Package4Error
from .provisioning import ProvisionedWorkspaceResolver
from .repository import ProjectRepository, RepositoryError


_ACTIVE_EXECUTION_STATUSES = frozenset({"prepared", "running", "interaction_required", "approval_required"})


class ProjectDeletionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class WorkspaceInventory:
    workspace_sha256: str
    file_count: int
    total_bytes: int
    run_count: int
    artifact_count: int
    release_count: int
    active_run_ids: tuple[str, ...]
    active_execution_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectDeletionBinding:
    preview: ProjectDeletionPreviewData
    workspace: Path


class ProjectDeletionService:
    """Delete only server-managed provisioned workspaces after a hash-bound preview."""

    def __init__(
        self,
        repository: ProjectRepository,
        resolver: ProvisionedWorkspaceResolver,
        clock: Clock,
        operator_id: str,
    ) -> None:
        self._repository = repository
        self._resolver = resolver
        self._clock = clock
        self._operator_id = operator_id
        self._previews: dict[str, ProjectDeletionBinding] = {}
        self._results: dict[str, ProjectDeletionResultData] = {}
        self._lock = threading.RLock()

    def preview(self, tenant_id: str, project_id: str) -> ProjectDeletionPreviewData:
        with self._lock:
            workspace = self._managed_workspace(tenant_id, project_id)
            project = self._repository.project(tenant_id, project_id)
            project_name = _required_string(project, "name")
            customer_name = _required_string(project, "customer")
            current_step = _required_string(project, "current_step")
            inventory = _inventory(workspace, tenant_id, project_id)
            blockers = _blockers(inventory)
            previewed_at = self._clock.now()
            preview_hash = _sha256(
                {
                    "tenant_id": tenant_id,
                    "project_id": project_id,
                    "project_name": project_name,
                    "customer_name": customer_name,
                    "current_step": current_step,
                    "operator_id": self._operator_id,
                    "previewed_at": previewed_at,
                    **_inventory_payload(inventory),
                }
            )
            preview = ProjectDeletionPreviewData(
                tenant_id=tenant_id,
                project_id=project_id,
                project_name=project_name,
                customer_name=customer_name,
                current_step=current_step,
                file_count=inventory.file_count,
                total_bytes=inventory.total_bytes,
                run_count=inventory.run_count,
                artifact_count=inventory.artifact_count,
                release_count=inventory.release_count,
                active_run_ids=inventory.active_run_ids,
                active_execution_ids=inventory.active_execution_ids,
                allowed=not blockers,
                blockers=blockers,
                preview_hash=preview_hash,
                workspace_sha256=inventory.workspace_sha256,
                previewed_at=previewed_at,
            )
            self._previews[preview_hash] = ProjectDeletionBinding(preview=preview, workspace=workspace)
            return preview

    def confirm(
        self,
        tenant_id: str,
        project_id: str,
        request: ProjectDeletionConfirmRequest,
    ) -> ProjectDeletionResultData:
        with self._lock:
            deletion_id = _deletion_id(tenant_id, project_id, request.idempotency_key)
            existing = self._replay_result(tenant_id, project_id, deletion_id, request.preview_hash)
            if existing is not None:
                return existing.model_copy(update={"replay": True})
            binding = self._previews.get(request.preview_hash)
            if (
                not isinstance(binding, ProjectDeletionBinding)
                or binding.preview.tenant_id != tenant_id
                or binding.preview.project_id != project_id
            ):
                raise ProjectDeletionError(
                    "ERROR_PROJECT_DELETE_PREVIEW_STALE",
                    "Project deletion preview is unavailable or does not match this project.",
                )
            if not binding.preview.allowed:
                raise ProjectDeletionError(
                    "ERROR_PROJECT_DELETE_ACTIVE_RUN",
                    "Project deletion is blocked while a workflow run or production execution is active.",
                )
            workspace = self._managed_workspace(tenant_id, project_id)
            if workspace != binding.workspace:
                raise ProjectDeletionError(
                    "ERROR_PROJECT_DELETE_PREVIEW_STALE",
                    "Project workspace binding changed after the deletion preview.",
                )
            current = _inventory(workspace, tenant_id, project_id)
            if _inventory_payload(current) != _preview_inventory_payload(binding.preview):
                raise ProjectDeletionError(
                    "ERROR_PROJECT_DELETE_PREVIEW_STALE",
                    "Project content changed after the deletion preview. Create a new preview before deleting.",
                )
            if current.active_run_ids or current.active_execution_ids:
                raise ProjectDeletionError(
                    "ERROR_PROJECT_DELETE_ACTIVE_RUN",
                    "Project deletion is blocked while a workflow run or production execution is active.",
                )
            deleted_at = self._clock.now()
            result = ProjectDeletionResultData(
                tenant_id=tenant_id,
                project_id=project_id,
                project_name=binding.preview.project_name,
                deletion_id=deletion_id,
                deleted_at=deleted_at,
                deleted=True,
                replay=False,
                deleted_file_count=current.file_count,
                deleted_total_bytes=current.total_bytes,
                readback_urls=(
                    f"/v1/tenants/{tenant_id}/projects",
                    f"/v1/tenants/{tenant_id}/projects/{project_id}",
                ),
            )
            staging = workspace.parent / f".{project_id}.deleting-{deletion_id[-12:]}"
            if staging.exists():
                raise ProjectDeletionError(
                    "ERROR_PROJECT_DELETE_RECOVERY_REQUIRED",
                    "A previous project deletion requires manual recovery before this project can be deleted.",
                )
            tombstone = {
                "schema_version": "1.0.0",
                "status": "prepared",
                "preview_hash": request.preview_hash,
                "idempotency_key": request.idempotency_key,
                "confirmation_text": request.confirmation_text,
                "requested_by": self._operator_id,
                "staging_name": staging.name,
                **result.model_dump(mode="json"),
            }
            tombstone_path = self._tombstone_path(tenant_id, project_id, deletion_id)
            _write_canonical(tombstone_path, tombstone)
            try:
                os.replace(workspace, staging)
                shutil.rmtree(staging)
            except OSError as error:
                if staging.exists() and not workspace.exists():
                    try:
                        os.replace(staging, workspace)
                    except OSError:
                        pass
                tombstone_path.unlink(missing_ok=True)
                raise ProjectDeletionError(
                    "ERROR_PROJECT_DELETE_FAILED",
                    "Project files could not be deleted safely.",
                ) from error
            if workspace.exists() or staging.exists():
                raise ProjectDeletionError(
                    "ERROR_PROJECT_DELETE_FAILED",
                    "Project deletion did not remove the complete managed workspace.",
                )
            completed = {**tombstone, "status": "completed"}
            _write_canonical(tombstone_path, completed)
            self._results[deletion_id] = result
            self._previews = {
                key: value
                for key, value in self._previews.items()
                if value.preview.tenant_id != tenant_id or value.preview.project_id != project_id
            }
            if any(item.project_id == project_id for item in self._resolver.projects(tenant_id)):
                raise ProjectDeletionError(
                    "ERROR_PROJECT_DELETE_FAILED",
                    "Deleted project remains visible in the canonical project registry.",
                )
            return result

    def _managed_workspace(self, tenant_id: str, project_id: str) -> Path:
        try:
            return self._resolver.managed_workspace_for_deletion(tenant_id, project_id)
        except RepositoryError as error:
            if error.code == "ERROR_PROJECT_DELETE_NOT_MANAGED":
                raise ProjectDeletionError(error.code, error.message) from error
            if error.code == "ERR_TENANT_ISOLATION":
                raise ProjectDeletionError("ERROR_PROJECT_DELETE_NOT_FOUND", "Project is unavailable.") from error
            raise ProjectDeletionError("ERROR_PROJECT_DELETE_INVENTORY_INVALID", error.message) from error
        except Package4Error as error:
            raise ProjectDeletionError("ERROR_PROJECT_DELETE_NOT_MANAGED", error.message) from error

    def _tombstone_path(self, tenant_id: str, project_id: str, deletion_id: str) -> Path:
        try:
            root = self._resolver.project_deletion_audit_root()
        except Package4Error as error:
            raise ProjectDeletionError("ERROR_PROJECT_DELETE_NOT_MANAGED", error.message) from error
        return root / tenant_id / project_id / f"{deletion_id}.json"

    def _replay_result(
        self,
        tenant_id: str,
        project_id: str,
        deletion_id: str,
        preview_hash: str,
    ) -> ProjectDeletionResultData | None:
        in_memory = self._results.get(deletion_id)
        if in_memory is not None:
            return in_memory
        path = self._tombstone_path(tenant_id, project_id, deletion_id)
        if not path.exists():
            return None
        record = _read_object(path)
        if record.get("preview_hash") != preview_hash:
            raise ProjectDeletionError(
                "ERR_IDEMPOTENCY_CONFLICT",
                "Project deletion idempotency identity conflicts with the stored deletion.",
            )
        if record.get("status") != "completed":
            raise ProjectDeletionError(
                "ERROR_PROJECT_DELETE_RECOVERY_REQUIRED",
                "A previous project deletion did not reach a verified terminal state.",
            )
        try:
            result = ProjectDeletionResultData.model_validate(
                {key: record[key] for key in ProjectDeletionResultData.model_fields}
            )
        except (KeyError, ValueError) as error:
            raise ProjectDeletionError(
                "ERROR_PROJECT_DELETE_INVENTORY_INVALID",
                "Stored project deletion record is invalid.",
            ) from error
        self._results[deletion_id] = result
        return result


def _blockers(inventory: WorkspaceInventory) -> tuple[ActionBlocker, ...]:
    if inventory.active_run_ids or inventory.active_execution_ids:
        return (
            ActionBlocker(
                code="ERROR_PROJECT_DELETE_ACTIVE_RUN",
                message="Ein Workflow-Lauf oder eine Produktionsausführung ist noch aktiv.",
                remediation="Warte auf einen terminalen Status oder beende den aktiven Lauf kontrolliert, bevor du das Projekt löschst.",
            ),
        )
    return ()


def _inventory(workspace: Path, tenant_id: str, project_id: str) -> WorkspaceInventory:
    workspace_sha256, file_count, total_bytes = _workspace_digest(workspace)
    operator = workspace / "v2/operator"
    runs_root = operator / "runs"
    active_runs: list[str] = []
    run_count = 0
    if runs_root.exists():
        for path in sorted(runs_root.glob("*.json")):
            run = _read_object(path)
            if run.get("tenant_id") != tenant_id or run.get("project_id") != project_id:
                raise ProjectDeletionError("ERROR_PROJECT_DELETE_INVENTORY_INVALID", "Project run identity is invalid.")
            run_id = run.get("run_id")
            status_value = run.get("status")
            if not isinstance(run_id, str) or not isinstance(status_value, str):
                raise ProjectDeletionError("ERROR_PROJECT_DELETE_INVENTORY_INVALID", "Project run record is invalid.")
            run_count += 1
            if status_value == "in_progress":
                active_runs.append(run_id)
    artifacts_path = operator / "artifacts.json"
    artifact_count = len(_read_list(artifacts_path)) if artifacts_path.exists() else 0
    releases_root = operator / "releases"
    release_count = len(tuple(releases_root.glob("*.json"))) if releases_root.exists() else 0
    active_executions: list[str] = []
    executions_root = operator / "production-executions/v1"
    if executions_root.exists():
        for path in sorted(executions_root.glob("production-execution-*.json")):
            execution = _read_object(path)
            if execution.get("tenant_id") != tenant_id or execution.get("project_id") != project_id:
                raise ProjectDeletionError("ERROR_PROJECT_DELETE_INVENTORY_INVALID", "Production execution identity is invalid.")
            execution_id = execution.get("execution_id")
            execution_status = execution.get("status")
            if not isinstance(execution_id, str) or not isinstance(execution_status, str):
                raise ProjectDeletionError("ERROR_PROJECT_DELETE_INVENTORY_INVALID", "Production execution record is invalid.")
            if execution_status in _ACTIVE_EXECUTION_STATUSES:
                active_executions.append(execution_id)
    return WorkspaceInventory(
        workspace_sha256=workspace_sha256,
        file_count=file_count,
        total_bytes=total_bytes,
        run_count=run_count,
        artifact_count=artifact_count,
        release_count=release_count,
        active_run_ids=tuple(sorted(active_runs)),
        active_execution_ids=tuple(sorted(active_executions)),
    )


def _workspace_digest(workspace: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    file_count = 0
    total_bytes = 0
    try:
        root = workspace.resolve(strict=True)
    except OSError as error:
        raise ProjectDeletionError("ERROR_PROJECT_DELETE_NOT_FOUND", "Project workspace is unavailable.") from error
    if workspace.is_symlink() or _is_reparse(os.lstat(workspace)) or not root.is_dir():
        raise ProjectDeletionError("ERROR_PROJECT_DELETE_INVENTORY_INVALID", "Project workspace root is unsafe.")
    for current_root, directory_names, file_names in os.walk(root, topdown=True, followlinks=False):
        current = Path(current_root)
        directory_names.sort()
        file_names.sort()
        for name in tuple(directory_names):
            path = current / name
            metadata = os.lstat(path)
            if stat.S_ISLNK(metadata.st_mode) or _is_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
                raise ProjectDeletionError("ERROR_PROJECT_DELETE_INVENTORY_INVALID", "Project workspace contains an unsafe directory.")
            relative = path.relative_to(root).as_posix()
            digest.update(b"D\0" + relative.encode("utf-8") + b"\0")
        for name in file_names:
            path = current / name
            metadata = os.lstat(path)
            if stat.S_ISLNK(metadata.st_mode) or _is_reparse(metadata) or not stat.S_ISREG(metadata.st_mode):
                raise ProjectDeletionError("ERROR_PROJECT_DELETE_INVENTORY_INVALID", "Project workspace contains an unsafe file.")
            relative = path.relative_to(root).as_posix()
            digest.update(b"F\0" + relative.encode("utf-8") + b"\0")
            with path.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
            digest.update(b"\0")
            file_count += 1
            total_bytes += metadata.st_size
    return digest.hexdigest(), file_count, total_bytes


def _is_reparse(metadata: os.stat_result) -> bool:
    attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _preview_inventory_payload(preview: ProjectDeletionPreviewData) -> dict[str, JsonValue]:
    return {
        "workspace_sha256": preview.workspace_sha256,
        "file_count": preview.file_count,
        "total_bytes": preview.total_bytes,
        "run_count": preview.run_count,
        "artifact_count": preview.artifact_count,
        "release_count": preview.release_count,
        "active_run_ids": list(preview.active_run_ids),
        "active_execution_ids": list(preview.active_execution_ids),
    }


def _inventory_payload(inventory: WorkspaceInventory) -> dict[str, JsonValue]:
    return {
        "workspace_sha256": inventory.workspace_sha256,
        "file_count": inventory.file_count,
        "total_bytes": inventory.total_bytes,
        "run_count": inventory.run_count,
        "artifact_count": inventory.artifact_count,
        "release_count": inventory.release_count,
        "active_run_ids": list(inventory.active_run_ids),
        "active_execution_ids": list(inventory.active_execution_ids),
    }


def _deletion_id(tenant_id: str, project_id: str, idempotency_key: str) -> str:
    return f"project-deletion-{_sha256({'tenant_id': tenant_id, 'project_id': project_id, 'idempotency_key': idempotency_key})[:24]}"


def _required_string(record: Mapping[str, JsonValue], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or value == "":
        raise ProjectDeletionError("ERROR_PROJECT_DELETE_INVENTORY_INVALID", "Project summary is invalid.")
    return value


def _read_object(path: Path) -> dict[str, JsonValue]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProjectDeletionError("ERROR_PROJECT_DELETE_INVENTORY_INVALID", "Project deletion inventory contains invalid JSON.") from error
    if not isinstance(value, dict):
        raise ProjectDeletionError("ERROR_PROJECT_DELETE_INVENTORY_INVALID", "Project deletion inventory contains a non-object record.")
    return value


def _read_list(path: Path) -> list[JsonValue]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProjectDeletionError("ERROR_PROJECT_DELETE_INVENTORY_INVALID", "Project deletion inventory contains invalid JSON.") from error
    if not isinstance(value, list):
        raise ProjectDeletionError("ERROR_PROJECT_DELETE_INVENTORY_INVALID", "Project deletion inventory contains a non-list projection.")
    return value


def _write_canonical(path: Path, value: Mapping[str, JsonValue]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        for parent in (path.parent, *path.parents[:3]):
            if parent.exists() and (parent.is_symlink() or _is_reparse(os.lstat(parent)) or not parent.is_dir()):
                raise OSError("unsafe deletion audit path")
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    except OSError as error:
        raise ProjectDeletionError("ERROR_PROJECT_DELETE_AUDIT_FAILED", "Project deletion audit record could not be written.") from error


def _sha256(value: Mapping[str, JsonValue]) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
