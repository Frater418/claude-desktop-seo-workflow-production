from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker

from services.agent_gateway.evidence_store import AgentGatewayStore, AgentGatewayStoreError
from services.deterministic_output_fields import bind_deterministic_output_fields

from .step_agents import StepAgentContract


@dataclass(frozen=True, slots=True)
class StepAgentResultError(Exception):
    code: str
    path: str
    message: str
    remediation: str

    def __str__(self) -> str:
        return f"{self.code}:{self.path}: {self.message}"


@dataclass(frozen=True, slots=True)
class StepAgentOutput:
    contract_id: str
    content: Mapping[str, Any]
    content_bytes: bytes
    content_sha256: str
    logical_ref: str


@dataclass(frozen=True, slots=True)
class ObservedToolCall:
    call_id: str
    operation_id: str
    tool_name: str
    evidence_refs: tuple[Mapping[str, str], ...]


@dataclass(frozen=True, slots=True)
class ObservedDelegation:
    subagent_id: str
    purpose: str
    status: str


@dataclass(frozen=True, slots=True)
class StepAgentResult:
    envelope: Mapping[str, Any]
    outputs: tuple[StepAgentOutput, ...]
    tool_calls: tuple[ObservedToolCall, ...]
    delegations: tuple[ObservedDelegation, ...]
    evidence_refs: tuple[Mapping[str, str], ...]
    raw_sha256: str


def validate_step_agent_result(
    *,
    repository_root: Path,
    customer_root: Path,
    contract: StepAgentContract,
    request: Mapping[str, Any],
    package: Mapping[str, Any],
    raw_output: str,
    events: Sequence[Mapping[str, object]],
    event_stream_error: str | None,
    accepted_live_steering_refs: Sequence[str] = (),
) -> StepAgentResult:
    if event_stream_error is not None:
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_EVENT_EVIDENCE_UNAVAILABLE",
            "/events",
            f"Hermes event observation failed with {event_stream_error}.",
            "Restore the Runs event stream and start a fresh Step run. Do not persist an unobserved agent result.",
        )
    envelope = _parse_json_object(raw_output)
    envelope_schema = _load_json(repository_root / "standards" / "runtime" / "step-agent-output-envelope.schema.json")
    _assert_schema("ERROR_STEP_AGENT_OUTPUT_ENVELOPE_INVALID", envelope_schema, envelope, "/")
    _assert_identity(contract, request, package, envelope, accepted_live_steering_refs)
    tool_calls, delegations = _observe_events(contract, events)
    _raise_agent_failure(envelope)
    tool_calls = _verify_workspace_evidence(
        customer_root=customer_root,
        contract=contract,
        package=package,
        llm_run_request_id=str(request["llm_run_request_id"]),
        declared=envelope["evidence_refs"],
        tool_calls=tool_calls,
        delegations=delegations,
    )
    normalized_outputs = bind_deterministic_output_fields(contract.step_id, envelope["outputs"])
    outputs = _validate_outputs(repository_root, contract, request, normalized_outputs)
    raw_hash = hashlib.sha256(raw_output.encode("utf-8")).hexdigest()
    return StepAgentResult(
        envelope=envelope,
        outputs=outputs,
        tool_calls=tool_calls,
        delegations=delegations,
        evidence_refs=tuple(dict(reference) for reference in envelope["evidence_refs"]),
        raw_sha256=raw_hash,
    )


def _raise_agent_failure(envelope: Mapping[str, Any]) -> None:
    failure = envelope.get("failure")
    if failure is None:
        return
    raise StepAgentResultError(
        str(failure["code"]),
        "/failure",
        str(failure["message"]),
        str(failure["remediation"]),
    )


def _parse_json_object(raw_output: str) -> dict[str, Any]:
    text = raw_output.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_OUTPUT_ENVELOPE_INVALID",
            "/",
            "Step agent must return one strict JSON object without prose or code fences.",
            "Start a fresh run with the registered envelope instruction.",
        ) from exc
    if not isinstance(parsed, dict):
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_OUTPUT_ENVELOPE_INVALID",
            "/",
            "Step agent output root must be one JSON object.",
            "Return the registered envelope and no surrounding text.",
        )
    return parsed


