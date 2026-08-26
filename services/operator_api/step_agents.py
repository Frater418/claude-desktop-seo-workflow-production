from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker


PRODUCTION_STEP_TYPES = ("0", "1", "1b", "1c", "2", "3", "4a", "4b")


@dataclass(frozen=True, slots=True)
class StepAgentContractError(Exception):
    code: str
    path: str
    message: str
    remediation: str

    def __str__(self) -> str:
        return f"{self.code}:{self.path}: {self.message}"


@dataclass(frozen=True, slots=True)
class StepAgentContract:
    step_id: str
    entry: Mapping[str, Any]
    worker_profile: Mapping[str, Any]
    tool_policy: Mapping[str, Any]
    prompt_entry: Mapping[str, Any]

    @property
    def required_operation_ids(self) -> tuple[str, ...]:
        return tuple(self.tool_policy["required_gateway_operations"])

    @property
    def allowed_operations(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(self.tool_policy["allowed_gateway_operations"])

    def production_preview(self) -> dict[str, Any]:
        operations = []
        for operation in self.allowed_operations:
            operations.append(
                {
                    "operation_id": operation["operation_id"],
                    "tool_name": operation["tool_name"],
                    "required": operation["operation_id"] in self.required_operation_ids,
                    "phase": operation["phase"],
                    "side_effect": operation["side_effect"],
                    "provider_id": operation.get("provider_id"),
                    "confirmation_scope": operation["confirmation_scope"],
                    "cost_mode": operation["cost_mode"],
                    "max_cost_usd": operation.get("max_cost_usd"),
                    "max_calls": operation["max_calls"],
                    "max_items": operation.get("max_items"),
                    "timeout_seconds": operation["timeout_seconds"],
                    "evidence_required": operation["evidence_required"],
                }
            )
        return {
            "step_id": self.step_id,
            "agent_contract_id": self.entry["agent_contract_id"],
            "agent_contract_version": self.entry["agent_contract_version"],
            "worker_profile_id": self.worker_profile["worker_profile_id"],
            "worker_profile_version": self.worker_profile["profile_version"],
            "worker_profile_sha256": self.worker_profile["profile_sha256"],
            "model_id": self.worker_profile["model_policy"]["default_model_id"],
            "inference_policy": self.worker_profile["inference_policy"],
            "prompt": {
                name: self.prompt_entry[name]
                for name in ("prompt_id", "prompt_version", "prompt_path", "prompt_sha256")
            },
            "output_contracts": self.prompt_entry["output_contracts"],
            "tool_policy_id": self.tool_policy["tool_policy_id"],
            "tool_policy_version": self.tool_policy["policy_version"],
            "tool_policy_sha256": self.tool_policy["policy_sha256"],
            "required_operation_ids": list(self.required_operation_ids),
            "operations": operations,
            "delegation_policy": self.tool_policy["delegation_policy"],
            "failure_mode": self.tool_policy["failure_mode"],
        }


class StepAgentRegistry:
    def __init__(self, contracts: Mapping[str, StepAgentContract], registry_sha256: str) -> None:
        self._contracts = dict(contracts)
        self.registry_sha256 = registry_sha256

    def for_step(self, step_id: str) -> StepAgentContract:
        contract = self._contracts.get(step_id)
        if contract is None:
            raise StepAgentContractError(
                "ERROR_STEP_AGENT_NOT_CONFIGURED",
                "/step_id",
                f"No active specialized agent contract exists for Step {step_id}.",
                "Add and validate an active Step agent contract before production.",
            )
        return contract

    @property
    def steps(self) -> tuple[str, ...]:
        return tuple(step for step in PRODUCTION_STEP_TYPES if step in self._contracts)


def load_step_agent_registry(
    repository_root: Path,
    prompt_registry: Mapping[str, Any],
    registry_path: Path | None = None,
) -> StepAgentRegistry:
    root = repository_root.resolve()
    selected_registry_path = registry_path or root / "standards" / "runtime" / "step-agent-registry.json"
    registry_schema = _load_json(root / "standards" / "runtime" / "step-agent-registry.schema.json")
    worker_schema = _load_json(root / "standards" / "runtime" / "worker-profile.schema.json")
    tool_schema = _load_json(root / "standards" / "runtime" / "agent-tool-policy.schema.json")
    registry = _load_json(selected_registry_path)

    _assert_schema("ERROR_STEP_AGENT_REGISTRY_INVALID", registry_schema, registry, selected_registry_path)
    _assert_record_hash(registry, "registry_sha256", selected_registry_path)

    entries = tuple(entry for entry in registry["entries"] if entry["active"] is True)
    steps = tuple(entry["step_id"] for entry in entries)
    if steps != PRODUCTION_STEP_TYPES or len(set(steps)) != len(steps):
        raise _error(
            "ERROR_STEP_AGENT_REGISTRY_INVALID",
            selected_registry_path,
            "Active entries must contain the eight initial Steps exactly once and in workflow order.",
            "Repair the Step agent registry without adding Step 3b to the initial sequence.",
        )

    prompt_entries = {
        entry["step_id"]: entry
        for entry in prompt_registry.get("entries", ())
        if entry.get("active") is True and entry.get("step_id") in PRODUCTION_STEP_TYPES
    }
    if tuple(prompt_entries) != PRODUCTION_STEP_TYPES:
        raise _error(
            "ERROR_STEP_AGENT_PROMPT_BINDING_INVALID",
            selected_registry_path,
            "The official prompt registry must expose one active prompt for every initial Step in workflow order.",
            "Repair the official prompt registry before loading Step agents.",
        )

    contracts: dict[str, StepAgentContract] = {}
    for index, entry in enumerate(entries):
        step_id = entry["step_id"]
        profile_path = _resolve_repository_path(root, entry["worker_profile_path"], f"/entries/{index}/worker_profile_path")
        policy_path = _resolve_repository_path(root, entry["tool_policy_path"], f"/entries/{index}/tool_policy_path")
        profile = _load_json(profile_path)
        policy = _load_json(policy_path)
        _assert_schema("ERROR_STEP_AGENT_WORKER_PROFILE_INVALID", worker_schema, profile, profile_path)
        _assert_schema("ERROR_STEP_AGENT_TOOL_POLICY_INVALID", tool_schema, policy, policy_path)
        _assert_record_hash(profile, "profile_sha256", profile_path)
        _assert_record_hash(policy, "policy_sha256", policy_path)
        _assert_entry_binding(entry, profile, policy, step_id, profile_path, policy_path)
        _assert_tool_policy_semantics(profile, policy, policy_path)
        contracts[step_id] = StepAgentContract(
            step_id=step_id,
            entry=entry,
            worker_profile=profile,
            tool_policy=policy,
            prompt_entry=prompt_entries[step_id],
        )
    return StepAgentRegistry(contracts, registry["registry_sha256"])


def _assert_entry_binding(
    entry: Mapping[str, Any],
    profile: Mapping[str, Any],
    policy: Mapping[str, Any],
    step_id: str,
    profile_path: Path,
    policy_path: Path,
) -> None:
    profile_binding = (
        entry["worker_profile_id"],
        entry["worker_profile_version"],
        entry["worker_profile_sha256"],
    )
    if profile_binding != (
        profile["worker_profile_id"],
        profile["profile_version"],
        profile["profile_sha256"],
    ) or profile["allowed_steps"] != [step_id] or profile["enabled"] is not True:
        raise _error(
            "ERROR_STEP_AGENT_WORKER_PROFILE_INVALID",
            profile_path,
            "Worker Profile identity, Step binding or enabled state differs from the Step agent registry.",
            "Create a new profile version and update the registry hashes atomically.",
        )
    policy_binding = (
        entry["tool_policy_id"],
        entry["tool_policy_version"],
        entry["tool_policy_sha256"],
    )
    if policy_binding != (
        policy["tool_policy_id"],
        policy["policy_version"],
        policy["policy_sha256"],
    ) or policy["step_id"] != step_id or policy["enabled"] is not True:
        raise _error(
            "ERROR_STEP_AGENT_TOOL_POLICY_INVALID",
            policy_path,
            "Tool Policy identity, Step binding or enabled state differs from the Step agent registry.",
            "Create a new policy version and update the registry hashes atomically.",
        )
    profile_policy = profile["tool_policy"]
    if (
        profile_policy["tool_policy_id"],
        profile_policy["policy_version"],
        profile_policy["policy_sha256"],
    ) != policy_binding:
        raise _error(
            "ERROR_STEP_AGENT_TOOL_POLICY_INVALID",
            profile_path,
            "Worker Profile does not bind the exact Step Tool Policy.",
            "Update the Worker Profile with the exact policy ID, version and hash.",
        )
    if profile["inference_policy"]["delegation_policy_ref"] != policy["delegation_policy"]["delegation_policy_id"]:
        raise _error(
            "ERROR_STEP_AGENT_DELEGATION_POLICY_INVALID",
            profile_path,
            "Worker Profile and Tool Policy bind different delegation policies.",
            "Bind one versioned delegation policy before production.",
        )


def _assert_tool_policy_semantics(
    profile: Mapping[str, Any],
    policy: Mapping[str, Any],
    policy_path: Path,
) -> None:
    operations = tuple(policy["allowed_gateway_operations"])
    operation_ids = tuple(operation["operation_id"] for operation in operations)
    tool_names = tuple(operation["tool_name"] for operation in operations)
    required = tuple(policy["required_gateway_operations"])
    if len(operation_ids) != len(set(operation_ids)) or len(tool_names) != len(set(tool_names)):
        raise _error(
            "ERROR_STEP_AGENT_TOOL_POLICY_INVALID",
            policy_path,
            "Allowed operation IDs and tool names must be unique within one Step.",
            "Remove duplicates and issue a new Tool Policy version.",
        )
    if any(operation_id not in operation_ids for operation_id in required):
        raise _error(
            "ERROR_STEP_AGENT_TOOL_POLICY_INVALID",
            policy_path,
            "Every required operation must also be present in allowed gateway operations.",
            "Add the operation contract or remove the invalid requirement.",
        )
    for operation in operations:
        if operation["side_effect"] != "read_only" and operation["confirmation_scope"] == "none":
            if operation["side_effect"] != "local_evidence_write" or operation["cost_mode"] != "none":
                raise _error(
                    "ERROR_STEP_AGENT_CONFIRMATION_POLICY_INVALID",
                    policy_path,
                    f"Operation {operation['operation_id']} has an external or costly effect without confirmation.",
                    "Require step_run or exact_request confirmation before enabling the operation.",
                )
        if operation["cost_mode"] in {"unknown_blocked", "provider_credits_unreported"} and operation["confirmation_scope"] != "exact_request":
            raise _error(
                "ERROR_STEP_AGENT_COST_POLICY_INVALID",
                policy_path,
                f"Operation {operation['operation_id']} has provider-managed cost without exact request confirmation.",
                "Bind exact parameters, provider identity, call limit and item limit before enabling the operation.",
            )
    generic = tuple(profile["tool_policy"]["allowed_operations"])
    if bool(operations) != ("request_gateway_operation" in generic):
        raise _error(
            "ERROR_STEP_AGENT_TOOL_POLICY_INVALID",
            policy_path,
            "Worker generic operation permission does not match concrete gateway operations.",
            "Align the Worker Profile and Tool Policy before production.",
        )
    delegation = policy["delegation_policy"]
    if delegation["allowed"] != ("delegate_bounded_review" in generic):
        raise _error(
            "ERROR_STEP_AGENT_DELEGATION_POLICY_INVALID",
            policy_path,
            "Worker delegation permission does not match the bounded delegation policy.",
            "Align the Worker Profile and delegation policy before production.",
        )
    if profile["inference_policy"]["max_tool_rounds"] < len(required):
        raise _error(
            "ERROR_STEP_AGENT_TOOL_POLICY_INVALID",
            policy_path,
            "Worker max tool rounds cannot cover all required gateway operations.",
            "Increase the versioned max_tool_rounds or reduce required operations.",
        )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _error(
            "ERROR_STEP_AGENT_CONTRACT_UNREADABLE",
            path,
            f"Contract could not be read as UTF-8 JSON: {type(exc).__name__}.",
            "Restore the versioned contract file before production.",
        ) from exc
    if not isinstance(document, dict):
        raise _error(
            "ERROR_STEP_AGENT_CONTRACT_UNREADABLE",
            path,
            "Contract root must be a JSON object.",
            "Replace the file with a closed object contract.",
        )
    return document


def _assert_schema(code: str, schema: Mapping[str, Any], document: Mapping[str, Any], path: Path) -> None:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda item: (tuple(str(part) for part in item.absolute_path), item.message))
    if errors:
        first = errors[0]
        pointer = "/" + "/".join(str(part) for part in first.absolute_path)
        raise StepAgentContractError(
            code,
            f"{path}{pointer}",
            first.message,
            "Correct the versioned contract and recompute its canonical hash.",
        )


def _assert_record_hash(document: Mapping[str, Any], hash_field: str, path: Path) -> None:
    expected = _canonical_sha256({key: value for key, value in document.items() if key != hash_field})
    if document.get(hash_field) != expected:
        raise _error(
            "ERROR_STEP_AGENT_HASH_MISMATCH",
            path,
            f"{hash_field} does not bind the canonical record bytes.",
            "Do not repair in place for accepted runs. Create a new version and recompute the hash.",
        )


def _canonical_sha256(document: Mapping[str, Any]) -> str:
    encoded = json.dumps(document, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _resolve_repository_path(root: Path, relative: str, pointer: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise StepAgentContractError(
            "ERROR_STEP_AGENT_PATH_INVALID",
            pointer,
            "Step agent contract path escapes the repository root.",
            "Use a repository-relative standards/runtime path.",
        ) from exc
    if not candidate.is_file():
        raise StepAgentContractError(
            "ERROR_STEP_AGENT_CONTRACT_UNREADABLE",
            pointer,
            f"Referenced contract file is missing: {relative}.",
            "Restore the exact registered file before production.",
        )
    return candidate


def _error(code: str, path: Path, message: str, remediation: str) -> StepAgentContractError:
    return StepAgentContractError(code, str(path), message, remediation)
