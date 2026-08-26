from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from services.operator_api.hermes_runs_client import HermesRunHandle, HermesRunResult, HermesRunsError, HermesRunWaiting
from services.operator_api.hermes_source_envelope import canonical_source_envelope_bytes
from services.operator_api.models import JsonValue
from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet
from services.operator_api.step_agent_results import (
    ObservedDelegation,
    ObservedToolCall,
    StepAgentResultError,
    validate_step_agent_result,
)
from services.operator_api.step_agents import StepAgentContract


_HERMES_CAPABILITY = {
    "provider_id": "provider-hermes",
    "provider_kind": "gateway",
    "capability_id": "capability-hermes-runs",
}
_HERMES_PROVIDER = "provider-hermes"
_HERMES_AGENT_CAPABILITY = {
    "provider_id": "provider-hermes-runtime",
    "provider_kind": "gateway",
    "capability_id": "capability-hermes-step-agent-runtime",
}
_HERMES_MODEL = "gpt-5.6-sol"
_ONE_OBJECT_CONSTRAINT = "Return exactly one JSON object and no other text."


class HermesRunsExecutor(Protocol):
    def execute(self, *, input_text: str, instructions: str, session_id: str) -> HermesRunResult: ...


class HermesStepRunsExecutor(Protocol):
    def start(
        self,
        *,
        input_text: str,
        instructions: str,
        session_id: str,
        model: str | None = None,
        provider: str | None = None,
        reasoning_effort: str | None = None,
    ) -> HermesRunHandle: ...

    def wait(self, handle: HermesRunHandle, *, timeout_seconds: int | None = None) -> HermesRunResult: ...

    def inspect(self, handle: HermesRunHandle) -> HermesRunResult | HermesRunWaiting | None: ...

    def approve_once(self, run_id: str, *, allow: bool) -> int: ...

    def stop(self, run_id: str) -> None: ...


@dataclass(frozen=True, slots=True)
class HermesRuntimeDispatch:
    context_package: Mapping[str, JsonValue]
    llm_request: Mapping[str, JsonValue]
    worker_profile: Mapping[str, JsonValue]
    official_prompt: str
    registry: Mapping[str, JsonValue]
    parent_revision: int
    source_bytes: Mapping[str, bytes]
    repository_root: Path | None = None
    step_agent_contract: StepAgentContract | None = None
    run_deployment_id: str | None = None


@dataclass(frozen=True, slots=True)
class HermesRuntimeOutput:
    output_set: ProviderOutputSet
    output_bytes: bytes
    provider_run_id: str
    model_id: str
    started_at: str
    finished_at: str
    token_usage: Mapping[str, int]
    output_bytes_by_ref: Mapping[str, bytes]
    raw_output_sha256: str
    observed_tool_calls: tuple[ObservedToolCall, ...] = ()
    observed_delegations: tuple[ObservedDelegation, ...] = ()
    evidence_refs: tuple[Mapping[str, str], ...] = ()
    lifecycle_events: tuple[Mapping[str, JsonValue], ...] = ()


@dataclass(frozen=True, slots=True)
class HermesStepExecution:
    dispatch: HermesRuntimeDispatch
    handle: HermesRunHandle


