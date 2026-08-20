from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from services.context_builder import decide_technical_session, validate_context_package, validate_llm_request
from services.context_builder.builder import JsonValue
from services.runtime_contracts.llm_records import RuntimeContractValidator


INITIAL_PATH = ("0", "1", "1b", "1c", "2", "3", "4a", "4b")


@dataclass(frozen=True, slots=True)
class N8nSimulationError(ValueError):
    code: str
    path: str
    message: str
    remediation: str

    def __str__(self) -> str:
        return f"{self.code}:{self.path}: {self.message} Remediation: {self.remediation}"


@dataclass(frozen=True, slots=True)
class N8nContracts:
    command_schema: Mapping[str, Any]
    state_schema: Mapping[str, Any]
    wait_schema: Mapping[str, Any]
    retry_schema: Mapping[str, Any]
    dlq_schema: Mapping[str, Any]
    workflow_graph: Mapping[str, Any]
    runtime_validator: RuntimeContractValidator
    worker_profile: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class N8nSimulationRequest:
    command: Mapping[str, Any]
    state: Mapping[str, Any]
    context_package: Mapping[str, Any] | None
    llm_request: Mapping[str, Any] | None
    releases: Sequence[Mapping[str, Any]]
    revision_inputs: Sequence[Mapping[str, JsonValue]]
    cache_record: Mapping[str, Any] | None
    package_is_current: bool
    stored_commands: Sequence[Mapping[str, Any]]
    checkpoint_day: int | None
    context_source_bytes: Mapping[str, bytes]
    current_records: Mapping[str, Mapping[str, JsonValue]]
    prompt_registry: Mapping[str, JsonValue]
    wait_event_type: str = "gate.approved"


@dataclass(frozen=True, slots=True)
class N8nSimulationResult:
    state: dict[str, Any]
    replay: bool
    dispatch_intents: tuple[dict[str, Any], ...]
    wait_subscriptions: tuple[dict[str, Any], ...]
    retry_entries: tuple[dict[str, Any], ...]
    dlq_entries: tuple[dict[str, Any], ...]
    resume_commands: tuple[dict[str, Any], ...]
    technical_session_decision: str | None


