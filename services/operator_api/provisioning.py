from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Final

from services.domain_contract.validator import validate_project

from .intake import ReviewedAcceptance
from .clock import Clock
from .models import JsonValue
from .package4 import Package4Error
from .repository import RepositoryError, WorkspaceRegistration, WorkspaceRegistry


_INITIAL_STEPS: Final = ("0", "1", "1b", "1c", "2", "3", "4a", "4b")
_INITIAL_RUN_ID: Final = "run-neutral-0001"
_OPERATOR_OWNER: Final = "Heartweb Admin Operator"
_INITIAL_NEXT_ACTION: Final = "Schritt 0 prüfen und starten"
_COLLECTIONS: Final = (
    "artifacts", "gates", "tasks", "tickets", "assignments", "context-packages", "llm-runs",
    "performance-checkpoints", "metrics", "adjustment-proposals", "integrations-status", "approvals",
)


class ProvisionedWorkspaceResolver(WorkspaceRegistry):
    def __init__(self, explicit: WorkspaceRegistry, provisioning_root: Path | None, enabled: bool) -> None:
        super().__init__(explicit.registrations)
        self._provisioning_root = provisioning_root
        self._provisioning_enabled = enabled

    def resolve(self, tenant_id: str, project_id: str) -> Path:
        self._validate_id(tenant_id, "tenant")
        self._validate_id(project_id, "project")
        for registration in self.registrations:
            if registration.tenant_id == tenant_id and registration.project_id == project_id:
                return self._safe_root(registration.workspace)
        return self._provisioned_workspace(tenant_id, project_id)

    def projects(self, tenant_id: str) -> tuple[WorkspaceRegistration, ...]:
        self._validate_id(tenant_id, "tenant")
        explicit = super().projects(tenant_id)
        if not self._provisioning_enabled or self._provisioning_root is None or not self._provisioning_root.exists():
            return explicit
        tenant_root = self._checked_directory(self._provisioning_root / tenant_id)
        if tenant_root is None:
            return explicit
        provisioned = tuple(
            WorkspaceRegistration(tenant_id, project_dir.name, self._provisioned_workspace(tenant_id, project_dir.name))
            for project_dir in tenant_root.iterdir()
            if (
                project_dir.is_dir()
                and not project_dir.is_symlink()
                and self._is_discoverable_id(project_dir.name, "project")
            )
        )
        duplicates = {item.project_id for item in explicit}.intersection(item.project_id for item in provisioned)
        if duplicates:
            raise RepositoryError("ERROR_DOMAIN_CONTRACT_INVALID", "Workspace identity is registered and provisioned twice.")
        return explicit + provisioned

    def all_projects(self) -> tuple[WorkspaceRegistration, ...]:
        tenants = {registration.tenant_id for registration in self.registrations}
        if self._provisioning_enabled and self._provisioning_root is not None and self._provisioning_root.exists():
            tenants.update(
                path.name
                for path in self._provisioning_root.iterdir()
                if path.is_dir() and not path.is_symlink() and self._is_discoverable_id(path.name, "tenant")
            )
        return tuple(registration for tenant_id in sorted(tenants) for registration in self.projects(tenant_id))

    def _is_discoverable_id(self, value: str, prefix: str) -> bool:
        try:
            self._validate_id(value, prefix)
        except RepositoryError:
            return False
        return True

    def provisioned_target(self, tenant_id: str, project_id: str) -> Path:
        self._validate_id(tenant_id, "tenant")
        self._validate_id(project_id, "project")
        root = self._root_for_provisioning()
        return root / tenant_id / project_id

    def managed_workspace_for_deletion(self, tenant_id: str, project_id: str) -> Path:
        """Return only a provisioned workspace owned by this Operator instance."""
        self._validate_id(tenant_id, "tenant")
        self._validate_id(project_id, "project")
        if any(
            registration.tenant_id == tenant_id and registration.project_id == project_id
            for registration in self.registrations
        ):
            raise RepositoryError(
                "ERROR_PROJECT_DELETE_NOT_MANAGED",
                "Explicitly registered workspaces cannot be deleted by the Operator Console.",
            )
        workspace = self._checked_directory(self.provisioned_target(tenant_id, project_id))
        if workspace is None:
            raise RepositoryError("ERR_TENANT_ISOLATION", "Tenant and project are not configured.")
        project = _read_canonical_project(workspace)
        if project.get("tenant_id") != tenant_id or project.get("project_id") != project_id:
            raise RepositoryError("ERR_TENANT_ISOLATION", "Provisioned workspace identity is mismatched.")
        return workspace

    def project_deletion_audit_root(self) -> Path:
        """Return the server-owned path for minimal deletion tombstones."""
        return self._root_for_provisioning() / ".heartweb-project-deletions" / "v1"

    def _provisioned_workspace(self, tenant_id: str, project_id: str) -> Path:
        if not self._provisioning_enabled or self._provisioning_root is None:
            raise RepositoryError("ERR_TENANT_ISOLATION", "Tenant and project are not configured.")
        workspace = self.provisioned_target(tenant_id, project_id)
        checked = self._checked_directory(workspace)
        if checked is None:
            raise RepositoryError("ERR_TENANT_ISOLATION", "Tenant and project are not configured.")
        project = _read_canonical_project(checked)
        if project.get("tenant_id") != tenant_id or project.get("project_id") != project_id:
            raise RepositoryError("ERR_TENANT_ISOLATION", "Provisioned workspace identity is mismatched.")
        return checked

    def _root_for_provisioning(self) -> Path:
        if not self._provisioning_enabled or self._provisioning_root is None:
            raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Provisioning mode is disabled.")
        root = self._provisioning_root.absolute()
        if root.exists() and (root.is_symlink() or not root.is_dir()):
            raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Provisioning root is unsafe.")
        return root

    @staticmethod
    def _checked_directory(path: Path) -> Path | None:
        if not path.exists():
            return None
        try:
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise RepositoryError("ERROR_OUTPUT_ROOT_INVALID", "Provisioned workspace is inaccessible.") from exc
        if path.is_symlink() or not resolved.is_dir() or resolved != path.absolute():
            raise RepositoryError("ERR_TENANT_ISOLATION", "Provisioned workspace traverses a link or reparse point.")
        return resolved