@dataclass(frozen=True, slots=True)
class HermesRuntimeProvider:
    client: HermesRunsExecutor | HermesStepRunsExecutor
    customer_root: Path | None = None

    def execute(self, dispatch: HermesRuntimeDispatch) -> HermesRuntimeOutput:
        if dispatch.step_agent_contract is not None:
            return self.finish_step(self.start_step(dispatch))
        return self._execute_legacy(dispatch)

    def start_step(self, dispatch: HermesRuntimeDispatch) -> HermesStepExecution:
        contract = dispatch.step_agent_contract
        if contract is None or dispatch.repository_root is None:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        _assert_agent_capability(contract, dispatch.worker_profile, dispatch.llm_request)
        start = getattr(self.client, "start", None)
        if not callable(start):
            raise HermesRunsError("ERROR_LLM_BACKEND_UNAVAILABLE")
        profile = contract.worker_profile
        inference = profile["inference_policy"]
        session_id = _required_string(dispatch.llm_request, "llm_run_request_id")
        input_text = canonical_source_envelope_bytes(dispatch.context_package, dispatch.source_bytes).decode("utf-8")
        handle = start(
            input_text=input_text,
            instructions=_step_agent_instructions(dispatch, contract),
            session_id=session_id,
            model=profile["model_policy"]["default_model_id"],
            provider=inference["upstream_provider_id"],
            reasoning_effort=inference["reasoning_effort"],
        )
        if not isinstance(handle, HermesRunHandle):
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        return HermesStepExecution(dispatch=dispatch, handle=handle)

    def finish_step(
        self,
        execution: HermesStepExecution,
        *,
        accepted_live_steering_refs: Sequence[str] = (),
    ) -> HermesRuntimeOutput:
        contract = execution.dispatch.step_agent_contract
        if contract is None:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        wait = getattr(self.client, "wait", None)
        if not callable(wait):
            raise HermesRunsError("ERROR_LLM_BACKEND_UNAVAILABLE")
        result = wait(
            execution.handle,
            timeout_seconds=contract.worker_profile["inference_policy"]["timeout_seconds"],
        )
        return self.finish_step_result(
            execution,
            result,
            accepted_live_steering_refs=accepted_live_steering_refs,
        )

    def inspect_step(
        self,
        execution: HermesStepExecution,
        *,
        accepted_live_steering_refs: Sequence[str] = (),
    ) -> HermesRuntimeOutput | HermesRunWaiting | None:
        inspect = getattr(self.client, "inspect", None)
        if not callable(inspect):
            raise HermesRunsError("ERROR_LLM_BACKEND_UNAVAILABLE")
        observed = inspect(execution.handle)
        if isinstance(observed, HermesRunResult):
            return self.finish_step_result(
                execution,
                observed,
                accepted_live_steering_refs=accepted_live_steering_refs,
            )
        return observed

    def approve_step(self, execution: HermesStepExecution, *, allow: bool) -> None:
        approve = getattr(self.client, "approve_once", None)
        if not callable(approve):
            raise HermesRunsError("ERROR_LLM_BACKEND_UNAVAILABLE")
        approve(execution.handle.run_id, allow=allow)

    def stop_step(self, execution: HermesStepExecution) -> None:
        stop = getattr(self.client, "stop", None)
        if not callable(stop):
            raise HermesRunsError("ERROR_LLM_BACKEND_UNAVAILABLE")
        stop(execution.handle.run_id)

    def finish_step_result(
        self,
        execution: HermesStepExecution,
        result: HermesRunResult,
        *,
        accepted_live_steering_refs: Sequence[str] = (),
    ) -> HermesRuntimeOutput:
        dispatch = execution.dispatch
        contract = dispatch.step_agent_contract
        if contract is None or dispatch.repository_root is None or self.customer_root is None:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        _assert_terminal_result(result, contract.worker_profile)
        validated = validate_step_agent_result(
            repository_root=dispatch.repository_root,
            customer_root=self.customer_root,
            contract=contract,
            request=dispatch.llm_request,
            package=dispatch.context_package,
            raw_output=result.output,
            events=result.events,
            event_stream_error=result.event_stream_error,
            accepted_live_steering_refs=accepted_live_steering_refs,
        )
        created_at = _datetime(result.updated_at)
        outputs = tuple(
            ProviderOutput(
                contract_id=output.contract_id,
                content_bytes=output.content_bytes,
                content_sha256=output.content_sha256,
                content_type="application/json",
                tenant_id=_required_string(dispatch.llm_request, "tenant_id"),
                project_id=_required_string(dispatch.llm_request, "project_id"),
                run_id=_required_string(dispatch.llm_request, "run_id"),
                step_id=_required_string(dispatch.llm_request, "step_id"),
                idempotency_key=_required_string(dispatch.llm_request, "idempotency_key"),
                parent_revision=dispatch.parent_revision,
                target_revision=dispatch.parent_revision + 1,
                created_at=created_at,
            )
            for output in validated.outputs
        )
        try:
            output_set = ProviderOutputSet.from_registry(
                dict(dispatch.registry),
                primary=outputs[0],
                supporting=outputs[1:],
            )
        except (IndexError, ValueError) as error:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error
        return HermesRuntimeOutput(
            output_set=output_set,
            output_bytes=outputs[0].content_bytes,
            provider_run_id=result.run_id,
            model_id=result.model,
            started_at=_rfc3339(result.created_at),
            finished_at=_rfc3339(result.updated_at),
            token_usage=_token_usage(result),
            output_bytes_by_ref={output.logical_ref: output.content_bytes for output in validated.outputs},
            raw_output_sha256=validated.raw_sha256,
            observed_tool_calls=validated.tool_calls,
            observed_delegations=validated.delegations,
            evidence_refs=validated.evidence_refs,
            lifecycle_events=_lifecycle_events(result.events),
        )

    def _execute_legacy(self, dispatch: HermesRuntimeDispatch) -> HermesRuntimeOutput:
        _assert_capability(dispatch.worker_profile, dispatch.llm_request)
        contract_id = _single_contract_id(dispatch.llm_request)
        session_id = _required_string(dispatch.llm_request, "llm_run_request_id")
        input_text = canonical_source_envelope_bytes(dispatch.context_package, dispatch.source_bytes).decode("utf-8")
        try:
            result = self.client.execute(
                input_text=input_text,
                instructions=f"{dispatch.official_prompt}\n\n{_ONE_OBJECT_CONSTRAINT}",
                session_id=session_id,
            )
        except HermesRunsError:
            raise
        if result.last_event != "run.completed":
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        if result.model != _HERMES_MODEL:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        output_bytes = _one_json_object_bytes(result.output)
        started_at = _rfc3339(result.created_at)
        finished_at = _rfc3339(result.updated_at)
        try:
            created_at = datetime.fromtimestamp(result.updated_at, UTC)
        except (OSError, OverflowError, ValueError) as error:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error
        primary = ProviderOutput(
            contract_id=contract_id,
            content_bytes=output_bytes,
            content_sha256=hashlib.sha256(output_bytes).hexdigest(),
            content_type="application/json",
            tenant_id=_required_string(dispatch.llm_request, "tenant_id"),
            project_id=_required_string(dispatch.llm_request, "project_id"),
            run_id=_required_string(dispatch.llm_request, "run_id"),
            step_id=_required_string(dispatch.llm_request, "step_id"),
            idempotency_key=_required_string(dispatch.llm_request, "idempotency_key"),
            parent_revision=dispatch.parent_revision,
            target_revision=dispatch.parent_revision + 1,
            created_at=created_at,
        )
        try:
            output_set = ProviderOutputSet.from_registry(dict(dispatch.registry), primary=primary)
        except ValueError as error:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error
        return HermesRuntimeOutput(
            output_set=output_set,
            output_bytes=output_bytes,
            provider_run_id=result.run_id,
            model_id=result.model,
            started_at=started_at,
            finished_at=finished_at,
            token_usage={
                "input_tokens": result.usage.input_tokens,
                "output_tokens": result.usage.output_tokens,
                "total_tokens": result.usage.total_tokens,
            },
            output_bytes_by_ref={"runtime:provider-output/primary": output_bytes},
            raw_output_sha256=hashlib.sha256(result.output.encode("utf-8")).hexdigest(),
        )


