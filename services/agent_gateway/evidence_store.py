from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from services.operator_api.provisioning import ProvisionedWorkspaceResolver
from services.operator_api.repository import RepositoryError, WorkspaceRegistry


JsonObject = dict[str, Any]
_LLM_RUN_REQUEST_ID = re.compile(r"^llm-request-[a-z0-9][a-z0-9-]{7,63}$")


class AgentGatewayStoreError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class AgentGatewayStore:
    customer_root: Path

    @classmethod
    def from_environment(cls) -> "AgentGatewayStore":
        raw = os.environ.get("HEARTWEB_CUSTOMER_ROOT", "").strip()
        if not raw:
            raise AgentGatewayStoreError(
                "ERROR_AGENT_GATEWAY_CONFIG_MISSING",
                "HEARTWEB_CUSTOMER_ROOT is required for the isolated Heartweb agent gateway.",
            )
        root = Path(raw)
        if not root.is_absolute():
            raise AgentGatewayStoreError(
                "ERROR_AGENT_GATEWAY_CONFIG_INVALID",
                "HEARTWEB_CUSTOMER_ROOT must be absolute.",
            )
        return cls(root)

    def persist_evidence(
        self,
        *,
        tenant_id: str,
        project_id: str,
        run_id: str,
        operation_id: str,
        evidence_kind: str,
        operation_binding: Mapping[str, Any],
        request_payload: Mapping[str, Any],
        result_payload: Mapping[str, Any],
    ) -> JsonObject:
        workspace = self._workspace(tenant_id, project_id)
        _validate_run_id(run_id)
        binding = _validated_operation_binding(operation_binding, operation_id)
        binding_sha256 = hashlib.sha256(_canonical_bytes(binding)).hexdigest()
        request_bytes = _canonical_bytes(dict(request_payload))
        result_bytes = _canonical_bytes(dict(result_payload))
        content_sha256 = hashlib.sha256(result_bytes).hexdigest()
        seed = _canonical_bytes(
            {
                "tenant_id": tenant_id,
                "project_id": project_id,
                "run_id": run_id,
                "operation_id": operation_id,
                "operation_binding_sha256": binding_sha256,
                "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
                "content_sha256": content_sha256,
            }
        )
        evidence_id = f"evidence-{hashlib.sha256(seed).hexdigest()[:24]}"
        logical_ref = f"runtime:evidence/{evidence_id}"
        result_relative = Path("agent-evidence/v2") / run_id / f"{evidence_id}.result.json"
        result_path = self._operator_path(workspace, result_relative)
        existing_result = _read_json(result_path)
        if existing_result is not None and existing_result != dict(result_payload):
            raise AgentGatewayStoreError(
                "ERR_IDEMPOTENCY_CONFLICT",
                "Existing agent Evidence result bytes conflict with the deterministic Evidence identity.",
            )
        if existing_result is None:
            _atomic_write(result_path, dict(result_payload))
        record: JsonObject = {
            "schema_version": "2.1.0",
            "evidence_id": evidence_id,
            "logical_ref": logical_ref,
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_id": run_id,
            "operation_id": operation_id,
            "evidence_kind": evidence_kind,
            "operation_binding": binding,
            "operation_binding_sha256": binding_sha256,
            "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
            "content_sha256": content_sha256,
            "result_storage_key": result_relative.as_posix(),
            "request": dict(request_payload),
            "result": dict(result_payload),
            "created_at": _now(),
        }
        relative = Path("agent-evidence/v2") / run_id / f"{evidence_id}.json"
        path = self._operator_path(workspace, relative)
        existing = _read_json(path)
        if existing is not None:
            comparable = dict(existing)
            comparable.pop("created_at", None)
            proposed = dict(record)
            proposed.pop("created_at", None)
            if comparable != proposed:
                raise AgentGatewayStoreError(
                    "ERR_IDEMPOTENCY_CONFLICT",
                    "Existing agent Evidence conflicts with the deterministic Evidence identity.",
                )
            record = existing
        else:
            _atomic_write(path, record)
        evidence_bytes = _canonical_bytes(record)
        return {
            "status": "succeeded",
            "evidence_id": evidence_id,
            "operation_id": operation_id,
            "logical_ref": logical_ref,
            "content_sha256": content_sha256,
            "record_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            "evidence_kind": evidence_kind,
            "result_storage_key": result_relative.as_posix(),
            "result": dict(result_payload),
        }

    def list_evidence(self, tenant_id: str, project_id: str, run_id: str) -> tuple[JsonObject, ...]:
        workspace = self._workspace(tenant_id, project_id)
        _validate_run_id(run_id)
        root = self._operator_path(workspace, Path("agent-evidence/v2") / run_id)
        if not root.exists():
            return ()
        if root.is_symlink() or not root.is_dir():
            raise AgentGatewayStoreError(
                "ERROR_AGENT_EVIDENCE_STORAGE_INVALID",
                "The agent Evidence directory is unsafe.",
            )
        records = tuple(
            _read_json(path)
            for path in sorted(root.glob("evidence-*.json"))
            if not path.name.endswith(".result.json")
        )
        if any(record is None for record in records):
            raise AgentGatewayStoreError(
                "ERROR_AGENT_EVIDENCE_STORAGE_INVALID",
                "An agent Evidence record is unreadable.",
            )
        validated: list[JsonObject] = []
        for record in records:
            assert record is not None
            self._validate_evidence_record(record, tenant_id, project_id, run_id, workspace)
            validated.append(record)
        return tuple(validated)

    @staticmethod
    def _validate_evidence_record(
        record: Mapping[str, Any],
        tenant_id: str,
        project_id: str,
        run_id: str,
        workspace: Path,
    ) -> None:
        required_strings = (
            "schema_version",
            "evidence_id",
            "logical_ref",
            "tenant_id",
            "project_id",
            "run_id",
            "operation_id",
            "evidence_kind",
            "operation_binding_sha256",
            "request_sha256",
            "content_sha256",
        )
        if any(not isinstance(record.get(field), str) or not record[field] for field in required_strings):
            raise AgentGatewayStoreError(
                "ERROR_AGENT_EVIDENCE_STORAGE_INVALID",
                "An agent Evidence record lacks required identity or hash fields.",
            )
        if record["schema_version"] not in {"2.0.0", "2.1.0"}:
            raise AgentGatewayStoreError(
                "ERROR_AGENT_EVIDENCE_STORAGE_INVALID",
                "Agent Evidence record has an unsupported schema version.",
            )
        evidence_id = record["evidence_id"]
        if (
            record["tenant_id"] != tenant_id
            or record["project_id"] != project_id
            or record["run_id"] != run_id
            or record["logical_ref"] != f"runtime:evidence/{evidence_id}"
        ):
            raise AgentGatewayStoreError(
                "ERR_TENANT_ISOLATION",
                "Agent Evidence identity does not match its tenant, project or run scope.",
            )
        request = record.get("request")
        result = record.get("result")
        if not isinstance(request, dict) or not isinstance(result, dict):
            raise AgentGatewayStoreError(
                "ERROR_AGENT_EVIDENCE_STORAGE_INVALID",
                "Agent Evidence request and result must be objects.",
            )
        binding = _validated_operation_binding(record.get("operation_binding"), record["operation_id"])
        if hashlib.sha256(_canonical_bytes(binding)).hexdigest() != record["operation_binding_sha256"]:
            raise AgentGatewayStoreError(
                "ERROR_AGENT_EVIDENCE_HASH_MISMATCH",
                "Agent Evidence operation binding no longer matches its recorded hash.",
            )
        if hashlib.sha256(_canonical_bytes(request)).hexdigest() != record["request_sha256"]:
            raise AgentGatewayStoreError(
                "ERROR_AGENT_EVIDENCE_HASH_MISMATCH",
                "Agent Evidence request bytes no longer match their recorded hash.",
            )
        if hashlib.sha256(_canonical_bytes(result)).hexdigest() != record["content_sha256"]:
            raise AgentGatewayStoreError(
                "ERROR_AGENT_EVIDENCE_HASH_MISMATCH",
                "Agent Evidence result bytes no longer match their recorded hash.",
            )
        if record["schema_version"] == "2.1.0":
            storage_key = record.get("result_storage_key")
            if not isinstance(storage_key, str) or not storage_key:
                raise AgentGatewayStoreError(
                    "ERROR_AGENT_EVIDENCE_STORAGE_INVALID",
                    "Agent Evidence 2.1 lacks its immutable result storage key.",
                )
            stored = _read_json(AgentGatewayStore._operator_path(workspace, Path(storage_key)))
            if stored != result:
                raise AgentGatewayStoreError(
                    "ERROR_AGENT_EVIDENCE_HASH_MISMATCH",
                    "Stored Agent Evidence result bytes differ from the Evidence record.",
                )

    def request_authorization(
        self,
        *,
        tenant_id: str,
        project_id: str,
        run_id: str,
        operation_id: str,
        operation_binding: Mapping[str, Any],
        idempotency_key: str,
        confirmation_scope: str,
        cost_mode: str,
        maximum_cost_usd: float | None,
        request_payload: Mapping[str, Any],
    ) -> JsonObject:
        workspace = self._workspace(tenant_id, project_id)
        _validate_run_id(run_id)
        binding = _validated_operation_binding(operation_binding, operation_id)
        binding_sha256 = hashlib.sha256(_canonical_bytes(binding)).hexdigest()
        if not idempotency_key.startswith("tool-idem-"):
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_INVALID",
                "Tool authorization requires a server-derived idempotency key.",
            )
        if confirmation_scope != binding["confirmation_scope"] or cost_mode != binding["cost_mode"]:
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_INVALID",
                "Tool authorization confirmation and cost modes differ from the versioned operation binding.",
            )
        policy_cap = binding.get("max_cost_usd")
        if isinstance(policy_cap, int | float) and (
            not isinstance(maximum_cost_usd, int | float) or maximum_cost_usd > policy_cap
        ):
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_INVALID",
                "Tool authorization exceeds the versioned operation cost maximum.",
            )
        request_sha256 = hashlib.sha256(_canonical_bytes(dict(request_payload))).hexdigest()
        seed = _canonical_bytes(
            {
                "tenant_id": tenant_id,
                "project_id": project_id,
                "run_id": run_id,
                "operation_id": operation_id,
                "operation_binding_sha256": binding_sha256,
                "request_sha256": request_sha256,
                "idempotency_key": idempotency_key,
            }
        )
        interaction_id = f"interaction-{hashlib.sha256(seed).hexdigest()[:24]}"
        record: JsonObject = {
            "schema_version": "2.0.0",
            "interaction_id": interaction_id,
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_id": run_id,
            "operation_id": operation_id,
            "operation_binding": binding,
            "operation_binding_sha256": binding_sha256,
            "idempotency_key": idempotency_key,
            "confirmation_scope": confirmation_scope,
            "cost_mode": cost_mode,
            "maximum_cost_usd": maximum_cost_usd,
            "request_sha256": request_sha256,
            "request": dict(request_payload),
            "status": "awaiting_approval",
            "requested_at": _now(),
            "decision": None,
        }
        path = self._interaction_path(workspace, run_id, interaction_id)
        existing = _read_json(path)
        if existing is None:
            _atomic_write(path, record)
            return record
        stable_fields = (
            "interaction_id",
            "tenant_id",
            "project_id",
            "run_id",
            "operation_id",
            "operation_binding",
            "operation_binding_sha256",
            "idempotency_key",
            "confirmation_scope",
            "cost_mode",
            "maximum_cost_usd",
            "request_sha256",
            "request",
        )
        if any(existing.get(field) != record[field] for field in stable_fields):
            raise AgentGatewayStoreError(
                "ERR_IDEMPOTENCY_CONFLICT",
                "Existing tool authorization conflicts with the exact request.",
            )
        return existing

    def await_authorization(
        self,
        *,
        tenant_id: str,
        project_id: str,
        run_id: str,
        operation_id: str,
        operation_binding: Mapping[str, Any],
        idempotency_key: str,
        confirmation_scope: str,
        cost_mode: str,
        maximum_cost_usd: float | None,
        request_payload: Mapping[str, Any],
        timeout_seconds: int,
    ) -> JsonObject:
        record = self.request_authorization(
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            operation_id=operation_id,
            operation_binding=operation_binding,
            idempotency_key=idempotency_key,
            confirmation_scope=confirmation_scope,
            cost_mode=cost_mode,
            maximum_cost_usd=maximum_cost_usd,
            request_payload=request_payload,
        )
        workspace = self._workspace(tenant_id, project_id)
        path = self._interaction_path(workspace, run_id, record["interaction_id"])
        deadline = time.monotonic() + timeout_seconds
        while True:
            current = _read_json(path)
            if current is None:
                raise AgentGatewayStoreError(
                    "ERROR_TOOL_AUTHORIZATION_MISSING",
                    "The exact tool authorization record disappeared while the agent was waiting.",
                )
            status = current.get("status")
            if status == "approved":
                decision = current.get("decision")
                if (
                    not isinstance(decision, dict)
                    or decision.get("request_sha256") != record["request_sha256"]
                    or decision.get("operation_binding_sha256") != record["operation_binding_sha256"]
                    or decision.get("idempotency_key") != record["idempotency_key"]
                ):
                    raise AgentGatewayStoreError(
                        "ERROR_TOOL_AUTHORIZATION_INVALID",
                        "The operator decision is not bound to the exact tool request.",
                    )
                return current
            if status == "denied":
                raise AgentGatewayStoreError(
                    "ERROR_TOOL_AUTHORIZATION_DENIED",
                    "The operator denied the exact external tool request.",
                )
            if status != "awaiting_approval":
                raise AgentGatewayStoreError(
                    "ERROR_TOOL_AUTHORIZATION_INVALID",
                    "The tool authorization has an invalid state.",
                )
            if time.monotonic() >= deadline:
                raise AgentGatewayStoreError(
                    "ERROR_TOOL_AUTHORIZATION_TIMEOUT",
                    "The external tool request was not approved before its bounded timeout.",
                )
            time.sleep(0.5)

    def list_interactions(self, tenant_id: str, project_id: str, run_id: str) -> tuple[JsonObject, ...]:
        workspace = self._workspace(tenant_id, project_id)
        _validate_run_id(run_id)
        root = self._operator_path(workspace, Path("agent-interactions/v2") / run_id)
        if not root.exists():
            return ()
        if root.is_symlink() or not root.is_dir():
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_STORAGE_INVALID",
                "The interaction directory is unsafe.",
            )
        records = tuple(_read_json(path) for path in sorted(root.glob("interaction-*.json")))
        if any(record is None for record in records):
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_STORAGE_INVALID",
                "An interaction record is unreadable.",
            )
        validated: list[JsonObject] = []
        for record in records:
            assert record is not None
            self._validate_interaction_record(record, tenant_id, project_id, run_id)
            validated.append(record)
        return tuple(validated)

    def interaction(
        self,
        tenant_id: str,
        project_id: str,
        run_id: str,
        interaction_id: str,
    ) -> JsonObject:
        workspace = self._workspace(tenant_id, project_id)
        _validate_run_id(run_id)
        if not interaction_id.startswith("interaction-"):
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_MISSING",
                "The requested tool interaction identity is invalid.",
            )
        record = _read_json(self._interaction_path(workspace, run_id, interaction_id))
        if record is None:
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_MISSING",
                "The requested tool interaction does not exist.",
            )
        self._validate_interaction_record(record, tenant_id, project_id, run_id)
        return record

    @staticmethod
    def _validate_interaction_record(
        record: Mapping[str, Any],
        tenant_id: str,
        project_id: str,
        run_id: str,
    ) -> None:
        required_strings = (
            "schema_version",
            "interaction_id",
            "tenant_id",
            "project_id",
            "run_id",
            "operation_id",
            "operation_binding_sha256",
            "idempotency_key",
            "confirmation_scope",
            "cost_mode",
            "request_sha256",
            "status",
            "requested_at",
        )
        if any(not isinstance(record.get(field), str) or not record[field] for field in required_strings):
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_STORAGE_INVALID",
                "A tool authorization lacks required identity or state fields.",
            )
        if record["schema_version"] != "2.0.0":
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_STORAGE_INVALID",
                "Tool authorization has an unsupported schema version.",
            )
        if (
            record["tenant_id"] != tenant_id
            or record["project_id"] != project_id
            or record["run_id"] != run_id
        ):
            raise AgentGatewayStoreError(
                "ERR_TENANT_ISOLATION",
                "Tool authorization identity does not match its tenant, project or run scope.",
            )
        request = record.get("request")
        if not isinstance(request, dict) or hashlib.sha256(_canonical_bytes(request)).hexdigest() != record["request_sha256"]:
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_HASH_MISMATCH",
                "Tool authorization request bytes no longer match their recorded hash.",
            )
        binding = _validated_operation_binding(record.get("operation_binding"), record["operation_id"])
        if hashlib.sha256(_canonical_bytes(binding)).hexdigest() != record["operation_binding_sha256"]:
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_HASH_MISMATCH",
                "Tool authorization operation binding no longer matches its recorded hash.",
            )
        if (
            record["confirmation_scope"] != binding["confirmation_scope"]
            or record["cost_mode"] != binding["cost_mode"]
        ):
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_INVALID",
                "Stored tool authorization differs from its versioned operation policy.",
            )
        status = record["status"]
        decision = record.get("decision")
        if status == "awaiting_approval" and decision is not None:
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_INVALID",
                "A pending tool authorization cannot contain an operator decision.",
            )
        if status in {"approved", "denied"}:
            expected = status == "approved"
            if (
                not isinstance(decision, dict)
                or decision.get("approved") is not expected
                or decision.get("request_sha256") != record["request_sha256"]
                or decision.get("operation_binding_sha256") != record["operation_binding_sha256"]
                or decision.get("idempotency_key") != record["idempotency_key"]
                or not isinstance(decision.get("actor_id"), str)
                or not isinstance(decision.get("reason"), str)
            ):
                raise AgentGatewayStoreError(
                    "ERROR_TOOL_AUTHORIZATION_INVALID",
                    "A decided tool authorization is not bound to a complete operator decision.",
                )
        elif status != "awaiting_approval":
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_INVALID",
                "Tool authorization has an unknown state.",
            )

    def decide_interaction(
        self,
        *,
        tenant_id: str,
        project_id: str,
        run_id: str,
        interaction_id: str,
        approved: bool,
        actor_id: str,
        reason: str,
        expected_request_sha256: str,
    ) -> JsonObject:
        workspace = self._workspace(tenant_id, project_id)
        _validate_run_id(run_id)
        if not interaction_id.startswith("interaction-") or not actor_id or not reason.strip():
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_DECISION_INVALID",
                "A valid interaction, actor and decision reason are required.",
            )
        path = self._interaction_path(workspace, run_id, interaction_id)
        record = _read_json(path)
        if record is None:
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_MISSING",
                "The requested tool interaction does not exist.",
            )
        if record.get("request_sha256") != expected_request_sha256:
            raise AgentGatewayStoreError(
                "ERR_STALE_REVISION",
                "The tool request changed after the operator opened it.",
            )
        target_status = "approved" if approved else "denied"
        decision = {
            "approved": approved,
            "actor_id": actor_id,
            "reason": reason.strip(),
            "decided_at": _now(),
            "request_sha256": expected_request_sha256,
            "operation_binding_sha256": record["operation_binding_sha256"],
            "idempotency_key": record["idempotency_key"],
        }
        if record.get("status") in {"approved", "denied"}:
            if record.get("status") != target_status or record.get("decision", {}).get("request_sha256") != expected_request_sha256:
                raise AgentGatewayStoreError(
                    "ERR_IDEMPOTENCY_CONFLICT",
                    "The tool request already has a conflicting operator decision.",
                )
            return record
        if record.get("status") != "awaiting_approval":
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_INVALID",
                "Only a pending tool request can be decided.",
            )
        updated = {**record, "status": target_status, "decision": decision}
        _atomic_write(path, updated)
        return updated

    def _workspace(self, tenant_id: str, project_id: str) -> Path:
        try:
            resolver = ProvisionedWorkspaceResolver(WorkspaceRegistry(()), self.customer_root, True)
            return resolver.resolve(tenant_id, project_id)
        except RepositoryError as error:
            raise AgentGatewayStoreError(error.code, error.message) from error

    @staticmethod
    def _operator_path(workspace: Path, relative: Path) -> Path:
        root = (workspace / "v2/operator").resolve(strict=True)
        target = (root / relative).resolve(strict=False)
        try:
            target.relative_to(root)
        except ValueError as error:
            raise AgentGatewayStoreError(
                "ERR_TENANT_ISOLATION",
                "Agent gateway storage escaped the tenant workspace.",
            ) from error
        return target

    def _interaction_path(self, workspace: Path, run_id: str, interaction_id: str) -> Path:
        return self._operator_path(
            workspace,
            Path("agent-interactions/v2") / run_id / f"{interaction_id}.json",
        )


