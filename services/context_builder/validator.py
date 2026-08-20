from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias

from services.context_builder.builder import ContextBuildError, JsonValue, canonical_json_bytes, parse_rfc3339_utc, sha256
from services.runtime_contracts.llm_records import RuntimeContractValidator


RecordMap: TypeAlias = Mapping[str, Mapping[str, JsonValue]]


@dataclass(frozen=True, slots=True)
class ContextValidationError:
    code: str
    path: str
    message: str
    remediation: str


@dataclass(frozen=True, slots=True)
class ContextValidationResult:
    errors: tuple[ContextValidationError, ...]

    @property
    def valid(self) -> bool:
        return not self.errors


def build_llm_request(
    package: Mapping[str, JsonValue],
    profile: Mapping[str, JsonValue],
    identifiers: Mapping[str, str],
    requested_at: str,
    runtime_validator: RuntimeContractValidator,
    context_result: ContextValidationResult,
    cache_hint: Mapping[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    if not context_result.valid:
        raise ContextBuildError("ERROR_LLM_REQUEST_INVALID", "/context_package_id", "a request requires a semantically valid stored package", "Repair and revalidate the package before constructing a request.")
    mode = package["trigger"]
    cache_allowed = mode in {"retry", "resume"} and cache_hint is not None
    request: dict[str, JsonValue] = {
        "llm_run_request_id": identifiers["llm_run_request_id"], "schema_version": "1.0.0", "tenant_id": package["tenant_id"], "project_id": package["project_id"], "run_id": package["run_id"], "step_id": package["step_id"], "target_revision": package["target_revision"], "correlation_id": identifiers["correlation_id"], "idempotency_key": identifiers["idempotency_key"], "run_mode": mode, "logical_session_id": package["logical_session_id"], "logical_session_revision": package["logical_session_revision"], "context_package_id": package["context_package_id"], "context_package_sha256": package["package_sha256"], "worker_profile_id": profile["worker_profile_id"], "worker_profile_version": profile["profile_version"], "worker_profile_sha256": profile["profile_sha256"], "provider_id": profile["provider_capability_ref"]["provider_id"], "model_id": profile["model_policy"]["default_model_id"], "tool_policy_id": profile["tool_policy"]["tool_policy_id"], "tool_policy_version": profile["tool_policy"]["policy_version"], "tool_policy_sha256": profile["tool_policy"]["policy_sha256"], "input_sha256": package["package_sha256"], "output_contracts": package["output_contracts"], "dispatch_policy": {"execution": "fresh_or_reuse_after_validation" if cache_allowed else "fresh", "technical_session_reuse": "cache_hint" if cache_allowed else "forbidden"}, "requested_at": requested_at,
    }
    if cache_allowed:
        request["technical_session_cache_hint"] = cache_hint
    result = runtime_validator.validate("llm-run-request", request)
    if not result.valid:
        first = result.errors[0]
        raise ContextBuildError("ERROR_LLM_REQUEST_INVALID", first.path, first.message, "Correct the request identity or worker profile.")
    return request


def validate_context_package(
    package: Mapping[str, JsonValue],
    source_bytes: Mapping[str, bytes],
    current_records: RecordMap,
    workflow_graph: Mapping[str, JsonValue],
    release_records: Sequence[Mapping[str, JsonValue]],
    revision_requests: Sequence[Mapping[str, JsonValue]],
    runtime_validator: RuntimeContractValidator,
    prompt_registry: Mapping[str, JsonValue],
    evaluation_at: str,
) -> ContextValidationResult:
    runtime = runtime_validator.validate("context-package", package)
    if not runtime.valid:
        return ContextValidationResult(tuple(_error("ERROR_CONTEXT_SCHEMA_INVALID", item.path, item.message) for item in runtime.errors))
    errors = [*_hash_errors(package), *_source_errors(package, source_bytes, current_records, workflow_graph, evaluation_at), *_binding_errors(package, prompt_registry, source_bytes), *_lineage_errors(package, current_records, workflow_graph, release_records, revision_requests)]
    return ContextValidationResult(tuple(sorted(errors, key=lambda item: (item.code, item.path, item.message))))


def validate_llm_request(
    request: Mapping[str, JsonValue],
    package: Mapping[str, JsonValue],
    profile: Mapping[str, JsonValue],
    runtime_validator: RuntimeContractValidator,
    prior_request: Mapping[str, JsonValue] | None = None,
) -> ContextValidationResult:
    runtime = runtime_validator.validate("llm-run-request", request)
    if not runtime.valid:
        return ContextValidationResult(tuple(_error("ERROR_LLM_REQUEST_INVALID", item.path, item.message) for item in runtime.errors))
    fields = ("tenant_id", "project_id", "run_id", "step_id", "target_revision", "logical_session_id", "logical_session_revision")
    errors = [_error("ERROR_LLM_REQUEST_INVALID", f"/{field}", "request must exactly project the stored package") for field in fields if request[field] != package[field]]
    expected = {"context_package_id": package["context_package_id"], "context_package_sha256": package["package_sha256"], "input_sha256": package["package_sha256"], "worker_profile_id": profile["worker_profile_id"], "worker_profile_version": profile["profile_version"], "worker_profile_sha256": profile["profile_sha256"], "provider_id": profile["provider_capability_ref"]["provider_id"], "model_id": profile["model_policy"]["default_model_id"], "tool_policy_id": profile["tool_policy"]["tool_policy_id"], "tool_policy_version": profile["tool_policy"]["policy_version"], "tool_policy_sha256": profile["tool_policy"]["policy_sha256"], "output_contracts": package["output_contracts"]}
    errors.extend(_error("ERROR_LLM_REQUEST_INVALID", f"/{field}", "request does not match package or enabled worker profile") for field, value in expected.items() if request[field] != value)
    if profile["enabled"] is not True or package["step_id"] not in profile["allowed_steps"]:
        errors.append(_error("ERROR_LLM_REQUEST_INVALID", "/worker_profile_id", "worker profile is disabled or cannot run this step"))
    if prior_request is not None and request["idempotency_key"] == prior_request.get("idempotency_key") and canonical_json_bytes(request) != canonical_json_bytes(prior_request):
        errors.append(_error("ERROR_LLM_REQUEST_IDEMPOTENCY_CONFLICT", "/idempotency_key", "same idempotency key has different request content"))
    return ContextValidationResult(tuple(sorted(errors, key=lambda item: (item.code, item.path))))


def validate_llm_result(
    result: Mapping[str, JsonValue],
    request: Mapping[str, JsonValue],
    output_bytes: Mapping[str, bytes],
    runtime_validator: RuntimeContractValidator,
) -> ContextValidationResult:
    runtime = runtime_validator.validate("llm-run-result", result)
    if not runtime.valid:
        return ContextValidationResult(tuple(_error("ERROR_LLM_RESULT_INVALID", item.path, item.message) for item in runtime.errors))
    fields = ("tenant_id", "project_id", "run_id", "step_id", "target_revision", "context_package_id", "context_package_sha256", "worker_profile_id", "worker_profile_version", "worker_profile_sha256", "provider_id", "model_id", "tool_policy_id", "tool_policy_version", "tool_policy_sha256", "input_sha256")
    errors = [_error("ERROR_LLM_RESULT_INVALID", f"/{field}", "result must exactly project its request") for field in fields if result[field] != request[field]]
    if result["llm_run_request_id"] != request["llm_run_request_id"]:
        errors.append(_error("ERROR_LLM_RESULT_INVALID", "/llm_run_request_id", "result request ID must match"))
    if result["result_sha256"] != result_record_sha256(result):
        errors.append(_error("ERROR_LLM_RESULT_INVALID", "/result_sha256", "result hash does not match the complete result record"))
    if result["status"] == "succeeded":
        output = result["output"]
        content = output_bytes.get(output["logical_ref"])
        if content is None or hashlib.sha256(content).hexdigest() != output["content_sha256"]:
            errors.append(_error("ERROR_LLM_RESULT_INVALID", "/output/content_sha256", "candidate output bytes do not match result hash"))
    return ContextValidationResult(tuple(sorted(errors, key=lambda item: (item.code, item.path))))


def result_record_sha256(result: Mapping[str, JsonValue]) -> str:
    return sha256({key: value for key, value in result.items() if key != "result_sha256"})


def _hash_errors(package: Mapping[str, JsonValue]) -> list[ContextValidationError]:
    errors: list[ContextValidationError] = []
    if package["source_manifest_sha256"] != sha256(package["sources"]):
        errors.append(_error("ERROR_CONTEXT_PACKAGE_HASH_MISMATCH", "/source_manifest_sha256", "source manifest hash is incorrect"))
    payload = {key: value for key, value in package.items() if key != "package_sha256"}
    if package["package_sha256"] != sha256(payload):
        errors.append(_error("ERROR_CONTEXT_PACKAGE_HASH_MISMATCH", "/package_sha256", "package hash is incorrect"))
    return errors


def _source_errors(package: Mapping[str, JsonValue], source_bytes: Mapping[str, bytes], records: RecordMap, graph: Mapping[str, JsonValue], evaluation_at: str) -> list[ContextValidationError]:
    errors: list[ContextValidationError] = []
    try:
        evaluated_at = parse_rfc3339_utc(evaluation_at, "/evaluation_at")
    except ContextBuildError as error:
        return [_error(error.code, error.path, error.message)]
    seen: set[str] = set()
    for index, source in enumerate(package["sources"]):
        ref = source["logical_ref"]
        if ref in seen:
            errors.append(_error("ERROR_CONTEXT_SOURCE_INVALID", f"/sources/{index}/logical_ref", "logical references must be unique"))
        seen.add(ref)
        content = source_bytes.get(ref)
        record = records.get(ref)
        if content is None or record is None:
            errors.append(_error("ERROR_CONTEXT_SOURCE_INVALID", f"/sources/{index}", "source bytes or current record are missing"))
            continue
        if source["source_kind"] not in {"official_prompt", "output_contract"} and hashlib.sha256(content).hexdigest() != source["content_sha256"]:
            errors.append(_error("ERROR_CONTEXT_SOURCE_INVALID", f"/sources/{index}/content_sha256", "source hash differs from exact current bytes or record"))
        for field in ("source_id", "tenant_id", "project_id", "revision", "content_sha256", "source_status"):
            if record.get(field) != source[field]:
                errors.append(_error("ERROR_CONTEXT_IDENTITY_MISMATCH", f"/sources/{index}/{field}", "source record identity differs from package"))
        source_steps = {edge.get("from_step_id") for edge in graph.get("initial_edges", ()) if edge.get("to_step_id") == package["step_id"]}
        if source["source_kind"] == "released_predecessor":
            if record.get("step_id") not in source_steps:
                errors.append(_error("ERROR_CONTEXT_IDENTITY_MISMATCH", f"/sources/{index}/step_id", "predecessor record step does not match the graph edge"))
            if record.get("run_id") != package["run_id"]:
                errors.append(_error("ERROR_CONTEXT_IDENTITY_MISMATCH", f"/sources/{index}/run_id", "predecessor record run does not match package lineage"))
        historical_comparison = source["source_kind"] == "evidence" and source["source_status"] == "historical" and source.get("permitted_use") == "comparison_only"
        valid_until = record.get("valid_until")
        try:
            stale = valid_until is not None and parse_rfc3339_utc(valid_until, f"/sources/{index}/valid_until") <= evaluated_at
        except ContextBuildError as error:
            errors.append(_error(error.code, error.path, error.message))
            stale = True
        if record.get("source_status") == "superseded" or record.get("source_status") == "historical" and not historical_comparison or stale:
            errors.append(_error("ERROR_CONTEXT_SOURCE_INVALID", f"/sources/{index}", "source is stale or superseded"))
        if source["trust_level"] == "untrusted" and (source["source_kind"] != "evidence" or not source.get("untrusted_reason") or not source.get("permitted_use")):
            errors.append(_error("ERROR_CONTEXT_TRUST_POLICY_INVALID", f"/sources/{index}", "untrusted content is data only and requires permitted use"))
    return errors


def _binding_errors(package: Mapping[str, JsonValue], registry: Mapping[str, JsonValue], source_bytes: Mapping[str, bytes]) -> list[ContextValidationError]:
    entries = registry.get("entries", ())
    entry = next((item for item in entries if item.get("step_id") == package["step_id"] and item.get("active") is True), None)
    if entry is None or package["prompt"] != {field: entry[field] for field in ("prompt_id", "prompt_version", "prompt_path", "prompt_sha256")} or hashlib.sha256(source_bytes.get(f"prompt:{package['step_id']}", b"")).hexdigest() != entry["prompt_sha256"]:
        return [_error("ERROR_CONTEXT_PROMPT_BINDING_INVALID", "/prompt", "package prompt does not exactly bind the active registry")]
    contracts_match = package["output_contracts"] == entry["output_contracts"] and all(hashlib.sha256(source_bytes.get(f"output-contract:{package['step_id']}/{index}", b"")).hexdigest() == contract["contract_sha256"] for index, contract in enumerate(entry["output_contracts"], start=1))
    if not contracts_match:
        return [_error("ERROR_CONTEXT_OUTPUT_CONTRACT_INVALID", "/output_contracts", "package output contracts do not exactly bind the registry")]
    return []


def _lineage_errors(package: Mapping[str, JsonValue], records: RecordMap, graph: Mapping[str, JsonValue], releases: Sequence[Mapping[str, JsonValue]], requests: Sequence[Mapping[str, JsonValue]]) -> list[ContextValidationError]:
    sources = package["sources"]
    kind_set = {source["source_kind"] for source in sources}
    errors: list[ContextValidationError] = []
    if package["step_id"] == "0" and "project_intake" not in kind_set or package["step_id"] != "0" and "project_v2" not in kind_set:
        errors.append(_error("ERROR_CONTEXT_SOURCE_INVALID", "/sources", "Step 0 requires intake and later steps require Project V2"))
    required = next((step for step in graph.get("steps", ()) if step.get("step_id") == package["step_id"]), {})
    predecessor = next((source for source in sources if source["source_kind"] == "released_predecessor"), None)
    predecessor_run_id = records.get(predecessor["logical_ref"], {}).get("run_id") if predecessor is not None else None
    edge_sources = {edge.get("from_step_id") for edge in graph.get("initial_edges", ()) if edge.get("to_step_id") == package["step_id"]}
    release_matches = predecessor is not None and any(
        release.get("tenant_id") == package["tenant_id"] and release.get("project_id") == package["project_id"]
        and release.get("status") == "released" and release.get("artifact_id") == predecessor["source_id"]
        and release.get("artifact_sha256") == predecessor["content_sha256"] and release.get("artifact_revision") == predecessor["revision"]
        and release.get("step_id") in edge_sources and release.get("run_id") == predecessor_run_id
        for release in releases
    )
    if required.get("requires_released_predecessor") is True and not release_matches:
        errors.append(_error("ERROR_CONTEXT_PREDECESSOR_INVALID", "/sources", "required released predecessor lacks matching release record"))
    if package["trigger"] == "revision":
        rejected = next((source for source in sources if source["source_kind"] == "rejected_artifact"), None)
        request = next((source for source in sources if source["source_kind"] == "revision_request"), None)
        matched = next((item for item in requests if request is not None and item.get("revision_request_id") == request["source_id"]), None)
        if rejected is None or request is None or "operator_instruction" not in kind_set or matched is None or matched.get("current_artifact_id") != rejected["source_id"] or matched.get("current_artifact_sha256") != rejected["content_sha256"] or package["target_revision"] <= rejected["revision"]:
            errors.append(_error("ERROR_CONTEXT_REVISION_BINDING_INVALID", "/revision_context", "revision sources must bind a new revision request and rejected artifact"))
    return errors


def _error(code: str, path: str, message: str) -> ContextValidationError:
    return ContextValidationError(code, path, message, "Correct the immutable context input and revalidate before dispatch.")