def _assert_identity(
    contract: StepAgentContract,
    request: Mapping[str, Any],
    package: Mapping[str, Any],
    envelope: Mapping[str, Any],
    accepted_live_steering_refs: Sequence[str],
) -> None:
    expected = {
        "agent_contract_id": contract.entry["agent_contract_id"],
        "agent_contract_version": contract.entry["agent_contract_version"],
        "llm_run_request_id": request["llm_run_request_id"],
        "tenant_id": request["tenant_id"],
        "project_id": request["project_id"],
        "run_id": request["run_id"],
        "step_id": request["step_id"],
        "target_revision": request["target_revision"],
        "context_package_id": package["context_package_id"],
        "context_package_sha256": package["package_sha256"],
    }
    for field, value in expected.items():
        if envelope[field] != value:
            raise StepAgentResultError(
                "ERROR_STEP_AGENT_IDENTITY_MISMATCH",
                f"/{field}",
                "Step agent output identity differs from the immutable Heartweb request.",
                "Discard the candidate and start a fresh run from the canonical Context Package.",
            )
    revision_steering_refs = tuple(
        source["logical_ref"]
        for source in package["sources"]
        if source["source_kind"] == "operator_instruction"
    )
    if package["trigger"] == "revision" and len(revision_steering_refs) != 1:
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_STEERING_MISMATCH",
            "/operator_steering_refs",
            "Revision run lacks exactly one versioned Context Package steering instruction.",
            "Rebuild the revision Context Package and start a fresh Step run.",
        )
    expected_steering = (*revision_steering_refs, *accepted_live_steering_refs)
    observed_steering = tuple(envelope.get("operator_steering_refs", ()))
    if observed_steering != expected_steering:
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_STEERING_MISMATCH",
            "/operator_steering_refs",
            "Agent output does not bind every accepted versioned operator steering instruction in order.",
            "Discard the candidate if a steering instruction was omitted, invented or accepted too late.",
        )