def _validated_operation_binding(value: object, operation_id: str) -> JsonObject:
    if not isinstance(value, Mapping):
        raise AgentGatewayStoreError(
            "ERROR_AGENT_OPERATION_BINDING_INVALID",
            "Agent operation binding must be a closed object.",
        )
    binding = dict(value)
    required_strings = {
        "schema_version",
        "registry_id",
        "registry_version",
        "registry_sha256",
        "step_id",
        "agent_contract_id",
        "agent_contract_version",
        "worker_profile_id",
        "worker_profile_version",
        "worker_profile_sha256",
        "tool_policy_id",
        "tool_policy_version",
        "tool_policy_sha256",
        "operation_id",
        "tool_name",
        "phase",
        "side_effect",
        "confirmation_scope",
        "cost_mode",
    }
    schema_version = binding.get("schema_version")
    execution_strings = {"llm_run_request_id"} if schema_version == "1.2.0" else set()
    optional = {"provider_id", "max_cost_usd", "input_contract_id", "output_contract_id"}
    if set(binding) - required_strings - execution_strings - optional - {"max_calls", "max_items", "target_revision", "timeout_seconds", "evidence_required"}:
        raise AgentGatewayStoreError(
            "ERROR_AGENT_OPERATION_BINDING_INVALID",
            "Agent operation binding contains fields outside the closed contract.",
        )
    if any(not isinstance(binding.get(field), str) or not binding[field] for field in required_strings | execution_strings):
        raise AgentGatewayStoreError(
            "ERROR_AGENT_OPERATION_BINDING_INVALID",
            "Agent operation binding lacks required identity fields.",
        )
    if schema_version not in {"1.0.0", "1.1.0", "1.2.0"} or binding["operation_id"] != operation_id:
        raise AgentGatewayStoreError(
            "ERROR_AGENT_OPERATION_BINDING_INVALID",
            "Agent operation binding does not match the requested operation.",
        )
    for field in ("registry_sha256", "worker_profile_sha256", "tool_policy_sha256"):
        value = binding[field]
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise AgentGatewayStoreError(
                "ERROR_AGENT_OPERATION_BINDING_INVALID",
                "Agent operation binding contains an invalid canonical hash.",
            )
    if (
        not binding["tool_name"].startswith("mcp__heartweb__")
        or not isinstance(binding.get("max_calls"), int)
        or binding["max_calls"] < 1
        or not isinstance(binding.get("timeout_seconds"), int)
        or binding["timeout_seconds"] < 1
        or not isinstance(binding.get("evidence_required"), bool)
        or (
            schema_version in {"1.1.0", "1.2.0"}
            and (
                not isinstance(binding.get("target_revision"), int)
                or isinstance(binding.get("target_revision"), bool)
                or binding["target_revision"] < 1
            )
        )
        or (
            binding.get("max_items") is not None
            and (
                not isinstance(binding.get("max_items"), int)
                or isinstance(binding.get("max_items"), bool)
                or binding["max_items"] < 1
            )
        )
    ):
        raise AgentGatewayStoreError(
            "ERROR_AGENT_OPERATION_BINDING_INVALID",
            "Agent operation binding contains invalid tool limits or evidence policy.",
        )
    provider_id = binding.get("provider_id")
    if provider_id is not None and (not isinstance(provider_id, str) or not provider_id.startswith("provider-")):
        raise AgentGatewayStoreError(
            "ERROR_AGENT_OPERATION_BINDING_INVALID",
            "Agent operation binding contains an invalid provider identity.",
        )
    if schema_version == "1.2.0" and _LLM_RUN_REQUEST_ID.fullmatch(binding["llm_run_request_id"]) is None:
        raise AgentGatewayStoreError(
            "ERROR_LLM_REQUEST_ID_INVALID",
            "Agent operation binding requires the exact valid LLM run request identity.",
        )
    return binding