def simulate_n8n(request: N8nSimulationRequest, contracts: N8nContracts) -> N8nSimulationResult:
    command = _validated(request.command, contracts.command_schema, "N8N_SIMULATION_COMMAND_INVALID", "/command")
    state = _validated(request.state, contracts.state_schema, "N8N_SIMULATION_STATE_INVALID", "/state")
    if command["integration_mode"] != "simulated" or "live_connection_id" in command or command["simulation_id"] != state["simulation_id"]:
        raise _error("N8N_SIMULATION_COMMAND_INVALID", "/command/integration_mode", "command and state must be one simulated identity", "Use the matching simulated command and state.")
    if any(command[field] != state[field] for field in ("tenant_id", "project_id")):
        raise _error("N8N_SIMULATION_SCOPE_INVALID", "/command", "command tenant and project must match the simulation state", "Use one tenant and project for each simulation state.")
    _target_matches(command)
    prior = next((item for item in request.stored_commands if item.get("idempotency_key") == command["idempotency_key"]), None)
    if prior is not None:
        if _canonical(prior) != _canonical(command):
            raise _error("N8N_SIMULATION_IDEMPOTENCY_CONFLICT", "/command/idempotency_key", "same idempotency key has changed command content", "Use a new key for a changed command.")
        return N8nSimulationResult(copy.deepcopy(state), True, (), (), (), (), (), None)
    match command["command_type"]:
        case "dispatch_tool_run":
            package, run_request, decision = _dispatch_inputs(request, contracts, command)
            _predecessor(command, package, request.releases, request.current_records, contracts.workflow_graph, request.checkpoint_day)
            intent = {
                "intent_type": "dispatch_llm_run", "tenant_id": command["tenant_id"], "project_id": command["project_id"], "run_id": command["run_id"],
                "step_id": command["step_id"], "expected_revision": command["expected_revision"], "correlation_id": command["correlation_id"],
                "idempotency_key": command["idempotency_key"], "context_package_id": package["context_package_id"], "context_package_sha256": package["package_sha256"],
                "llm_run_request_id": run_request["llm_run_request_id"], "llm_run_request_sha256": hashlib.sha256(_canonical(run_request)).hexdigest(),
                "technical_session_decision": decision,
            }
            return N8nSimulationResult(_queued(state, command), False, (intent,), (), (), (), (), decision)
        case "wait_for_gate":
            subscription = _wait(command, request.wait_event_type)
            _validated(subscription, contracts.wait_schema, "N8N_SIMULATION_WAIT_INVALID", "/wait")
            return N8nSimulationResult(_queued(state, command), False, (), (subscription,), (), (), (), None)
        case "retry_delivery":
            package, run_request, decision = _dispatch_inputs(request, contracts, command)
            del package, run_request
            attempt = 1 + sum(item["command_type"] == "retry_delivery" and item["idempotency_key"] == command["idempotency_key"] for item in state["command_queue"])
            if attempt == 3:
                first_failed_at = _first_failed_at(state, command)
                entry = _dlq(command, first_failed_at, state["clock"]["current_time"])
                _validated(entry, contracts.dlq_schema, "N8N_SIMULATION_DLQ_INVALID", "/dlq")
                return N8nSimulationResult(_queued(state, command, first_failed_at), False, (), (), (), (entry,), (), decision)
            first_failed_at = _first_failed_at(state, command)
            entry = _retry(command, attempt, first_failed_at, state["clock"]["current_time"])
            _validated(entry, contracts.retry_schema, "N8N_SIMULATION_RETRY_INVALID", "/retry")
            return N8nSimulationResult(_queued(state, command, first_failed_at), False, (), (), (entry,), (), (), decision)
        case "resume_run":
            core_request = {"request_kind": "core_command_request", "operation": "resume"}
            core_request.update({key: command[key] for key in ("command_id", "tenant_id", "project_id", "run_id", "step_id", "expected_revision", "correlation_id", "idempotency_key")})
            return N8nSimulationResult(copy.deepcopy(state), False, (), (), (), (), (core_request,), None)
        case "dead_letter":
            entry = _dlq(command, state["clock"]["current_time"], state["clock"]["current_time"])
            _validated(entry, contracts.dlq_schema, "N8N_SIMULATION_DLQ_INVALID", "/dlq")
            return N8nSimulationResult(_queued(state, command), False, (), (), (), (entry,), (), None)
        case _:
            raise _error("N8N_SIMULATION_COMMAND_INVALID", "/command/command_type", "unsupported command type", "Use the approved n8n command contract.")


def _dispatch_inputs(request: N8nSimulationRequest, contracts: N8nContracts, command: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any], str]:
    package = request.context_package
    run_request = request.llm_request
    if package is None or run_request is None:
        raise _error("N8N_SIMULATION_CONTEXT_INVALID", "/context_package", "dispatch requires a validated stored Context Package", "Validate and store the package before dispatch.")
    context_validation = validate_context_package(package, request.context_source_bytes, request.current_records, _context_graph(contracts.workflow_graph, command["step_id"]), request.releases, request.revision_inputs, contracts.runtime_validator, request.prompt_registry, request.state["clock"]["current_time"])
    if not context_validation.valid:
        error = context_validation.errors[0]
        raise _error("N8N_SIMULATION_CONTEXT_INVALID", error.path, error.message, "Use the exact stored Context Package and current records.")
    validation = validate_llm_request(run_request, package, contracts.worker_profile, contracts.runtime_validator)
    if not validation.valid:
        raise _error("N8N_SIMULATION_LLM_REQUEST_INVALID", validation.errors[0].path, validation.errors[0].message, "Use the exact validated LLM Run Request for the package.")
    if any(command[key] != package[key] for key in ("tenant_id", "project_id", "run_id", "step_id")) or command["expected_revision"] != package["target_revision"]:
        raise _error("N8N_SIMULATION_CONTEXT_INVALID", "/command", "command identity does not match the stored package", "Dispatch the package only for its bound run and revision.")
    decision = decide_technical_session(package, contracts.worker_profile, request.cache_record, request.state["clock"]["current_time"], request.package_is_current).decision.value
    return package, run_request, decision


