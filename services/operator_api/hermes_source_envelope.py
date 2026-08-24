from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence

from services.context_builder import canonical_json_bytes
from services.operator_api.hermes_runs_client import HermesRunsError
from services.operator_api.models import JsonValue


def canonical_source_envelope_bytes(
    context_package: Mapping[str, JsonValue],
    source_bytes: Mapping[str, bytes],
) -> bytes:
    bindings = _package_bindings(context_package)
    supplied = _source_bytes(source_bytes)
    if set(bindings) != set(supplied):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    entries: list[dict[str, JsonValue]] = []
    for logical_ref in sorted(bindings):
        content = supplied[logical_ref]
        digest = hashlib.sha256(content).hexdigest()
        if digest != bindings[logical_ref]:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID") from error
        entries.append({"logical_ref": logical_ref, "sha256": digest, "content": text})
    return canonical_json_bytes({"context_package": context_package, "sources": entries})


def _package_bindings(context_package: Mapping[str, JsonValue]) -> dict[str, str]:
    step_id = _required_string(context_package, "step_id")
    prompt = _required_mapping(context_package, "prompt")
    bindings = {f"prompt:{step_id}": _required_string(prompt, "prompt_sha256")}
    contracts = _required_sequence(context_package, "output_contracts")
    for index, contract in enumerate(contracts, start=1):
        binding = _required_record(contract)
        _add_binding(bindings, f"output-contract:{step_id}/{index}", _required_string(binding, "contract_sha256"))
    source_refs: set[str] = set()
    for source in _required_sequence(context_package, "sources"):
        binding = _required_record(source)
        logical_ref = _required_string(binding, "logical_ref")
        digest = _required_string(binding, "content_sha256")
        if logical_ref in source_refs or logical_ref in bindings and bindings[logical_ref] != digest:
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
        source_refs.add(logical_ref)
        bindings[logical_ref] = digest
    return bindings


def _source_bytes(source_bytes: Mapping[str, bytes]) -> Mapping[str, bytes]:
    for logical_ref, content in source_bytes.items():
        if not isinstance(logical_ref, str) or not isinstance(content, bytes):
            raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return source_bytes


def _add_binding(bindings: dict[str, str], logical_ref: str, digest: str) -> None:
    if logical_ref in bindings:
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    bindings[logical_ref] = digest


def _required_string(record: Mapping[str, JsonValue], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return value


def _required_mapping(record: Mapping[str, JsonValue], field: str) -> Mapping[str, JsonValue]:
    return _required_record(record.get(field))


def _required_record(value: JsonValue | None) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return value


def _required_sequence(record: Mapping[str, JsonValue], field: str) -> Sequence[JsonValue]:
    value = record.get(field)
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise HermesRunsError("ERROR_LLM_BACKEND_RESPONSE_INVALID")
    return value
