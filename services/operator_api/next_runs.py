from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .models import JsonValue
from .recovery_inventory import RecoveryInventory, RecoveryReplayIdentity
from .repository import ProjectRepository, RepositoryError


class NextRunError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class NextRunService:
    repository: ProjectRepository
    graph: dict[str, JsonValue]
    recovery_inventory: RecoveryInventory

    @classmethod
    def from_root(cls, repository: ProjectRepository, root: Path, recovery_inventory: RecoveryInventory) -> NextRunService:
        payload = json.loads((root / "standards/workflow/workflow-graph.json").read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise NextRunError("ERROR_CONTEXT_SOURCE_INVALID", "Workflow graph must be an object.")
        return cls(repository, payload, recovery_inventory)

    def derive(self, tenant_id: str, project_id: str, completed_run_id: str) -> dict[str, JsonValue]:
        completed = self.repository.run(tenant_id, project_id, completed_run_id)
        if completed.get("status") != "completed":
            raise NextRunError("ERR_TRANSITION_NOT_ALLOWED", "Only a completed run can unlock its successor.")
        step_id = completed.get("step_id")
        if not isinstance(step_id, str):
            raise NextRunError("ERROR_CONTEXT_SOURCE_INVALID", "Completed run step identity is invalid.")
        next_step = self._next_step(step_id)
        release = self.repository.released_predecessor(tenant_id, project_id, step_id)
        if release is None or release.get("run_id") != completed_run_id:
            raise NextRunError("ERR_GATE_REQUIRED", "Completed run requires its canonical release before successor creation.")
        content = self.repository.released_artifact_bytes(tenant_id, project_id, release)
        artifact_hash = hashlib.sha256(content).hexdigest()
        if artifact_hash != release.get("artifact_sha256"):
            raise NextRunError("ERR_STALE_REVISION", "Released predecessor bytes do not match its canonical hash.")
        run_id = self._run_id(project_id, next_step, release)
        return {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_id": run_id,
            "step_id": next_step,
            "gate_id": f"GATE-{next_step.upper()}",
            "revision": 1,
            "input_hash": artifact_hash,
            "status": "pending",
            "attempt": 1,
            "gate_context": {"local_workflow": True},
        }

    def create(self, tenant_id: str, project_id: str, completed_run_id: str) -> dict[str, JsonValue]:
        run = self.derive(tenant_id, project_id, completed_run_id)
        identity = self._replay_identity(tenant_id, project_id, run)
        self.recovery_inventory.authorize(identity)
        if identity is not None:
            self._recover(tenant_id, project_id, run["run_id"])
        existing = self.repository._optional(tenant_id, project_id, f"runs/{run['run_id']}.json", None)
        if existing is not None:
            if existing == run:
                return existing
            raise NextRunError("ERR_IDEMPOTENCY_CONFLICT", "Canonical successor run identity conflicts with existing state.")
        steps = self.repository.collection(tenant_id, project_id, "steps")
        next_step = run["step_id"]
        updated = [dict(record, status="pending") if record.get("step_id") == next_step else record for record in steps]
        path = f"next-run-recovery/{run['run_id']}.json"
        self.repository._write(tenant_id, project_id, path, {"run": run, "steps": updated})
        try:
            self.repository.write_run(tenant_id, project_id, run)
            self.repository._write(tenant_id, project_id, "steps.json", updated)
        except RepositoryError as exc:
            raise NextRunError(exc.code, exc.message) from exc
        except OSError as exc:
            raise NextRunError("ERROR_CONTEXT_SOURCE_INVALID", "Successor run projections cannot be materialized.") from exc
        self.repository._remove(tenant_id, project_id, path)
        return run

    def _replay_identity(self, tenant_id: str, project_id: str, run: dict[str, JsonValue]) -> RecoveryReplayIdentity | None:
        path = f"next-run-recovery/{run['run_id']}.json"
        recovery = self.repository._optional(tenant_id, project_id, path, None)
        if recovery is None:
            return None
        steps = self.repository.collection(tenant_id, project_id, "steps")
        updated = [dict(record, status="pending") if record.get("step_id") == run["step_id"] else record for record in steps]
        if not isinstance(recovery, dict) or recovery.get("run") != run or recovery.get("steps") != updated:
            raise NextRunError("ERR_IDEMPOTENCY_CONFLICT", "Successor run recovery conflicts with canonical state.")
        return RecoveryReplayIdentity(tenant_id, project_id, "next-run-recovery", path)

    def _recover(self, tenant_id: str, project_id: str, run_id: str) -> None:
        path = f"next-run-recovery/{run_id}.json"
        recovery = self.repository._optional(tenant_id, project_id, path, None)
        if recovery is None:
            return
        if not isinstance(recovery, dict) or not isinstance(recovery.get("run"), dict) or not isinstance(recovery.get("steps"), list):
            raise NextRunError("ERROR_CONTEXT_SOURCE_INVALID", "Successor run recovery record is invalid.")
        self.repository.write_run(tenant_id, project_id, recovery["run"])
        self.repository._write(tenant_id, project_id, "steps.json", recovery["steps"])
        self.repository._remove(tenant_id, project_id, path)

    def _next_step(self, step_id: str) -> str:
        edges = self.graph.get("initial_edges")
        if not isinstance(edges, list):
            raise NextRunError("ERROR_CONTEXT_SOURCE_INVALID", "Initial workflow edges are unavailable.")
        targets = [edge.get("to_step_id") for edge in edges if isinstance(edge, dict) and edge.get("from_step_id") == step_id]
        if len(targets) != 1 or not isinstance(targets[0], str) or targets[0] == "3b":
            raise NextRunError("ERR_TRANSITION_NOT_ALLOWED", "Completed run has no legal initial-route successor.")
        return targets[0]

    @staticmethod
    def _run_id(project_id: str, step_id: str, release: dict[str, JsonValue]) -> str:
        material = f"{project_id}|{step_id}|{release['release_id']}".encode("utf-8")
        return f"run-next-{hashlib.sha256(material).hexdigest()[:16]}"