def _predecessor(command: Mapping[str, Any], package: Mapping[str, Any], releases: Sequence[Mapping[str, Any]], current_records: Mapping[str, Mapping[str, JsonValue]], graph: Mapping[str, Any], checkpoint_day: int | None) -> None:
    step_id = command["step_id"]
    if step_id == "0":
        return None
    if step_id == "3b":
        if checkpoint_day not in {30, 60, 90}:
            raise _error("N8N_SIMULATION_CHECKPOINT_INVALID", "/checkpoint_day", "Step 3b is due only at day 30, 60 or 90", "Use a confirmed post-publication checkpoint.")
        predecessor, gate_id = "4b", "GATE-4B"
    else:
        predecessor = next((edge["from_step_id"] for edge in graph["initial_edges"] if edge["to_step_id"] == step_id), None)
        gate_id = next((step["gate_id"] for step in graph["steps"] if step["step_id"] == predecessor), None)
    if predecessor is None or gate_id is None or not _has_exact_release(package, command, predecessor, gate_id, releases, current_records):
        raise _error("N8N_SIMULATION_PREDECESSOR_REQUIRED", "/releases", "dispatch requires the released workflow predecessor", "Wait for the Core release event before dispatching the next step.")
    if step_id == "3b" and not _has_exact_release(package, command, "3", "GATE-3", releases, current_records):
        raise _error("N8N_SIMULATION_PREDECESSOR_REQUIRED", "/releases", "Step 3b requires the immutable released Step 3 plan", "Include the exact released Step 3 plan source and release record.")


def _context_graph(graph: Mapping[str, Any], step_id: str) -> Mapping[str, Any]:
    if step_id != "3b":
        return graph
    return {**graph, "initial_edges": [*graph["initial_edges"], {"from_step_id": "4b", "to_step_id": "3b"}]}


def _has_exact_release(package: Mapping[str, Any], command: Mapping[str, Any], expected_step: str, expected_gate: str, releases: Sequence[Mapping[str, Any]], current_records: Mapping[str, Mapping[str, JsonValue]]) -> bool:
    expected_release = {
        "tenant_id": command["tenant_id"], "project_id": command["project_id"], "run_id": command["run_id"], "step_id": expected_step,
        "artifact_id": "", "artifact_sha256": "", "artifact_revision": 0, "gate_id": expected_gate, "status": "released",
    }
    sources = (source for source in package["sources"] if current_records.get(source["logical_ref"], {}).get("step_id") == expected_step)
    for source in sources:
        record = current_records[source["logical_ref"]]
        if any(record.get(field) != source[field] for field in ("tenant_id", "project_id", "revision", "content_sha256", "source_status")):
            continue
        if record.get("run_id") != command["run_id"]:
            continue
        expected_release.update({"artifact_id": source["source_id"], "artifact_sha256": source["content_sha256"], "artifact_revision": source["revision"]})
        if any(all(release.get(field) == expected for field, expected in expected_release.items()) for release in releases):
            return True
    return False


def _target_matches(command: Mapping[str, Any]) -> None:
    expected = {"dispatch_tool_run": ("tool_runner", "dispatch"), "wait_for_gate": ("workflow_api", "wait"), "retry_delivery": ("delivery_queue", "retry"), "resume_run": ("workflow_api", "resume"), "dead_letter": ("delivery_queue", "dead_letter")}
    if tuple(command["target"].get(key) for key in ("service", "operation")) != expected[command["command_type"]]:
        raise _error("N8N_SIMULATION_COMMAND_INVALID", "/command/target", "target does not match command type", "Use the contract target for the requested command type.")


