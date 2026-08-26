"""Public repository facade over contained Operator projections."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Final

from .models import CurrentRunResponse, JsonValue
from .repository_operator_records import OperatorRecordPersistence
from .repository_runtime import RuntimeProjectionPersistence
from .repository_storage import RepositoryStorage
from .repository_types import RepositoryError, WorkspaceRegistration, WorkspaceRegistry

if TYPE_CHECKING:
    from .delivery_repository import DeliverySnapshot

_COLLECTIONS = frozenset({"steps", "tasks", "tickets", "assignments", "context-packages", "llm-runs", "performance-checkpoints", "metrics", "adjustment-proposals", "integrations-status", "approvals"})
_INITIAL_ROUTE: Final = ("0", "1", "1b", "1c", "2", "3", "4a", "4b")
_RUN_STATUSES: Final = frozenset({"pending", "in_progress", "awaiting_gate", "approved", "completed", "failed", "superseded"})


class ProjectRepository(RuntimeProjectionPersistence, OperatorRecordPersistence, RepositoryStorage):
    """Read and write controlled records below one registered workspace."""

    def __init__(self, registry: WorkspaceRegistry) -> None:
        self._registry = registry

    def workspace(self, tenant_id: str, project_id: str) -> Path:
        return self._registry.resolve(tenant_id, project_id)

    def list_projects(self, tenant_id: str) -> list[dict[str, JsonValue]]:
        return [self.project(item.tenant_id, item.project_id) for item in self._registry.projects(tenant_id)]

    def project(self, tenant_id: str, project_id: str) -> dict[str, JsonValue]:
        return self._required(tenant_id, project_id, "project.json")

    def logical_session(self, tenant_id: str, project_id: str) -> dict[str, JsonValue]:
        return self._required(tenant_id, project_id, "logical-session.json")

    def workflow(self, tenant_id: str, project_id: str) -> dict[str, JsonValue]:
        return self._required(tenant_id, project_id, "workflow.json")

    def intake(self, tenant_id: str, project_id: str) -> dict[str, JsonValue]:
        return self._required(tenant_id, project_id, "intake.json")

    def project_v2(self, tenant_id: str, project_id: str) -> dict[str, JsonValue]:
        project = self._optional(tenant_id, project_id, "project-v2.json", None)
        if not isinstance(project, dict) or project.get("project_id") != project_id:
            raise RepositoryError("ERROR_DOMAIN_CONTRACT_FILE_MISSING", "Required Project V2 is unavailable.")
        tenant = project.get("tenant")
        if not isinstance(tenant, dict) or tenant.get("tenant_id") != tenant_id:
            raise RepositoryError("ERR_TENANT_ISOLATION", "Project V2 identity is mismatched.")
        return copy.deepcopy(project)

    def delivery_snapshot(self, tenant_id: str, project_id: str) -> DeliverySnapshot:
        from .delivery_repository import DeliverySnapshotRepository

        return DeliverySnapshotRepository(self._registry).snapshot(tenant_id, project_id)

    def source_bytes(self, tenant_id: str, project_id: str, source: str) -> bytes:
        relative = {"intake": "intake.json", "project_v2": "project-v2.json"}.get(source)
        if relative is None:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Runtime source is invalid.")
        try:
            return self._path(tenant_id, project_id, relative).read_bytes()
        except OSError as exc:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Runtime source is unavailable.") from exc

    def released_artifact_bytes(self, tenant_id: str, project_id: str, release: dict[str, JsonValue]) -> bytes:
        artifact_id = release.get("artifact_id")
        if not isinstance(artifact_id, str):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Released artifact identity is malformed.")
        try:
            content = self._path(tenant_id, project_id, f"artifact-content/{artifact_id}.md").read_bytes()
        except OSError as exc:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Released artifact content is unavailable.") from exc
        if hashlib.sha256(content).hexdigest() != release.get("artifact_sha256"):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Released artifact content hash is invalid.")
        return content

    def artifact_bytes(self, tenant_id: str, project_id: str, artifact: dict[str, JsonValue]) -> bytes:
        artifact_id = artifact.get("artifact_id")
        if (
            not isinstance(artifact_id, str)
            or artifact.get("tenant_id") != tenant_id
            or artifact.get("project_id") != project_id
        ):
            raise RepositoryError("ERR_TENANT_ISOLATION", "Artifact identity is malformed or cross-project.")
        try:
            content = self._path(tenant_id, project_id, f"artifact-content/{artifact_id}.md").read_bytes()
        except OSError as exc:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Artifact content is unavailable.") from exc
        if hashlib.sha256(content).hexdigest() != artifact.get("content_sha256"):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Artifact content hash is invalid.")
        return content

    def run(self, tenant_id: str, project_id: str, run_id: str) -> dict[str, JsonValue]:
        WorkspaceRegistry._validate_id(run_id, "run")
        return self._required(tenant_id, project_id, f"runs/{run_id}.json")

    def current_run(self, tenant_id: str, project_id: str) -> CurrentRunResponse:
        records = self._current_run_records(tenant_id, project_id)
        furthest = max(_INITIAL_ROUTE.index(step_id) for step_id in records)
        required_steps = _INITIAL_ROUTE[:furthest + 1]
        if set(records) != set(required_steps):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Initial-route run records are discontinuous.")
        selected = records[_INITIAL_ROUTE[furthest]]
        return CurrentRunResponse(
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=selected["run_id"],
            step_id=selected["step_id"],
            expected_revision=selected["revision"],
        )

    def _current_run_records(self, tenant_id: str, project_id: str) -> dict[str, dict[str, str | int]]:
        root = self._path(tenant_id, project_id, "runs")
        if not root.exists() or not root.is_dir():
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run records are unavailable.")
        try:
            paths = tuple(sorted(root.iterdir()))
        except OSError as exc:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run records are unreadable.") from exc
        records: dict[str, dict[str, str | int]] = {}
        for path in paths:
            record = self._current_run_record(path, root, tenant_id, project_id)
            if record is None or record["status"] == "superseded" or record["step_id"] == "3b":
                continue
            step_id = record["step_id"]
            if step_id in records:
                raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run records are ambiguous.")
            records[step_id] = record
        if not records:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run records are unavailable.")
        return records

    @staticmethod
    def _current_run_record(
        path: Path,
        root: Path,
        tenant_id: str,
        project_id: str,
    ) -> dict[str, str | int] | None:
        if path.is_symlink():
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run record traverses a link or reparse point.")
        if path.suffix != ".json":
            return None
        if not path.is_file():
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run record is not a regular JSON file.")
        try:
            path.resolve(strict=True).relative_to(root.resolve(strict=True))
            value = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise RepositoryError("ERR_TENANT_ISOLATION", "Configured workspace path escapes its root.") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run record is unreadable.") from exc
        if not isinstance(value, dict):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run record is malformed.")
        record_tenant = value.get("tenant_id")
        record_project = value.get("project_id")
        if not isinstance(record_tenant, str) or not isinstance(record_project, str):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run identity is malformed.")
        if record_tenant != tenant_id or record_project != project_id:
            raise RepositoryError("ERR_TENANT_ISOLATION", "Canonical run identity is mismatched.")
        run_id, step_id, revision, status = value.get("run_id"), value.get("step_id"), value.get("revision"), value.get("status")
        if not isinstance(run_id, str) or run_id != path.stem:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run identity is malformed.")
        try:
            WorkspaceRegistry._validate_id(run_id, "run")
        except RepositoryError as exc:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run identity is malformed.") from exc
        if not isinstance(step_id, str) or step_id not in {*_INITIAL_ROUTE, "3b"}:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run step is invalid.")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run revision is invalid.")
        if not isinstance(status, str) or status not in _RUN_STATUSES:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Canonical run status is invalid.")
        return {"run_id": run_id, "step_id": step_id, "revision": revision, "status": status}

    def collection(self, tenant_id: str, project_id: str, name: str) -> list[dict[str, JsonValue]]:
        if name not in _COLLECTIONS:
            raise RepositoryError("ERROR_DOMAIN_CONTRACT_INVALID", "Requested projection collection is invalid.")
        value = self._optional(tenant_id, project_id, f"{name}.json", [])
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Projection collection is malformed.")
        return copy.deepcopy(value)

    def artifacts(self, tenant_id: str, project_id: str) -> list[dict[str, JsonValue]]:
        return self._artifact_projection(tenant_id, project_id, "artifacts")

    def quality_gate_runs(self, tenant_id: str, project_id: str) -> list[dict[str, JsonValue]]:
        return self._artifact_projection(tenant_id, project_id, "gates")

    def run_history(self, tenant_id: str, project_id: str, run_id: str) -> list[dict[str, JsonValue]]:
        return [item for item in self.collection(tenant_id, project_id, "llm-runs") if item.get("run_id") == run_id]

    def write_run(self, tenant_id: str, project_id: str, run: dict[str, JsonValue]) -> None:
        run_id = run.get("run_id")
        if not isinstance(run_id, str):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Derived run projection is malformed.")
        self._write(tenant_id, project_id, f"runs/{run_id}.json", run)

    def write_intake(self, tenant_id: str, project_id: str, intake: dict[str, JsonValue]) -> None:
        self._write(tenant_id, project_id, "intake.json", intake)

    def replace_project_v2_and_intake(
        self,
        tenant_id: str,
        project_id: str,
        *,
        expected_project_sha256: str,
        project_v2: dict[str, JsonValue],
        intake: dict[str, JsonValue],
        logical_session: dict[str, JsonValue],
        run_id: str,
        deployment_id: str,
        audit_record: dict[str, JsonValue],
    ) -> None:
        current_project = self.project_v2(tenant_id, project_id)
        current_intake = self.intake(tenant_id, project_id)
        current_logical_session = self.logical_session(tenant_id, project_id)
        current_run = self.run(tenant_id, project_id, run_id)
        if _canonical_sha256(current_project) != expected_project_sha256:
            raise RepositoryError("ERR_STALE_REVISION", "Project V2 changed after the location-binding preview.")
        tenant = project_v2.get("tenant")
        reviewed = intake.get("reviewed")
        if (
            project_v2.get("project_id") != project_id
            or not isinstance(tenant, dict)
            or tenant.get("tenant_id") != tenant_id
            or not isinstance(reviewed, dict)
            or reviewed.get("project_v2") != project_v2
            or logical_session.get("tenant_id") != tenant_id
            or logical_session.get("project_id") != project_id
        ):
            raise RepositoryError("ERROR_DOMAIN_CONTRACT_INVALID", "Project V2 upgrade identity or accepted intake binding is invalid.")
        upgraded_run = copy.deepcopy(current_run)
        upgraded_run["deployment_id"] = deployment_id
        upgrade_id = audit_record.get("upgrade_id")
        if not isinstance(upgrade_id, str):
            raise RepositoryError("ERROR_DOMAIN_CONTRACT_INVALID", "Project V2 upgrade audit identity is invalid.")
        audit_path = f"project-v2-upgrades/{upgrade_id}.json"
        existing_audit = self._optional(tenant_id, project_id, audit_path, None)
        if existing_audit is not None:
            if (
                existing_audit == audit_record
                and current_project == project_v2
                and current_intake == intake
                and current_logical_session == logical_session
                and current_run == upgraded_run
            ):
                return
            raise RepositoryError("ERR_IDEMPOTENCY_CONFLICT", "Project V2 upgrade identity conflicts with stored state.")
        history_path: str | None = None
        history_created = False
        if current_logical_session != logical_session:
            logical_session_id = current_logical_session.get("logical_session_id")
            session_revision = current_logical_session.get("session_revision")
            if not isinstance(logical_session_id, str) or not isinstance(session_revision, int):
                raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Logical project session identity is invalid.")
            history_path = f"logical-session-history/{logical_session_id}-r{session_revision}.json"
            existing_history = self._optional(tenant_id, project_id, history_path, None)
            if existing_history is not None and existing_history != current_logical_session:
                raise RepositoryError("ERR_IDEMPOTENCY_CONFLICT", "Logical project session history conflicts with stored state.")
            history_created = existing_history is None
        try:
            if history_path is not None and history_created:
                self._write(tenant_id, project_id, history_path, current_logical_session)
            self._write(tenant_id, project_id, "project-v2.json", project_v2)
            self._write(tenant_id, project_id, "intake.json", intake)
            self._write(tenant_id, project_id, "logical-session.json", logical_session)
            self._write(tenant_id, project_id, f"runs/{run_id}.json", upgraded_run)
            self._write(tenant_id, project_id, audit_path, audit_record)
        except Exception:
            self._write(tenant_id, project_id, "project-v2.json", current_project)
            self._write(tenant_id, project_id, "intake.json", current_intake)
            self._write(tenant_id, project_id, "logical-session.json", current_logical_session)
            self._write(tenant_id, project_id, f"runs/{run_id}.json", current_run)
            if self._optional(tenant_id, project_id, audit_path, None) is not None:
                self._remove(tenant_id, project_id, audit_path)
            if history_path is not None and history_created and self._optional(tenant_id, project_id, history_path, None) is not None:
                self._remove(tenant_id, project_id, history_path)
            raise

    def artifact_content_bytes(self, tenant_id: str, project_id: str, artifact_id: str) -> bytes:
        try:
            return self._path(tenant_id, project_id, f"artifact-content/{artifact_id}.md").read_bytes()
        except OSError as exc:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Artifact content is unavailable.") from exc

    def _artifact_projection(self, tenant_id: str, project_id: str, name: str) -> list[dict[str, JsonValue]]:
        value = self._optional(tenant_id, project_id, f"{name}.json", [])
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Artifact projection is malformed.")
        return copy.deepcopy(value)

    def write_release(self, tenant_id: str, project_id: str, release: dict[str, JsonValue]) -> None:
        release_id = release.get("release_id")
        if not isinstance(release_id, str):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Release projection is malformed.")
        self._write(tenant_id, project_id, f"releases/{release_id}.json", release)

    def releases(self, tenant_id: str, project_id: str) -> list[dict[str, JsonValue]]:
        root = self._path(tenant_id, project_id, "releases")
        return [] if not root.exists() else [self._required(tenant_id, project_id, f"releases/{path.name}") for path in sorted(root.glob("*.json"))]

    def released_predecessor(self, tenant_id: str, project_id: str, step_id: str) -> dict[str, JsonValue] | None:
        root = self._path(tenant_id, project_id, "releases")
        if not root.exists():
            return None
        matching = [item for item in (self._required(tenant_id, project_id, f"releases/{path.name}") for path in root.glob("*.json")) if item.get("step_id") == step_id and item.get("status") == "released"]
        if len(matching) > 1:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Multiple canonical predecessor releases are unavailable.")
        return matching[0] if matching else None


def _canonical_sha256(value: dict[str, JsonValue]) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