class WorkspaceProvisioner:
    def __init__(self, resolver: ProvisionedWorkspaceResolver, repository_root: Path, clock: Clock) -> None:
        self._resolver = resolver
        self._repository_root = repository_root
        self._clock = clock

    def provision(self, tenant_id: str, accepted: ReviewedAcceptance) -> dict[str, str]:
        reviewed = accepted.reviewed
        project_id = reviewed.project_id
        project_v2 = reviewed.project_v2
        project_name = reviewed.project_name
        if project_id is None or project_v2 is None or project_name is None:
            raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Reviewed intake is incomplete.")
        target = self._resolver.provisioned_target(tenant_id, project_id)
        self._reject_existing(tenant_id, project_id, target)
        validation = validate_project(project_v2, root=self._repository_root)
        if not validation["valid"]:
            raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Reviewed Project V2 does not satisfy the domain contract.")
        if project_v2.get("project_id") != project_id or project_v2.get("tenant", {}).get("tenant_id") != tenant_id:
            raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Project V2 identity does not match the reviewed intake.")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.parent.is_symlink():
            raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Provisioning path is unsafe.")
        temporary = Path(tempfile.mkdtemp(prefix=f".{project_id}-", dir=target.parent))
        try:
            self._write_workspace(temporary, tenant_id, project_id, project_name, accepted, project_v2, self._clock.now())
            if target.exists():
                raise Package4Error("ERR_IDEMPOTENCY_CONFLICT", "Provisioned workspace already exists.")
            os.replace(temporary, target)
        except OSError as exc:
            raise Package4Error("ERROR_CONTEXT_SOURCE_INVALID", "Provisioned workspace cannot be written.") from exc
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
        return {"tenant_id": tenant_id, "project_id": project_id}

    def _reject_existing(self, tenant_id: str, project_id: str, target: Path) -> None:
        if target.exists():
            raise Package4Error("ERR_IDEMPOTENCY_CONFLICT", "Provisioned workspace already exists.")
        for registration in self._resolver.registrations:
            if registration.tenant_id == tenant_id and registration.project_id == project_id:
                raise Package4Error("ERR_IDEMPOTENCY_CONFLICT", "Workspace is already explicitly registered.")

    def _write_workspace(self, workspace: Path, tenant_id: str, project_id: str, project_name: str, accepted: ReviewedAcceptance, project_v2: dict[str, JsonValue], created_at: str) -> None:
        operator = workspace / "v2/operator"
        customer = project_v2.get("customer")
        customer_name = customer.get("name") if isinstance(customer, dict) else None
        if not isinstance(customer_name, str) or customer_name == "":
            raise Package4Error("ERROR_CONTEXT_SCHEMA_INVALID", "Reviewed Project V2 customer is unavailable.")
        deployment_id = _primary_active_deployment_id(project_v2)
        project = {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "name": project_name,
            "customer": customer_name,
            "current_step": "0",
            "progress": "0 von 8 Schritten",
            "blocker_count": 0,
            "owner": _OPERATOR_OWNER,
            "next_action": _INITIAL_NEXT_ACTION,
        }
        initial_run = {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "deployment_id": deployment_id,
            "run_id": _INITIAL_RUN_ID,
            "step_id": "0",
            "gate_id": "GATE-0",
            "revision": 1,
            "input_hash": accepted.source_sha256,
            "status": "pending",
            "attempt": 1,
            "created_at": created_at,
            "gate_context": {"local_workflow": True},
        }
        initial_step = {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_id": _INITIAL_RUN_ID,
            "step_id": "0",
            "status": "pending",
            "blocker": "Keine offenen Blocker",
            "next_action": _INITIAL_NEXT_ACTION,
        }
        _write(operator / "project.json", project)
        _write(operator / "project-v2.json", project_v2)
        intake = {"tenant_id": tenant_id, "project_id": project_id, "markdown": accepted.markdown, "source_sha256": accepted.source_sha256, "reviewed": accepted.reviewed.model_dump(mode="json"), "accepted_by": accepted.actor_id, "accepted_at": accepted.accepted_at}
        if accepted.generation is not None:
            intake["generation"] = accepted.generation.model_dump(mode="json")
        _write(operator / "intake.json", intake)
        _write(operator / "logical-session.json", _logical_session(tenant_id, project_id, accepted.actor_id, intake))
        _write(operator / "workflow.json", _workflow(tenant_id, project_id))
        _write(operator / "steps.json", [initial_step])
        _write(operator / f"runs/{_INITIAL_RUN_ID}.json", initial_run)
        for collection in _COLLECTIONS:
            _write(operator / f"{collection}.json", [])


