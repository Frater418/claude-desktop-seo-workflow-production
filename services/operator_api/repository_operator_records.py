"""Operator-record projections and their recovery sidecars."""

from __future__ import annotations

import copy
import re
from typing import Final

from .models import JsonValue
from .repository_types import RepositoryError

_IDENTITIES: Final = {
    "operator-task": ("task_id", re.compile(r"^task-[a-z0-9][a-z0-9-]{7,63}$"), "run_id"),
    "blocker-record": ("blocker_id", re.compile(r"^blocker-[a-z0-9][a-z0-9-]{7,63}$"), "run_id"),
    "revision-request": ("revision_request_id", re.compile(r"^revision-[a-z0-9][a-z0-9-]{7,63}$"), "run_id"),
    "production-steering": ("steering_id", re.compile(r"^steering-[a-z0-9][a-z0-9-]{7,63}$"), "run_id"),
    "workflow-defect": ("defect_id", re.compile(r"^defect-[a-z0-9][a-z0-9-]{7,63}$"), "affected_run_id"),
    "escalation-record": ("escalation_id", re.compile(r"^escalation-[a-z0-9][a-z0-9-]{7,63}$"), "run_id"),
    "resolution-record": ("resolution_id", re.compile(r"^resolution-[a-z0-9][a-z0-9-]{7,63}$"), "run_id"),
}


class OperatorRecordPersistence:
    """Persist typed operator records and repair their event sidecars."""

    def write_operator_record(self, tenant_id: str, project_id: str, record_type: str, record: dict[str, JsonValue]) -> None:
        record_id = self.operator_record_id(record_type, record)
        relative = f"operator-records/{record_type}/{record_id}.json"
        existing = self._optional(tenant_id, project_id, relative, None)
        if existing is not None and existing != record:
            raise RepositoryError(
                "ERR_IDEMPOTENCY_CONFLICT",
                "Operator record identity conflicts with stored immutable content.",
            )
        if existing is None:
            self._write(tenant_id, project_id, relative, record)

    def operator_record(self, tenant_id: str, project_id: str, record_type: str, record_id: str) -> dict[str, JsonValue]:
        return self._required(tenant_id, project_id, f"operator-records/{record_type}/{record_id}.json")

    def optional_operator_record(self, tenant_id: str, project_id: str, record_type: str, record_id: str) -> dict[str, JsonValue] | None:
        value = self._optional(tenant_id, project_id, f"operator-records/{record_type}/{record_id}.json", None)
        if value is None:
            return None
        if not isinstance(value, dict) or self.operator_record_id(record_type, value) != record_id:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Stored operator record is invalid.")
        return value

    @staticmethod
    def operator_record_id(record_type: str, record: dict[str, JsonValue]) -> str:
        identity = _IDENTITIES.get(record_type)
        if identity is None:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator record type is invalid.")
        field, pattern, _ = identity
        identifier = record.get(field)
        if not isinstance(identifier, str) or pattern.fullmatch(identifier) is None:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator record identity is invalid.")
        return identifier

    @staticmethod
    def operator_record_run_field(record_type: str) -> str:
        identity = _IDENTITIES.get(record_type)
        if identity is None:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator record type is invalid.")
        return identity[2]

    def write_operator_recovery(self, tenant_id: str, project_id: str, record_type: str, command_id: str, record: dict[str, JsonValue]) -> str:
        record_id = self.operator_record_id(record_type, record)
        self._write(tenant_id, project_id, f"projection-recovery/{record_type}--{record_id}.json", {"record_type": record_type, "record_id": record_id, "command_id": command_id, "record": record})
        return record_id

    def operator_recovery(self, tenant_id: str, project_id: str, record_type: str, record_id: str) -> dict[str, JsonValue] | None:
        payload = self._optional(tenant_id, project_id, f"projection-recovery/{record_type}--{record_id}.json", None)
        if payload is None:
            return None
        if not isinstance(payload, dict) or payload.get("record_type") != record_type or payload.get("record_id") != record_id:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator recovery record is invalid.")
        record = payload.get("record")
        if not isinstance(payload.get("command_id"), str) or not isinstance(record, dict) or self.operator_record_id(record_type, record) != record_id:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator recovery record is invalid.")
        return copy.deepcopy(payload)

    def finalize_operator_recovery(self, tenant_id: str, project_id: str, record_type: str, record_id: str) -> None:
        recovery = self.operator_recovery(tenant_id, project_id, record_type, record_id)
        if recovery is None or not isinstance(recovery.get("record"), dict):
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator recovery record is unavailable.")
        self.write_operator_record(tenant_id, project_id, record_type, recovery["record"])
        self._remove(tenant_id, project_id, f"projection-recovery/{record_type}--{record_id}.json")

    def remove_operator_recovery(self, tenant_id: str, project_id: str, record_type: str, record_id: str) -> None:
        self._remove(tenant_id, project_id, f"projection-recovery/{record_type}--{record_id}.json")

    def has_operator_recoveries(self, tenant_id: str, project_id: str) -> bool:
        recovery_root = self._path(tenant_id, project_id, "projection-recovery")
        if not recovery_root.exists():
            return False
        try:
            return any(recovery_root.iterdir())
        except OSError as exc:
            raise RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Operator recovery records are unreadable.") from exc

    def has_any_operator_recoveries(self) -> bool:
        return any(self.has_operator_recoveries(item.tenant_id, item.project_id) for item in self._registry.registrations)