def _assert_capability(profile: Mapping[str, JsonValue], request: Mapping[str, JsonValue]) -> None:
    capability = profile.get("provider_capability_ref")
    model_policy = profile.get("model_policy")
    if (
        capability != _HERMES_CAPABILITY
        or not isinstance(model_policy, Mapping)
        or model_policy.get("default_model_id") != _HERMES_MODEL
        or model_policy.get("allowed_model_ids") != [_HERMES_MODEL]
        or request.get("provider_id") != _HERMES_PROVIDER
        or request.get("model_id") != _HERMES_MODEL
    ):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")


def _assert_agent_capability(
    contract: StepAgentContract,
    profile: Mapping[str, JsonValue],
    request: Mapping[str, JsonValue],
) -> None:
    contract_profile = contract.worker_profile
    model_policy = contract_profile.get("model_policy")
    inference_policy = contract_profile.get("inference_policy")
    tool_binding = contract_profile.get("tool_policy")
    if (
        profile != contract_profile
        or contract_profile.get("provider_capability_ref") != _HERMES_AGENT_CAPABILITY
        or not isinstance(model_policy, Mapping)
        or model_policy.get("default_model_id") != _HERMES_MODEL
        or model_policy.get("allowed_model_ids") != [_HERMES_MODEL]
        or not isinstance(inference_policy, Mapping)
        or inference_policy.get("upstream_provider_id") != "openai-codex"
        or inference_policy.get("fallback_mode") != "fail_closed"
        or not isinstance(tool_binding, Mapping)
        or request.get("provider_id") != _HERMES_AGENT_CAPABILITY["provider_id"]
        or request.get("model_id") != _HERMES_MODEL
        or request.get("step_id") != contract.step_id
        or request.get("worker_profile_id") != contract_profile.get("worker_profile_id")
        or request.get("worker_profile_version") != contract_profile.get("profile_version")
        or request.get("worker_profile_sha256") != contract_profile.get("profile_sha256")
        or request.get("tool_policy_id") != tool_binding.get("tool_policy_id")
        or request.get("tool_policy_version") != tool_binding.get("policy_version")
        or request.get("tool_policy_sha256") != tool_binding.get("policy_sha256")
    ):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")


