"""Runtime projection persistence and recovery mechanics."""

from __future__ import annotations

from .models import JsonValue
from .repository_types import RepositoryError


def _append_once(items: list[dict[str, JsonValue]], record: dict[str, JsonValue], identity: str) -> list[dict[str, JsonValue]]:
    record_id = record.get(identity)
    existing = next((item for item in items if item.get(identity) == record_id), None)
    if existing is None:
        return [*items, record]
    if existing != record:
        raise RepositoryError("ERR_IDEMPOTENCY_CONFLICT", "Runtime projection identity conflicts with stored content.")
    return items


class RuntimeProjectionPersistence:
    """Runtime projection transaction and sidecar recovery behavior."""

    def persist_runtime(self, tenant_id: str, project_id: str, run: dict[str, JsonValue], package: dict[str, JsonValue], request: dict[str, JsonValue], result: dict[str, JsonValue]) -> None:
        if run.get("input_hash") != package.get("package_sha256"):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Run input hash must bind the context package.")
        recovery = {"run": run, "package": package, "request": request, "result": result, "before": {"context-packages": self.collection(tenant_id, project_id, "context-packages"), "llm-runs": self.collection(tenant_id, project_id, "llm-runs"), "run": self.run(tenant_id, project_id, run["run_id"])}}
        self._write(tenant_id, project_id, f"runtime-recovery/{run['run_id']}.json", recovery)
        try:
            self._materialize_runtime(tenant_id, project_id, recovery)
        except (OSError, RepositoryError) as exc:
            self._restore_runtime(tenant_id, project_id, recovery["before"])
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Runtime projections cannot be materialized.") from exc
        self._remove(tenant_id, project_id, f"runtime-recovery/{run['run_id']}.json")

    def recover_runtime_persistence(self, tenant_id: str, project_id: str, run_id: str) -> None:
        recovery = self._optional(tenant_id, project_id, f"runtime-recovery/{run_id}.json", None)
        if recovery is None:
            return
        if not isinstance(recovery, dict) or not all(isinstance(recovery.get(name), dict) for name in ("run", "package", "request", "result")):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Runtime recovery record is malformed.")
        self._materialize_runtime(tenant_id, project_id, recovery)
        self._remove(tenant_id, project_id, f"runtime-recovery/{run_id}.json")

    def _materialize_runtime(self, tenant_id: str, project_id: str, recovery: dict[str, JsonValue]) -> None:
        package, request, result, run = (recovery[name] for name in ("package", "request", "result", "run"))
        if not all(isinstance(value, dict) for value in (package, request, result, run)):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Runtime recovery record is malformed.")
        self._write(tenant_id, project_id, "context-packages.json", _append_once(self.collection(tenant_id, project_id, "context-packages"), package, "context_package_id"))
        self._write(tenant_id, project_id, "llm-runs.json", _append_once(_append_once(self.collection(tenant_id, project_id, "llm-runs"), request, "llm_run_request_id"), result, "llm_run_result_id"))
        self.write_run(tenant_id, project_id, run)

    def _restore_runtime(self, tenant_id: str, project_id: str, before: JsonValue) -> None:
        if not isinstance(before, dict) or not isinstance(before.get("context-packages"), list) or not isinstance(before.get("llm-runs"), list) or not isinstance(before.get("run"), dict):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Runtime recovery rollback is malformed.")
        self._write(tenant_id, project_id, "context-packages.json", before["context-packages"])
        self._write(tenant_id, project_id, "llm-runs.json", before["llm-runs"])
        self.write_run(tenant_id, project_id, before["run"])
