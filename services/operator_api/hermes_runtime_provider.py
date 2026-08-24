from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Mapping, Protocol

from services.operator_api.hermes_runs_client import HermesRunResult, HermesRunsError
from services.operator_api.hermes_source_envelope import canonical_source_envelope_bytes
from services.operator_api.models import JsonValue
from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet


_HERMES_CAPABILITY = {
    "provider_id": "provider-hermes",
    "provider_kind": "gateway",
    "capability_id": "capability-hermes-runs",
}
_HERMES_PROVIDER = "provider-hermes"
_HERMES_MODEL = "gpt-5.6-sol"
_ONE_OBJECT_CONSTRAINT = "Return exactly one JSON object and no other text."


class HermesRunsExecutor(Protocol):
    def execute(self, *, input_text: str, instructions: str, session_id: str) -> HermesRunResult: ...


@dataclass(frozen=True, slots=True)
class HermesRuntimeDispatch:
    context_package: Mapping[str, JsonValue]
    llm_request: Mapping[str, JsonValue]
    worker_profile: Mapping[str, JsonValue]
    official_prompt: str
    registry: Mapping[str, JsonValue]
    parent_revision: int
    source_bytes: Mapping[str, bytes]


@dataclass(frozen=True, slots=True)
class HermesRuntimeOutput:
    output_set: ProviderOutputSet
    output_bytes: bytes
    provider_run_id: str
    model_id: str
    started_at: str
    finished_at: str
    token_usage: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class HermesRuntimeProvider:
    client: HermesRunsExecutor

    def execute(self, dispatch: HermesRuntimeDispatch) -> HermesRuntimeOutput:
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
