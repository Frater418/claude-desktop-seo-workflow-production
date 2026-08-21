from __future__ import annotations

import copy

from .models import JsonValue
from .repository import ProjectRepository, RepositoryError


def _append_once(records: list[dict[str, JsonValue]], record: dict[str, JsonValue], identity: str) -> list[dict[str, JsonValue]]:
    existing = next((item for item in records if item.get(identity) == record.get(identity)), None)
    if existing is None:
        return [*records, record]
    if existing != record:
        raise RepositoryError("ERR_IDEMPOTENCY_CONFLICT", "Transition projection identity conflicts with stored content.")
    return records


class TransitionRecovery:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def stage(
        self,
        tenant_id: str,
        project_id: str,
        command_id: str,
        event: dict[str, JsonValue],
        result: dict[str, JsonValue],
        approval: dict[str, JsonValue] | None,
    ) -> None:
        self._repository._write(
            tenant_id,
            project_id,
            self._path(command_id),
            {"command_id": command_id, "event": event, "result": result, "approval": approval},
        )

    def load(self, tenant_id: str, project_id: str, command_id: str) -> dict[str, JsonValue] | None:
        payload = self._repository._optional(tenant_id, project_id, self._path(command_id), None)
        if payload is None:
            return None
        if not isinstance(payload, dict) or payload.get("command_id") != command_id:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Transition recovery record is invalid.")
        if not isinstance(payload.get("event"), dict) or not isinstance(payload.get("result"), dict):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Transition recovery record is invalid.")
        return copy.deepcopy(payload)

    def finalize(self, tenant_id: str, project_id: str, command_id: str) -> dict[str, JsonValue]:
        payload = self.load(tenant_id, project_id, command_id)
        if payload is None:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Transition recovery record is unavailable.")
        result = payload["result"]
        if not isinstance(result, dict) or not isinstance(result.get("run"), dict):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Transition recovery result is invalid.")
        self._repository.write_run(tenant_id, project_id, result["run"])
        human_qgr = result.get("human_quality_gate_run")
        if human_qgr is not None:
            if not isinstance(human_qgr, dict):
                raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Transition human gate projection is invalid.")
            gates = self._repository.quality_gate_runs(tenant_id, project_id)
            self._repository._write(
                tenant_id,
                project_id,
                "gates.json",
                _append_once(gates, human_qgr, "quality_gate_run_id"),
            )
        approval = payload.get("approval")
        if approval is not None:
            if not isinstance(approval, dict):
                raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Transition approval projection is invalid.")
            approvals = self._repository.collection(tenant_id, project_id, "approvals")
            self._repository._write(
                tenant_id,
                project_id,
                "approvals.json",
                _append_once(approvals, approval, "approval_id"),
            )
        release = result.get("release_record")
        if release is not None:
            if not isinstance(release, dict):
                raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Transition release projection is invalid.")
            release_id = release.get("release_id")
            if not isinstance(release_id, str):
                raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Transition release identity is invalid.")
            try:
                existing = self._repository._required(tenant_id, project_id, f"releases/{release_id}.json")
            except RepositoryError as error:
                if error.code != "ERROR_DOMAIN_CONTRACT_FILE_MISSING":
                    raise
                self._repository.write_release(tenant_id, project_id, release)
            else:
                if existing != release:
                    raise RepositoryError("ERR_IDEMPOTENCY_CONFLICT", "Release identity conflicts with stored content.")
        self._repository._remove(tenant_id, project_id, self._path(command_id))
        return result

    def pending(self, tenant_id: str, project_id: str) -> bool:
        root = self._repository._path(tenant_id, project_id, "transition-recovery")
        return root.exists() and any(root.iterdir())

    @staticmethod
    def _path(command_id: str) -> str:
        return f"transition-recovery/{command_id}.json"