def _queued(state: Mapping[str, Any], command: Mapping[str, Any], first_failed_at: str | None = None) -> dict[str, Any]:
    result = copy.deepcopy(dict(state))
    entry = {key: command[key] for key in ("command_id", "command_type", "tenant_id", "project_id", "run_id", "step_id", "expected_revision", "correlation_id", "idempotency_key")}
    if first_failed_at is not None:
        entry["first_failed_at"] = first_failed_at
    result["command_queue"] = [*result["command_queue"], entry]
    return result


def _wait(command: Mapping[str, Any], event_type: str) -> dict[str, Any]:
    subscription = {"subscription_id": f"wait-{command['command_id'].removeprefix('command-')}", "schema_version": "2.0.0", "integration_mode": "simulated", "simulation_id": command["simulation_id"], "command_id": command["command_id"], "event_type": event_type, "created_at": command["requested_at"]}
    subscription.update({key: command[key] for key in ("tenant_id", "project_id", "run_id", "step_id", "expected_revision", "correlation_id", "idempotency_key")})
    return subscription


def _retry(command: Mapping[str, Any], attempt: int, first_failed_at: str, scheduled_at: str) -> dict[str, Any]:
    entry = {"retry_id": f"retry-{command['command_id'].removeprefix('command-')}-{attempt}", "schema_version": "2.0.0", "integration_mode": "simulated", "simulation_id": command["simulation_id"], "delivery_id": f"delivery-{command['command_id'].removeprefix('command-')}", "attempt": attempt, "max_attempts": 3, "first_failed_at": first_failed_at, "scheduled_at": scheduled_at, "original_command_sha256": hashlib.sha256(_canonical(command)).hexdigest()}
    entry.update({key: command[key] for key in ("correlation_id", "idempotency_key", "tenant_id", "project_id", "run_id", "step_id", "expected_revision")})
    return entry


def _dlq(command: Mapping[str, Any], first_failed_at: str, failed_at: str) -> dict[str, Any]:
    entry = {"dlq_id": f"dlq-{command['command_id'].removeprefix('command-')}", "schema_version": "2.0.0", "integration_mode": "simulated", "simulation_id": command["simulation_id"], "delivery_id": f"delivery-{command['command_id'].removeprefix('command-')}", "failure_code": "N8N_DELIVERY_EXHAUSTED", "attempt": 3, "max_attempts": 3, "original_command_id": command["command_id"], "original_command_sha256": hashlib.sha256(_canonical(command)).hexdigest(), "first_failed_at": first_failed_at, "failed_at": failed_at}
    entry.update({key: command[key] for key in ("correlation_id", "idempotency_key", "tenant_id", "project_id", "run_id", "step_id", "expected_revision")})
    return entry


def _first_failed_at(state: Mapping[str, Any], command: Mapping[str, Any]) -> str:
    timestamps = [entry["first_failed_at"] for entry in state["command_queue"] if entry["command_type"] == "retry_delivery" and entry["idempotency_key"] == command["idempotency_key"]]
    return min(timestamps) if timestamps else state["clock"]["current_time"]


def _validated(document: Mapping[str, Any], schema: Mapping[str, Any], code: str, path: str) -> dict[str, Any]:
    try:
        Draft202012Validator.check_schema(schema)
        errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document), key=lambda item: (list(item.absolute_path), item.message))
    except Exception as exc:
        raise _error(code, path, "injected schema is invalid", "Inject the approved Draft 2020-12 schema.") from exc
    if errors:
        raise _error(code, path + _path(errors[0].absolute_path), errors[0].message, "Submit a schema-valid simulated record.")
    return copy.deepcopy(dict(document))


def _canonical(document: Mapping[str, Any]) -> bytes:
    return json.dumps(document, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _path(parts: Sequence[Any]) -> str:
    return "/" + "/".join(str(part) for part in parts)


def _error(code: str, path: str, message: str, remediation: str) -> N8nSimulationError:
    return N8nSimulationError(code, path, message, remediation)