def scope_operation_binding(
    operation_binding: Mapping[str, Any],
    *,
    llm_run_request_id: str,
    evidence_records: tuple[Mapping[str, Any], ...],
) -> JsonObject:
    """Bind one policy operation and its call budget to one LLM Step execution."""
    binding = {
        **dict(operation_binding),
        "schema_version": "1.2.0",
        "llm_run_request_id": llm_run_request_id,
    }
    operation_id = binding.get("operation_id")
    if not isinstance(operation_id, str):
        raise AgentGatewayStoreError(
            "ERROR_AGENT_OPERATION_BINDING_INVALID",
            "Agent operation binding lacks its operation identity.",
        )
    binding = _validated_operation_binding(binding, operation_id)
    completed_calls = sum(
        1
        for record in evidence_records
        if record.get("operation_id") == operation_id
        and isinstance(record.get("operation_binding"), Mapping)
        and record["operation_binding"].get("target_revision") == binding["target_revision"]
        and record["operation_binding"].get("llm_run_request_id") == llm_run_request_id
    )
    if completed_calls >= binding["max_calls"]:
        raise AgentGatewayStoreError(
            "ERROR_AGENT_TOOL_CALL_LIMIT",
            "The versioned Step Tool Policy call limit has already been reached for this LLM run request.",
        )
    return binding