def _assert_terminal_result(result: HermesRunResult, profile: Mapping[str, Any]) -> None:
    inference = profile["inference_policy"]
    if (
        result.last_event != "run.completed"
        or result.model != profile["model_policy"]["default_model_id"]
        or result.usage.input_tokens <= 0
        or result.usage.output_tokens <= 0
        or result.usage.total_tokens != result.usage.input_tokens + result.usage.output_tokens
        or result.usage.output_tokens > inference["max_output_tokens"]
    ):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")


def _step_agent_instructions(dispatch: HermesRuntimeDispatch, contract: StepAgentContract) -> str:
    request = dispatch.llm_request
    package = dispatch.context_package
    revision_refs = [
        source["logical_ref"]
        for source in package["sources"]
        if source["source_kind"] == "operator_instruction"
    ]
    envelope_template: dict[str, Any] = {
        "schema_version": "1.1.0",
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
        "outputs": [
            {"contract_id": binding["contract_id"], "content": {}}
            for binding in contract.prompt_entry["output_contracts"]
        ],
        "evidence_refs": [],
    }
    if revision_refs:
        envelope_template["operator_steering_refs"] = revision_refs
    execution_contract = {
        "agent_contract": {
            "agent_contract_id": contract.entry["agent_contract_id"],
            "agent_contract_version": contract.entry["agent_contract_version"],
            "worker_profile_id": contract.worker_profile["worker_profile_id"],
            "worker_profile_version": contract.worker_profile["profile_version"],
            "worker_profile_sha256": contract.worker_profile["profile_sha256"],
            "tool_policy_id": contract.tool_policy["tool_policy_id"],
            "tool_policy_version": contract.tool_policy["policy_version"],
            "tool_policy_sha256": contract.tool_policy["policy_sha256"],
        },
        "allowed_gateway_operations": contract.tool_policy["allowed_gateway_operations"],
        "required_gateway_operations": list(contract.required_operation_ids),
        "delegation_policy": contract.tool_policy["delegation_policy"],
        "output_envelope_template": envelope_template,
        "rules": [
            "Treat every source in the canonical input envelope according to its declared trust and lifecycle status.",
            "Copy every authoritative_output_binding into the matching output field exactly. Never recalculate, normalize or replace an authoritative binding.",
            "Use only the exact Heartweb MCP tools named by allowed_gateway_operations. Never call providers directly.",
            "Pass the exact llm_run_request_id from this execution contract to every Heartweb MCP tool call. Never invent, omit or reuse another execution identity.",
            "Call every required_gateway_operation and copy only its exact evidence_ref object into evidence_refs. Never copy the full evidence record into evidence_refs.",
            "When a failed Heartweb tool result contains error.code, copy that exact code into failure.code instead of replacing it with a generic tool failure code.",
            "For any permitted child review, prefix the child goal with PURPOSE=<allowed-purpose> on the first line.",
            "A live steering message contains a versioned logical_ref. Apply it and append that ref to operator_steering_refs in receipt order.",
            "On success, return every output contract exactly once and in the registered order. Multi-output Steps are one atomic candidate revision.",
            "On fail-closed, return outputs as an empty array and add failure with code, message, remediation and optional details. Never place a failure document inside an output content field.",
            "Do not set workflow state, gates, approvals, releases, artifact revisions or canonical Heartweb identities.",
            "Return one strict JSON object matching the output envelope. No prose and no code fence.",
        ],
    }
    authoritative_bindings = _authoritative_output_bindings(dispatch)
    if authoritative_bindings is not None:
        execution_contract["authoritative_output_bindings"] = authoritative_bindings
    return (
        f"{dispatch.official_prompt}\n\n"
        "<heartweb_step_agent_execution_contract>\n"
        f"{json.dumps(execution_contract, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}\n"
        "</heartweb_step_agent_execution_contract>\n\n"
        f"{_ONE_OBJECT_CONSTRAINT}"
    )