def _observe_events(
    contract: StepAgentContract,
    events: Sequence[Mapping[str, object]],
) -> tuple[tuple[ObservedToolCall, ...], tuple[ObservedDelegation, ...]]:
    allowed_by_tool = {
        operation["tool_name"]: operation
        for operation in contract.allowed_operations
    }
    delegation_policy = contract.tool_policy["delegation_policy"]
    pending_tools: dict[str, int] = {}
    completed_calls: list[ObservedToolCall] = []
    call_counts: dict[str, int] = {}
    delegation_events: dict[str, ObservedDelegation] = {}
    for event_index, event in enumerate(events, start=1):
        event_kind = event.get("event")
        if event_kind in {"tool.started", "tool.completed"}:
            tool_name = event.get("tool")
            if not isinstance(tool_name, str) or not tool_name:
                raise _event_error("Malformed Hermes tool lifecycle event.")
            if tool_name == "delegate_task":
                if not delegation_policy["allowed"]:
                    raise StepAgentResultError(
                        "ERROR_STEP_AGENT_DELEGATION_NOT_ALLOWED",
                        "/events",
                        "Hermes invoked delegate_task while the Step policy disables delegation.",
                        "Discard the candidate and start a fresh run under the registered policy.",
                    )
                continue
            operation = allowed_by_tool.get(tool_name)
            if operation is None:
                raise StepAgentResultError(
                    "ERROR_STEP_AGENT_TOOL_NOT_ALLOWED",
                    "/events",
                    f"Hermes observed undeclared tool {tool_name}.",
                    "Discard the candidate and restrict the runtime to the registered Heartweb tools.",
                )
            if event_kind == "tool.started":
                pending_tools[tool_name] = pending_tools.get(tool_name, 0) + 1
                continue
            if not pending_tools.get(tool_name):
                raise _event_error(f"Hermes completed tool {tool_name} without a matching start event.")
            pending_tools[tool_name] -= 1
            if event.get("error") is True:
                raise StepAgentResultError(
                    "ERROR_STEP_AGENT_TOOL_FAILED",
                    "/events",
                    f"Heartweb tool {tool_name} failed.",
                    "Resolve the tool or provider error and start a controlled retry.",
                )
            call_counts[tool_name] = call_counts.get(tool_name, 0) + 1
            if call_counts[tool_name] > operation["max_calls"]:
                raise StepAgentResultError(
                    "ERROR_STEP_AGENT_TOOL_LIMIT_EXCEEDED",
                    "/events",
                    f"Tool {tool_name} exceeded its registered call limit.",
                    "Discard the run and review the Step Tool Policy before retrying.",
                )
            completed_calls.append(
                ObservedToolCall(
                    call_id=f"observed-call-{event_index}",
                    operation_id=operation["operation_id"],
                    tool_name=tool_name,
                    evidence_refs=(),
                )
            )
        elif event_kind in {"subagent.start", "subagent.complete"}:
            subagent_id = event.get("subagent_id")
            goal = event.get("goal", "")
            if not isinstance(subagent_id, str) or not subagent_id or not isinstance(goal, str):
                raise _event_error("Malformed Hermes subagent lifecycle event.")
            if not delegation_policy["allowed"]:
                raise StepAgentResultError(
                    "ERROR_STEP_AGENT_DELEGATION_NOT_ALLOWED",
                    "/events",
                    "Hermes delegated a child while the Step policy disables delegation.",
                    "Discard the candidate and start a fresh run under the registered policy.",
                )
            purpose = _delegation_purpose(goal)
            if purpose not in delegation_policy["allowed_purposes"]:
                raise StepAgentResultError(
                    "ERROR_STEP_AGENT_DELEGATION_NOT_ALLOWED",
                    "/events",
                    f"Subagent purpose {purpose or 'missing'} is not allowed for this Step.",
                    "Use a PURPOSE=<registered-purpose> prefix and keep the child within the Step policy.",
                )
            if event_kind == "subagent.start":
                if subagent_id in delegation_events:
                    raise _event_error(f"Hermes emitted duplicate start events for subagent {subagent_id}.")
                delegation_events[subagent_id] = ObservedDelegation(subagent_id, purpose, "running")
            else:
                previous = delegation_events.get(subagent_id)
                if previous is None:
                    raise _event_error(f"Hermes completed unknown subagent {subagent_id}.")
                status = event.get("status", "completed")
                if not isinstance(status, str):
                    raise _event_error("Malformed Hermes subagent completion status.")
                if status != "completed":
                    raise StepAgentResultError(
                        "ERROR_STEP_AGENT_DELEGATION_FAILED",
                        "/events",
                        f"Subagent {subagent_id} ended with status {status}.",
                        "Resolve the child failure and start a controlled Step retry.",
                    )
                delegation_events[subagent_id] = ObservedDelegation(subagent_id, purpose, status)
    still_running_tools = [name for name, count in pending_tools.items() if count]
    if still_running_tools:
        raise _event_error(f"Hermes lacks terminal events for tools: {', '.join(sorted(still_running_tools))}.")
    delegations = tuple(delegation_events.values())
    if len(delegations) > delegation_policy["max_workers"]:
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_DELEGATION_LIMIT_EXCEEDED",
            "/events",
            "Observed subagents exceed the registered worker limit.",
            "Discard the run and reduce delegation to the versioned policy limit.",
        )
    incomplete = [item.subagent_id for item in delegations if item.status != "completed"]
    if incomplete:
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_DELEGATION_INCOMPLETE",
            "/events",
            "One or more observed subagents lack a successful terminal event.",
            "Wait for terminal child evidence or stop and retry the Step.",
        )
    return tuple(completed_calls), delegations