def _primary_active_deployment_id(project_v2: dict[str, JsonValue]) -> str:
    deployments = project_v2.get("market_deployments")
    matches = [
        deployment
        for deployment in deployments
        if isinstance(deployment, dict)
        and deployment.get("market_phase") == "active"
        and deployment.get("deployment_role") == "primary"
    ] if isinstance(deployments, list) else []
    if len(matches) != 1 or not isinstance(matches[0].get("deployment_id"), str):
        raise Package4Error(
            "ERROR_CONTEXT_SCHEMA_INVALID",
            "Project provisioning requires exactly one active primary deployment.",
        )
    return matches[0]["deployment_id"]  # type: ignore[return-value]


def _read_canonical_project(workspace: Path) -> dict[str, JsonValue]:
    path = workspace / "v2/operator/project.json"
    try:
        raw = path.read_text(encoding="utf-8")
        project = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Provisioned workspace project projection is unreadable.") from exc
    if not isinstance(project, dict) or raw != _canonical_json(project):
        raise RepositoryError("ERR_TENANT_ISOLATION", "Provisioned workspace project identity is not canonical.")
    return project


def _write(path: Path, value: JsonValue) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical_json(value), encoding="utf-8")


def _canonical_json(value: JsonValue) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _logical_session(tenant_id: str, project_id: str, actor_id: str, intake: dict[str, JsonValue]) -> dict[str, JsonValue]:
    content_sha256 = hashlib.sha256(_canonical_json(intake).encode("utf-8")).hexdigest()
    source_id = f"intake-{content_sha256[:12]}"
    return {"logical_session_id": "logical-session-neutral-0001", "schema_version": "1.0.0", "session_revision": 1, "tenant_id": tenant_id, "project_id": project_id, "binding_mode": "project_intake", "project_source": {"source_kind": "project_intake", "source_id": source_id, "revision": 1, "logical_ref": f"runtime:intake/{source_id}", "content_sha256": content_sha256}, "created_at": intake["accepted_at"], "created_by": actor_id, "state_authority": "local_core", "technical_session_policy": {"default_execution": "fresh_per_step_or_substantial_revision", "reuse_allowed": True, "reuse_authority": "cache_only", "lost_handle_recovery": "rebuild_from_context_package"}}


def _workflow(tenant_id: str, project_id: str) -> dict[str, JsonValue]:
    return {"tenant_id": tenant_id, "project_id": project_id, "initial_edges": [{"from_step_id": before, "to_step_id": after} for before, after in zip(_INITIAL_STEPS[:-1], _INITIAL_STEPS[1:], strict=True)], "sideflows": [{"step_id": "3b", "status": "not_due"}]}