def _authoritative_output_bindings(dispatch: HermesRuntimeDispatch) -> dict[str, JsonValue] | None:
    if dispatch.llm_request.get("step_id") != "0":
        return None
    sources = dispatch.context_package.get("sources")
    if not isinstance(sources, list):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    intake_sources = [
        source
        for source in sources
        if isinstance(source, Mapping) and source.get("source_kind") == "project_intake"
    ]
    if len(intake_sources) != 1:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    logical_ref = intake_sources[0].get("logical_ref")
    if not isinstance(logical_ref, str):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    content = dispatch.source_bytes.get(logical_ref)
    if not isinstance(content, bytes):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    try:
        intake = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error
    reviewed = intake.get("reviewed") if isinstance(intake, dict) else None
    project_v2 = reviewed.get("project_v2") if isinstance(reviewed, dict) else None
    project_tenant = project_v2.get("tenant") if isinstance(project_v2, dict) else None
    intake_source_sha256 = intake.get("source_sha256") if isinstance(intake, dict) else None
    tenant_id = dispatch.llm_request.get("tenant_id")
    project_id = dispatch.llm_request.get("project_id")
    if (
        not isinstance(project_v2, dict)
        or not isinstance(project_tenant, dict)
        or intake.get("tenant_id") != tenant_id
        or intake.get("project_id") != project_id
        or project_tenant.get("tenant_id") != tenant_id
        or project_v2.get("project_id") != project_id
        or not isinstance(intake_source_sha256, str)
        or len(intake_source_sha256) != 64
        or any(character not in "0123456789abcdef" for character in intake_source_sha256)
    ):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    project_v2_sha256 = hashlib.sha256(
        json.dumps(
            project_v2,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    deployments = project_v2.get("market_deployments")
    if not isinstance(deployments, list):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    if dispatch.run_deployment_id is not None:
        bound = [
            deployment
            for deployment in deployments
            if isinstance(deployment, dict)
            and deployment.get("deployment_id") == dispatch.run_deployment_id
            and deployment.get("market_phase") == "active"
        ]
    else:
        bound = [
            deployment
            for deployment in deployments
            if isinstance(deployment, dict)
            and deployment.get("market_phase") == "active"
            and deployment.get("deployment_role") == "primary"
        ]
    if len(bound) != 1:
        raise HermesRunsError("ERROR_RUN_DEPLOYMENT_UNBOUND")
    deployment = bound[0]
    verification = deployment.get("provider_location_verification")
    customer = project_v2.get("customer")
    if (
        not isinstance(verification, dict)
        or verification.get("status") != "verified"
        or not isinstance(verification.get("target_id"), str)
        or not isinstance(verification.get("provider_location_code"), int)
        or not isinstance(customer, dict)
        or not isinstance(customer.get("customer_id"), str)
    ):
        raise HermesRunsError("ERROR_LOCATION_UNVERIFIED")
    deployment_sha256 = hashlib.sha256(
        json.dumps(
            deployment,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        "binding_mode": "copy_exactly",
        "deployment_binding": deployment,
        "source_binding": {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "customer_id": customer["customer_id"],
            "market_id": deployment["market_id"],
            "deployment_id": deployment["deployment_id"],
            "language": deployment["language"],
            "locale": deployment["locale"],
            "country": deployment["country_code"],
            "provider_target_id": verification["target_id"],
            "provider_location_code": verification["provider_location_code"],
            "deployment_sha256": deployment_sha256,
            "project_v2_sha256": project_v2_sha256,
            "intake_source_sha256": intake_source_sha256,
        },
    }


def _token_usage(result: HermesRunResult) -> dict[str, int]:
    return {
        "input_tokens": result.usage.input_tokens,
        "output_tokens": result.usage.output_tokens,
        "total_tokens": result.usage.total_tokens,
    }


def _lifecycle_events(events: Sequence[Mapping[str, object]]) -> tuple[Mapping[str, JsonValue], ...]:
    accepted = {"tool.started", "tool.completed", "subagent.start", "subagent.complete"}
    records: list[Mapping[str, JsonValue]] = []
    for sequence, event in enumerate(events, start=1):
        event_kind = event.get("event")
        if event_kind not in accepted:
            continue
        event_json = json.dumps(dict(event), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        records.append(
            {
                "sequence": sequence,
                "event": event_kind,
                "event_json": event_json,
                "event_sha256": hashlib.sha256(event_json.encode("utf-8")).hexdigest(),
            }
        )
    return tuple(records)


def _datetime(epoch: int | float) -> datetime:
    try:
        return datetime.fromtimestamp(epoch, UTC)
    except (OSError, OverflowError, ValueError) as error:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error


def _single_contract_id(request: Mapping[str, JsonValue]) -> str:
    contracts = request.get("output_contracts")
    if not isinstance(contracts, list) or len(contracts) != 1 or not isinstance(contracts[0], Mapping):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    contract_id = contracts[0].get("contract_id")
    if not isinstance(contract_id, str):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return contract_id


def _required_string(record: Mapping[str, JsonValue], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return value


def _one_json_object_bytes(output: str) -> bytes:
    try:
        output_bytes = output.encode("utf-8")
        document = json.loads(output_bytes)
    except (UnicodeEncodeError, json.JSONDecodeError) as error:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error
    if not isinstance(document, dict):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return output_bytes


def _rfc3339(epoch: int | float) -> str:
    try:
        value = datetime.fromtimestamp(epoch, UTC)
    except (OSError, OverflowError, ValueError) as error:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")