def _verify_workspace_evidence(
    *,
    customer_root: Path,
    contract: StepAgentContract,
    package: Mapping[str, Any],
    llm_run_request_id: str,
    declared: Sequence[Mapping[str, str]],
    tool_calls: Sequence[ObservedToolCall],
    delegations: Sequence[ObservedDelegation],
) -> tuple[ObservedToolCall, ...]:
    store = AgentGatewayStore(customer_root)
    tenant_id = str(package["tenant_id"])
    project_id = str(package["project_id"])
    run_id = str(package["run_id"])
    try:
        evidence_records = store.list_evidence(tenant_id, project_id, run_id)
        interactions = store.list_interactions(tenant_id, project_id, run_id)
    except AgentGatewayStoreError as error:
        raise StepAgentResultError(
            error.code,
            "/evidence_refs",
            error.message,
            "Repair the immutable Heartweb Evidence or authorization record and start a fresh Step run.",
        ) from error
    evidence_records = tuple(
        record
        for record in evidence_records
        if isinstance(record.get("operation_binding"), dict)
        and record["operation_binding"].get("llm_run_request_id") == llm_run_request_id
    )
    interactions = tuple(
        record
        for record in interactions
        if isinstance(record.get("operation_binding"), dict)
        and record["operation_binding"].get("llm_run_request_id") == llm_run_request_id
    )
    allowed_by_operation = {
        operation["operation_id"]: operation
        for operation in contract.allowed_operations
    }
    for record in (*evidence_records, *interactions):
        operation_id = record["operation_id"]
        if operation_id not in allowed_by_operation:
            raise StepAgentResultError(
                "ERROR_STEP_AGENT_TOOL_NOT_ALLOWED",
                "/evidence_refs",
                f"Run storage contains undeclared operation {operation_id}.",
                "Discard the candidate. A parent or child used a Heartweb tool outside the Step policy.",
            )
    verified = tuple(
        {
            "evidence_id": record["evidence_id"],
            "operation_id": record["operation_id"],
            "logical_ref": record["logical_ref"],
            "content_sha256": record["content_sha256"],
        }
        for record in evidence_records
    )
    _assert_evidence_refs(declared, verified)
    completed_operations = {record["operation_id"] for record in evidence_records}
    missing = [operation_id for operation_id in contract.required_operation_ids if operation_id not in completed_operations]
    if missing:
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_REQUIRED_TOOL_MISSING",
            "/evidence_refs",
            f"Required gateway operations lack verified Evidence: {', '.join(missing)}.",
            "Run the registered operations with operator authorization before accepting outputs.",
        )
    approved_operations = {
        record["operation_id"]
        for record in interactions
        if record["status"] == "approved"
    }
    unresolved = [record["interaction_id"] for record in interactions if record["status"] == "awaiting_approval"]
    if unresolved:
        raise StepAgentResultError(
            "ERROR_TOOL_AUTHORIZATION_PENDING",
            "/evidence_refs",
            "The Step finished while one or more exact tool requests still await an operator decision.",
            "Approve or deny every pending tool request, then resume or retry the Step explicitly.",
        )
    missing_after_approval = sorted(approved_operations - completed_operations)
    if missing_after_approval:
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_TOOL_EVIDENCE_MISSING",
            "/evidence_refs",
            f"Approved external operations produced no verified Evidence: {', '.join(missing_after_approval)}.",
            "Resolve the provider or persistence failure and start a controlled retry.",
        )
    refs_by_operation: dict[str, tuple[Mapping[str, str], ...]] = {}
    for operation_id in allowed_by_operation:
        refs_by_operation[operation_id] = tuple(ref for ref in verified if ref["operation_id"] == operation_id)
    observed_operations = {call.operation_id for call in tool_calls}
    uncorroborated = [
        operation_id
        for operation_id in completed_operations
        if operation_id not in observed_operations and not delegations
    ]
    if uncorroborated:
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_EVENT_EVIDENCE_UNAVAILABLE",
            "/events",
            f"Evidence exists without a matching parent tool lifecycle: {', '.join(sorted(uncorroborated))}.",
            "Discard the run because delegation was disabled and Hermes did not observe the tool call.",
        )
    bound_calls = tuple(
        ObservedToolCall(
            call_id=call.call_id,
            operation_id=call.operation_id,
            tool_name=call.tool_name,
            evidence_refs=refs_by_operation[call.operation_id],
        )
        for call in tool_calls
    )
    for call in bound_calls:
        operation = allowed_by_operation[call.operation_id]
        if operation["evidence_required"] and not call.evidence_refs:
            raise StepAgentResultError(
                "ERROR_STEP_AGENT_TOOL_EVIDENCE_MISSING",
                "/events",
                f"Tool {call.tool_name} completed without verified workspace Evidence.",
                "Repair the Heartweb tool adapter and run the Step again.",
            )
    return bound_calls


