from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .hermes_runs_client import HermesRunHandle
from .hermes_runtime_provider import HermesRuntimeDispatch, HermesStepExecution
from .models import JsonValue
from .repository import ProjectRepository, RepositoryError
from .runtime import PreparedAgentDispatch
from .step_agents import StepAgentContractError, StepAgentRegistry


class ProductionExecutionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class ProductionExecutionStore:
    _SCHEMA_VERSION = "1.0.0"
    _STATUSES = frozenset(
        {
            "prepared",
            "running",
            "interaction_required",
            "approval_required",
            "denied",
            "completed",
            "failed",
        }
    )
    _TRANSITIONS = {
        "prepared": frozenset({"prepared", "running", "failed"}),
        "running": frozenset(
            {"running", "interaction_required", "approval_required", "completed", "failed"}
        ),
        "interaction_required": frozenset(
            {"interaction_required", "running", "denied", "failed"}
        ),
        "approval_required": frozenset(
            {"approval_required", "running", "denied", "failed"}
        ),
        "denied": frozenset({"denied"}),
        "completed": frozenset({"completed"}),
        "failed": frozenset({"failed"}),
    }

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    @staticmethod
    def execution_id(
        tenant_id: str,
        project_id: str,
        run_id: str,
        idempotency_key: str,
    ) -> str:
        digest = hashlib.sha256(
            _canonical_bytes(
                {
                    "tenant_id": tenant_id,
                    "project_id": project_id,
                    "run_id": run_id,
                    "idempotency_key": idempotency_key,
                }
            )
        ).hexdigest()
        return f"production-execution-{digest[:32]}"

    def create(
        self,
        prepared: PreparedAgentDispatch,
        *,
        preview_hash: str,
        idempotency_key: str,
        created_at: str,
        technical_retry: Mapping[str, JsonValue] | None = None,
        steered_rerun: Mapping[str, JsonValue] | None = None,
    ) -> dict[str, JsonValue]:
        request = prepared.request
        execution_id = self.execution_id(
            request["tenant_id"],
            request["project_id"],
            request["run_id"],
            idempotency_key,
        )
        contract = prepared.dispatch.step_agent_contract
        if contract is None:
            raise ProductionExecutionError(
                "ERROR_STEP_AGENT_NOT_CONFIGURED",
                "A specialized Step-agent contract is required for production execution.",
            )
        dispatch = {
            "request": dict(request),
            "run": dict(prepared.run),
            "context_package": dict(prepared.context_package),
            "llm_request": dict(prepared.llm_request),
            "worker_profile": dict(prepared.dispatch.worker_profile),
            "official_prompt": prepared.dispatch.official_prompt,
            "official_prompt_sha256": hashlib.sha256(
                prepared.dispatch.official_prompt.encode("utf-8")
            ).hexdigest(),
            "registry": dict(prepared.dispatch.registry),
            "parent_revision": prepared.dispatch.parent_revision,
            "source_bytes_base64": {
                logical_ref: base64.b64encode(content).decode("ascii")
                for logical_ref, content in sorted(prepared.dispatch.source_bytes.items())
            },
            "agent_contract_binding": {
                "step_id": contract.step_id,
                "agent_contract_id": contract.entry["agent_contract_id"],
                "agent_contract_version": contract.entry["agent_contract_version"],
                "worker_profile_id": contract.worker_profile["worker_profile_id"],
                "worker_profile_version": contract.worker_profile["profile_version"],
                "worker_profile_sha256": contract.worker_profile["profile_sha256"],
                "tool_policy_id": contract.tool_policy["tool_policy_id"],
                "tool_policy_version": contract.tool_policy["policy_version"],
                "tool_policy_sha256": contract.tool_policy["policy_sha256"],
            },
        }
        if technical_retry is not None:
            required_retry = {
                "source_execution_id",
                "source_record_sha256",
                "reason",
            }
            if set(technical_retry) != required_retry or not all(
                isinstance(technical_retry[field], str) and technical_retry[field]
                for field in required_retry
            ):
                raise ProductionExecutionError(
                    "ERROR_TECHNICAL_RETRY_INVALID",
                    "Technical retry lineage is incomplete or invalid.",
                )
            dispatch["technical_retry"] = dict(technical_retry)
        if steered_rerun is not None:
            required_rerun = {
                "source_execution_id",
                "source_record_sha256",
                "revision_request_id",
                "steering_id",
                "source_artifact_sha256",
            }
            if set(steered_rerun) != required_rerun or not all(
                isinstance(steered_rerun[field], str) and steered_rerun[field]
                for field in required_rerun
            ):
                raise ProductionExecutionError(
                    "ERROR_STEERED_RERUN_INVALID",
                    "Steered rerun lineage is incomplete or invalid.",
                )
            dispatch["steered_rerun"] = dict(steered_rerun)
        immutable = {
            "execution_id": execution_id,
            "tenant_id": request["tenant_id"],
            "project_id": request["project_id"],
            "run_id": request["run_id"],
            "step_id": request["step_id"],
            "expected_revision": prepared.run["revision"],
            "preview_hash": preview_hash,
            "idempotency_key": idempotency_key,
            "dispatch": dispatch,
        }
        record: dict[str, JsonValue] = {
            "schema_version": self._SCHEMA_VERSION,
            **immutable,
            "immutable_sha256": hashlib.sha256(_canonical_bytes(immutable)).hexdigest(),
            "status": "prepared",
            "hermes": None,
            "interaction_ids": [],
            "completion": None,
            "error": None,
            "created_at": created_at,
            "updated_at": created_at,
        }
        record["record_sha256"] = _record_sha256(record)
        existing = self.optional(
            request["tenant_id"],
            request["project_id"],
            execution_id,
        )
        if existing is not None:
            if existing["immutable_sha256"] != record["immutable_sha256"]:
                raise ProductionExecutionError(
                    "ERR_IDEMPOTENCY_CONFLICT",
                    "The production execution identity conflicts with stored dispatch content.",
                )
            return existing
        self._write(record)
        return record

    def bind_handle(
        self,
        record: Mapping[str, JsonValue],
        handle: HermesRunHandle,
        *,
        updated_at: str,
    ) -> dict[str, JsonValue]:
        current = self.get(
            str(record["tenant_id"]),
            str(record["project_id"]),
            str(record["execution_id"]),
        )
        hermes = {"run_id": handle.run_id, "session_id": handle.session_id}
        if current["hermes"] is not None and current["hermes"] != hermes:
            raise ProductionExecutionError(
                "ERR_IDEMPOTENCY_CONFLICT",
                "The production execution is already bound to a different Hermes run.",
            )
        return self.update(
            current,
            status="running",
            updated_at=updated_at,
            hermes=hermes,
        )

    def update(
        self,
        record: Mapping[str, JsonValue],
        *,
        status: str,
        updated_at: str,
        hermes: Mapping[str, JsonValue] | None = None,
        interaction_ids: list[str] | None = None,
        completion: Mapping[str, JsonValue] | None = None,
        error: Mapping[str, JsonValue] | None = None,
    ) -> dict[str, JsonValue]:
        if status not in self._STATUSES:
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Production execution status is invalid.",
            )
        current = self.get(
            str(record["tenant_id"]),
            str(record["project_id"]),
            str(record["execution_id"]),
        )
        current_status = str(current["status"])
        if status not in self._TRANSITIONS[current_status]:
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Production execution status transition is invalid.",
            )
        updated = dict(current)
        updated["status"] = status
        updated["updated_at"] = updated_at
        if hermes is not None:
            if current["hermes"] is not None and current["hermes"] != dict(hermes):
                raise ProductionExecutionError(
                    "ERR_IDEMPOTENCY_CONFLICT",
                    "Production execution Hermes identity changed.",
                )
            updated["hermes"] = dict(hermes)
        if interaction_ids is not None:
            if len(interaction_ids) != len(set(interaction_ids)):
                raise ProductionExecutionError(
                    "ERROR_PRODUCTION_EXECUTION_INVALID",
                    "Production execution interaction identities must be unique.",
                )
            updated["interaction_ids"] = list(interaction_ids)
        if completion is not None:
            updated["completion"] = dict(completion)
        if error is not None:
            updated["error"] = dict(error)
        updated["record_sha256"] = _record_sha256(updated)
        self._validate(updated)
        self._write(updated)
        return updated

    def optional(
        self,
        tenant_id: str,
        project_id: str,
        execution_id: str,
    ) -> dict[str, JsonValue] | None:
        value = self._repository._optional(
            tenant_id,
            project_id,
            self._relative_path(execution_id),
            None,
        )
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Stored production execution is not a JSON object.",
            )
        self._validate(value)
        return value

    def get(
        self,
        tenant_id: str,
        project_id: str,
        execution_id: str,
    ) -> dict[str, JsonValue]:
        record = self.optional(tenant_id, project_id, execution_id)
        if record is None:
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_NOT_FOUND",
                "Production execution does not exist.",
            )
        return record

    def list_for_run(
        self,
        tenant_id: str,
        project_id: str,
        run_id: str,
    ) -> tuple[dict[str, JsonValue], ...]:
        root = self._repository._path(
            tenant_id,
            project_id,
            "production-executions/v1",
        )
        if not root.exists():
            return ()
        records: list[dict[str, JsonValue]] = []
        try:
            paths = tuple(sorted(root.glob("production-execution-*.json")))
        except OSError as error:
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Production execution inventory is unreadable.",
            ) from error
        for path in paths:
            if path.is_symlink() or not path.is_file():
                raise ProductionExecutionError(
                    "ERROR_PRODUCTION_EXECUTION_INVALID",
                    "Production execution inventory contains an unsafe path.",
                )
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise ProductionExecutionError(
                    "ERROR_PRODUCTION_EXECUTION_INVALID",
                    "Production execution inventory contains invalid JSON.",
                ) from error
            if not isinstance(value, dict):
                raise ProductionExecutionError(
                    "ERROR_PRODUCTION_EXECUTION_INVALID",
                    "Production execution inventory contains a non-object record.",
                )
            self._validate(value)
            if value["run_id"] == run_id:
                records.append(value)
        return tuple(records)

    def reconstruct(
        self,
        record: Mapping[str, JsonValue],
        *,
        repository_root: Path,
        step_agent_registry: StepAgentRegistry,
    ) -> tuple[PreparedAgentDispatch, HermesStepExecution | None]:
        self._validate(record)
        dispatch_value = record["dispatch"]
        if not isinstance(dispatch_value, dict):
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Production dispatch snapshot is missing.",
            )
        binding = dispatch_value["agent_contract_binding"]
        if not isinstance(binding, dict):
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Production agent contract binding is missing.",
            )
        try:
            contract = step_agent_registry.for_step(str(record["step_id"]))
        except StepAgentContractError as error:
            raise ProductionExecutionError(error.code, error.message) from error
        expected_binding = {
            "step_id": contract.step_id,
            "agent_contract_id": contract.entry["agent_contract_id"],
            "agent_contract_version": contract.entry["agent_contract_version"],
            "worker_profile_id": contract.worker_profile["worker_profile_id"],
            "worker_profile_version": contract.worker_profile["profile_version"],
            "worker_profile_sha256": contract.worker_profile["profile_sha256"],
            "tool_policy_id": contract.tool_policy["tool_policy_id"],
            "tool_policy_version": contract.tool_policy["policy_version"],
            "tool_policy_sha256": contract.tool_policy["policy_sha256"],
        }
        if binding != expected_binding:
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_CONTRACT_STALE",
                "Stored production execution no longer matches the versioned Step-agent contract.",
            )
        source_encoded = dispatch_value["source_bytes_base64"]
        if not isinstance(source_encoded, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in source_encoded.items()
        ):
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Stored production source bytes are invalid.",
            )
        try:
            source_bytes = {
                logical_ref: base64.b64decode(encoded, validate=True)
                for logical_ref, encoded in source_encoded.items()
            }
        except ValueError as error:
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Stored production source bytes cannot be decoded.",
            ) from error
        official_prompt = dispatch_value["official_prompt"]
        if (
            not isinstance(official_prompt, str)
            or hashlib.sha256(official_prompt.encode("utf-8")).hexdigest()
            != dispatch_value["official_prompt_sha256"]
        ):
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Stored official prompt bytes no longer match their hash.",
            )
        dispatch = HermesRuntimeDispatch(
            context_package=_object(dispatch_value["context_package"]),
            llm_request=_object(dispatch_value["llm_request"]),
            worker_profile=_object(dispatch_value["worker_profile"]),
            official_prompt=official_prompt,
            registry=_object(dispatch_value["registry"]),
            parent_revision=_integer(dispatch_value["parent_revision"]),
            source_bytes=source_bytes,
            repository_root=repository_root,
            step_agent_contract=contract,
        )
        prepared = PreparedAgentDispatch(
            request={key: str(value) for key, value in _object(dispatch_value["request"]).items()},
            run=_object(dispatch_value["run"]),
            context_package=_object(dispatch_value["context_package"]),
            llm_request=_object(dispatch_value["llm_request"]),
            dispatch=dispatch,
        )
        hermes_value = record["hermes"]
        if hermes_value is None:
            return prepared, None
        if not isinstance(hermes_value, dict):
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Stored Hermes run identity is invalid.",
            )
        handle = HermesRunHandle(
            run_id=_string(hermes_value.get("run_id")),
            session_id=_string(hermes_value.get("session_id")),
        )
        return prepared, HermesStepExecution(dispatch=dispatch, handle=handle)

    def _write(self, record: Mapping[str, JsonValue]) -> None:
        self._validate(record)
        try:
            self._repository._write(
                str(record["tenant_id"]),
                str(record["project_id"]),
                self._relative_path(str(record["execution_id"])),
                dict(record),
            )
        except RepositoryError as error:
            raise ProductionExecutionError(error.code, error.message) from error

    @classmethod
    def _relative_path(cls, execution_id: str) -> str:
        if not execution_id.startswith("production-execution-") or not execution_id[21:].isalnum():
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Production execution identity is invalid.",
            )
        return f"production-executions/v1/{execution_id}.json"

    @classmethod
    def _validate(cls, record: Mapping[str, Any]) -> None:
        required = {
            "schema_version",
            "execution_id",
            "tenant_id",
            "project_id",
            "run_id",
            "step_id",
            "expected_revision",
            "preview_hash",
            "idempotency_key",
            "dispatch",
            "immutable_sha256",
            "status",
            "hermes",
            "interaction_ids",
            "completion",
            "error",
            "created_at",
            "updated_at",
            "record_sha256",
        }
        if set(record) != required or record.get("schema_version") != cls._SCHEMA_VERSION:
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Production execution has an invalid closed record shape.",
            )
        strings = (
            "execution_id",
            "tenant_id",
            "project_id",
            "run_id",
            "step_id",
            "preview_hash",
            "idempotency_key",
            "immutable_sha256",
            "status",
            "created_at",
            "updated_at",
            "record_sha256",
        )
        if any(not isinstance(record.get(field), str) or not record[field] for field in strings):
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Production execution identity or state fields are missing.",
            )
        if record["status"] not in cls._STATUSES or not isinstance(record["expected_revision"], int):
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Production execution revision or status is invalid.",
            )
        if not isinstance(record["dispatch"], dict) or not isinstance(record["interaction_ids"], list):
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_INVALID",
                "Production execution dispatch or interaction inventory is invalid.",
            )
        immutable = {
            key: record[key]
            for key in (
                "execution_id",
                "tenant_id",
                "project_id",
                "run_id",
                "step_id",
                "expected_revision",
                "preview_hash",
                "idempotency_key",
                "dispatch",
            )
        }
        if hashlib.sha256(_canonical_bytes(immutable)).hexdigest() != record["immutable_sha256"]:
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_HASH_MISMATCH",
                "Production execution immutable dispatch hash does not match.",
            )
        if _record_sha256(record) != record["record_sha256"]:
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_HASH_MISMATCH",
                "Production execution record hash does not match.",
            )


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _record_sha256(record: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        _canonical_bytes({key: value for key, value in record.items() if key != "record_sha256"})
    ).hexdigest()


def _object(value: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ProductionExecutionError(
            "ERROR_PRODUCTION_EXECUTION_INVALID",
            "Production execution dispatch field is not an object.",
        )
    return dict(value)


def _integer(value: JsonValue) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProductionExecutionError(
            "ERROR_PRODUCTION_EXECUTION_INVALID",
            "Production execution integer field is invalid.",
        )
    return value


def _string(value: JsonValue | None) -> str:
    if not isinstance(value, str) or not value:
        raise ProductionExecutionError(
            "ERROR_PRODUCTION_EXECUTION_INVALID",
            "Production execution string field is invalid.",
        )
    return value
