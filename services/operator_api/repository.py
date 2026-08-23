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