def _validate_run_id(run_id: str) -> None:
    try:
        WorkspaceRegistry._validate_id(run_id, "run")
    except RepositoryError as error:
        raise AgentGatewayStoreError(error.code, error.message) from error


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _read_json(path: Path) -> JsonObject | None:
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise AgentGatewayStoreError(
            "ERROR_AGENT_GATEWAY_STORAGE_INVALID",
            "Agent gateway record is not a safe regular file.",
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AgentGatewayStoreError(
            "ERROR_AGENT_GATEWAY_STORAGE_INVALID",
            "Agent gateway record is unreadable.",
        ) from error
    if not isinstance(value, dict):
        raise AgentGatewayStoreError(
            "ERROR_AGENT_GATEWAY_STORAGE_INVALID",
            "Agent gateway record is not an object.",
        )
    return value


def _atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise AgentGatewayStoreError(
            "ERROR_AGENT_GATEWAY_STORAGE_INVALID",
            "Agent gateway output directory is unsafe.",
        )
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(_canonical_bytes(value))
        os.replace(temporary, path)
    except OSError as error:
        raise AgentGatewayStoreError(
            "ERROR_AGENT_GATEWAY_STORAGE_FAILED",
            "Agent gateway record could not be persisted atomically.",
        ) from error
    finally:
        temporary.unlink(missing_ok=True)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