def _validate_outputs(
    repository_root: Path,
    contract: StepAgentContract,
    request: Mapping[str, Any],
    outputs: Sequence[Mapping[str, Any]],
) -> tuple[StepAgentOutput, ...]:
    expected = tuple(contract.prompt_entry["output_contracts"])
    observed_ids = tuple(output["contract_id"] for output in outputs)
    expected_ids = tuple(binding["contract_id"] for binding in expected)
    if observed_ids != expected_ids:
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_OUTPUT_CONTRACT_MISMATCH",
            "/outputs",
            "Agent outputs must match the official Step contracts exactly once and in registry order.",
            "Return the complete registered output set. Do not partially replace a multi-output revision.",
        )
    validated: list[StepAgentOutput] = []
    for index, (binding, output) in enumerate(zip(expected, outputs, strict=True)):
        schema_path = (repository_root / binding["contract_path"]).resolve()
        _assert_repository_path(repository_root.resolve(), schema_path, f"/outputs/{index}")
        schema_bytes = schema_path.read_bytes()
        if hashlib.sha256(schema_bytes).hexdigest() != binding["contract_sha256"]:
            raise StepAgentResultError(
                "ERROR_STEP_AGENT_OUTPUT_CONTRACT_MISMATCH",
                f"/outputs/{index}",
                "Registered output contract bytes no longer match their hash.",
                "Restore or version the official output contract before production.",
            )
        schema = json.loads(schema_bytes.decode("utf-8"))
        _assert_schema("ERROR_STEP_AGENT_OUTPUT_CONTRACT_INVALID", schema, output["content"], f"/outputs/{index}/content")
        content_bytes = _canonical_json_bytes(output["content"])
        logical_ref = f"runtime:agent-output/{request['llm_run_request_id']}/{index + 1}"
        validated.append(
            StepAgentOutput(
                contract_id=output["contract_id"],
                content=output["content"],
                content_bytes=content_bytes,
                content_sha256=hashlib.sha256(content_bytes).hexdigest(),
                logical_ref=logical_ref,
            )
        )
    return tuple(validated)


def _assert_evidence_refs(
    declared: Sequence[Mapping[str, str]],
    observed: Sequence[Mapping[str, str]],
) -> None:
    key = lambda item: (item["evidence_id"], item["operation_id"], item["logical_ref"], item["content_sha256"])
    if tuple(sorted(map(key, declared))) != tuple(sorted(map(key, observed))):
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_EVIDENCE_MISMATCH",
            "/evidence_refs",
            "Agent Evidence references differ from the immutable run-scoped Heartweb Evidence records.",
            "Discard the candidate. Never accept invented, omitted or substituted Evidence references.",
        )


def _delegation_purpose(goal: str) -> str:
    first = goal.strip().splitlines()[0] if goal.strip() else ""
    prefix = "PURPOSE="
    if not first.startswith(prefix):
        return ""
    return first[len(prefix):].strip().split()[0]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_OUTPUT_CONTRACT_INVALID",
            str(path),
            f"Required JSON contract is unreadable: {type(exc).__name__}.",
            "Restore the exact registered contract before production.",
        ) from exc
    if not isinstance(value, dict):
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_OUTPUT_CONTRACT_INVALID",
            str(path),
            "JSON contract root must be an object.",
            "Restore the exact registered contract before production.",
        )
    return value


def _assert_schema(code: str, schema: Mapping[str, Any], document: Mapping[str, Any], path: str) -> None:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda item: (tuple(str(part) for part in item.absolute_path), item.message))
    if errors:
        first = errors[0]
        suffix = "/".join(str(part) for part in first.absolute_path)
        pointer = path.rstrip("/") + (f"/{suffix}" if suffix else "")
        raise StepAgentResultError(
            code,
            pointer or "/",
            first.message,
            "Correct the agent output and start a fresh versioned run.",
        )


def _assert_repository_path(root: Path, candidate: Path, path: str) -> None:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_OUTPUT_CONTRACT_INVALID",
            path,
            "Output contract path escapes the repository root.",
            "Repair the official Prompt Registry before production.",
        ) from exc
    if not candidate.is_file():
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_OUTPUT_CONTRACT_INVALID",
            path,
            "Registered output contract file is missing.",
            "Restore the exact registered contract before production.",
        )


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise StepAgentResultError(
            "ERROR_STEP_AGENT_OUTPUT_CONTRACT_INVALID",
            "/outputs",
            "Output contains a value that cannot be represented as canonical JSON.",
            "Return finite JSON values only.",
        ) from exc


def _event_error(message: str) -> StepAgentResultError:
    return StepAgentResultError(
        "ERROR_STEP_AGENT_EVENT_EVIDENCE_INVALID",
        "/events",
        message,
        "Discard the candidate and restore the exact Hermes Runs event contract.",
    )
