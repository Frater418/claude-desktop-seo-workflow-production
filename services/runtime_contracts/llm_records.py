from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence, TypeAlias

from jsonschema import Draft202012Validator, FormatChecker

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | Mapping[str, "JsonValue"] | Sequence["JsonValue"]
WORKFLOW_STEPS = frozenset(("0", "1", "1b", "1c", "2", "3", "3b", "4a", "4b"))


@dataclass(frozen=True, slots=True)
class ValidationError:
    code: str
    path: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    errors: tuple[ValidationError, ...]

    @property
    def valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True, slots=True)
class RuntimeContractError(Exception):
    result: ValidationResult

    def __str__(self) -> str:
        return "; ".join(f"{error.code}:{error.path}" for error in self.result.errors)


class RuntimeContractValidator:
    def __init__(
        self,
        schemas: Mapping[str, Mapping[str, JsonValue]],
        prompt_registry: Mapping[str, JsonValue],
    ) -> None:
        for schema in schemas.values():
            Draft202012Validator.check_schema(schema)
        self._validators = {
            record_kind: Draft202012Validator(schema, format_checker=FormatChecker())
            for record_kind, schema in schemas.items()
        }
        self._prompt_registry = prompt_registry

    def validate(self, record_kind: str, document: Mapping[str, JsonValue]) -> ValidationResult:
        schema_errors = tuple(
            ValidationError("LLM_RUNTIME_SCHEMA_INVALID", _path(error.absolute_path), error.message)
            for error in sorted(
                self._validators[record_kind].iter_errors(document),
                key=lambda error: (_path(error.absolute_path), error.message),
            )
        )
        if schema_errors:
            return ValidationResult(schema_errors)
        errors = _semantic_errors(record_kind, document, self._prompt_registry)
        return ValidationResult(tuple(errors))

    def assert_valid(self, record_kind: str, document: Mapping[str, JsonValue]) -> None:
        result = self.validate(record_kind, document)
        if not result.valid:
            raise RuntimeContractError(result)


def _path(parts: Sequence[JsonValue]) -> str:
    return "/" + "/".join(str(part) for part in parts)


def _error(code: str, path: str, message: str) -> ValidationError:
    return ValidationError(code, path, message)


def _semantic_errors(
    record_kind: str,
    document: Mapping[str, JsonValue],
    registry: Mapping[str, JsonValue],
) -> list[ValidationError]:
    match record_kind:
        case "official-prompt-registry":
            return _registry_errors(document)
        case "logical-project-session":
            return _session_errors(document)
        case "worker-profile":
            return _worker_errors(document)
        case "context-package":
            return _context_errors(document, registry)
        case "llm-run-request":
            return _request_errors(document)
        case "llm-run-result":
            return _result_errors(document)
        case _:
            return [_error("LLM_RUNTIME_RECORD_KIND_INVALID", "/", "unsupported runtime record kind")]


def _registry_errors(registry: Mapping[str, JsonValue]) -> list[ValidationError]:
    entries = registry["entries"]
    errors: list[ValidationError] = []
    steps: list[str] = []
    prompt_ids: list[str] = []
    prompt_paths: list[str] = []
    for index, entry in enumerate(entries):
        step_id = entry["step_id"]
        prompt_id = entry["prompt_id"]
        steps.append(step_id)
        prompt_ids.append(prompt_id)
        prompt_paths.append(entry["prompt_path"])
        if prompt_id != f"heartweb.step.{step_id}":
            errors.append(_error("LLM_RUNTIME_REGISTRY_INVALID", f"/entries/{index}/prompt_id", "prompt ID must bind its step"))
        contracts = entry["output_contracts"]
        paths = [contract["contract_path"] for contract in contracts]
        if len(paths) != len(set(paths)):
            errors.append(_error("LLM_RUNTIME_REGISTRY_INVALID", f"/entries/{index}/output_contracts", "output contract paths must be unique"))
    if set(steps) != WORKFLOW_STEPS or len(steps) != len(set(steps)):
        errors.append(_error("LLM_RUNTIME_REGISTRY_INVALID", "/entries", "entries must be unique and match workflow steps"))
    if len(prompt_ids) != len(set(prompt_ids)) or len(prompt_paths) != len(set(prompt_paths)):
        errors.append(_error("LLM_RUNTIME_REGISTRY_INVALID", "/entries", "prompt IDs and paths must be unique"))
    return errors


def _session_errors(document: Mapping[str, JsonValue]) -> list[ValidationError]:
    source = document["project_source"]
    reference = source["logical_ref"]
    mode = document["binding_mode"]
    errors: list[ValidationError] = []
    if mode == "project_intake" and (source["source_kind"] != "project_intake" or not reference.startswith("runtime:intake/")):
        errors.append(_error("LLM_RUNTIME_SESSION_INVALID", "/project_source/logical_ref", "intake mode requires an intake reference"))
    if mode == "project_v2" and (source["source_kind"] != "project_v2" or not reference.startswith("runtime:project/")):
        errors.append(_error("LLM_RUNTIME_SESSION_INVALID", "/project_source/logical_ref", "project V2 mode requires a project reference"))
    for field in ("supersedes_logical_session_id", "superseded_by_logical_session_id"):
        if document.get(field) == document["logical_session_id"]:
            errors.append(_error("LLM_RUNTIME_SESSION_INVALID", f"/{field}", "session cannot supersede itself"))
    if document.get("supersedes_logical_session_id") == document.get("superseded_by_logical_session_id") and document.get("supersedes_logical_session_id") is not None:
        errors.append(_error("LLM_RUNTIME_SESSION_INVALID", "/superseded_by_logical_session_id", "session links must be distinct"))
    return errors


def _worker_errors(document: Mapping[str, JsonValue]) -> list[ValidationError]:
    policy = document["model_policy"]
    if policy["default_model_id"] not in policy["allowed_model_ids"]:
        return [_error("LLM_RUNTIME_WORKER_INVALID", "/model_policy/default_model_id", "default model must be allowed")]
    return []


def _context_errors(document: Mapping[str, JsonValue], registry: Mapping[str, JsonValue]) -> list[ValidationError]:
    sources = document["sources"]
    errors: list[ValidationError] = []
    identities: list[tuple[JsonValue, ...]] = []
    orders: list[JsonValue] = []
    for index, source in enumerate(sources):
        identities.append(tuple(source[field] for field in ("source_kind", "source_id", "revision", "content_sha256")))
        orders.append(source["include_order"])
        if source["tenant_id"] != document["tenant_id"] or source["project_id"] != document["project_id"]:
            errors.append(_error("LLM_RUNTIME_CONTEXT_INVALID", f"/sources/{index}", "source tenant and project must match package"))
    if len(identities) != len(set(identities)):
        errors.append(_error("LLM_RUNTIME_CONTEXT_INVALID", "/sources", "source identity must be unique"))
    if sorted(orders) != list(range(1, len(orders) + 1)):
        errors.append(_error("LLM_RUNTIME_CONTEXT_INVALID", "/sources", "include order must be unique and contiguous"))
    project = document["project_context"]
    matches = [(index, source) for index, source in enumerate(sources) if source["source_id"] == project["source_id"]]
    if len(matches) != 1 or any(matches[0][1][field] != project[field] for field in ("revision", "logical_ref", "content_sha256")):
        errors.append(_error("LLM_RUNTIME_CONTEXT_INVALID", "/project_context", "project context must match one source"))
    elif matches[0][1]["source_kind"] != project["binding_mode"]:
        errors.append(_error("LLM_RUNTIME_CONTEXT_INVALID", "/project_context/source_id", "project context source kind must match binding mode"))
    else:
        selected_index, selected_source = matches[0]
        match project["binding_mode"]:
            case "project_intake":
                if selected_source["trust_level"] != "trusted":
                    errors.append(_error("LLM_RUNTIME_CONTEXT_INVALID", f"/sources/{selected_index}/trust_level", "selected project intake source must be trusted"))
            case "project_v2":
                if selected_source["source_status"] != "released":
                    errors.append(_error("LLM_RUNTIME_CONTEXT_INVALID", f"/sources/{selected_index}/source_status", "selected project V2 source must be released"))
    expected = _registry_entry(registry, document["step_id"])
    if expected is None or document["prompt"] != _prompt_binding(expected):
        errors.append(_error("LLM_RUNTIME_CONTEXT_INVALID", "/prompt", "prompt must match the active registry entry"))
    if expected is None or document["output_contracts"] != expected["output_contracts"]:
        errors.append(_error("LLM_RUNTIME_CONTEXT_INVALID", "/output_contracts", "output contracts must match registry order"))
    if document["trigger"] == "revision":
        revision = document["revision_context"]
        rejected = next(source for source in sources if source["source_kind"] == "rejected_artifact")
        request = next(source for source in sources if source["source_kind"] == "revision_request")
        if document["target_revision"] <= rejected["revision"] or revision["expected_new_revision"] != document["target_revision"] or revision["rejected_artifact_revision"] != rejected["revision"] or revision["revision_request_id"] != request["source_id"]:
            errors.append(_error("LLM_RUNTIME_CONTEXT_INVALID", "/revision_context", "revision context must agree with local sources"))
    return errors


def _registry_entry(registry: Mapping[str, JsonValue], step_id: JsonValue) -> Mapping[str, JsonValue] | None:
    entries = registry["entries"]
    matches = [entry for entry in entries if entry["step_id"] == step_id and entry["active"]]
    return matches[0] if len(matches) == 1 else None


def _prompt_binding(entry: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
    return {field: entry[field] for field in ("prompt_id", "prompt_version", "prompt_path", "prompt_sha256")}


def _request_errors(document: Mapping[str, JsonValue]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    if document["input_sha256"] != document["context_package_sha256"]:
        errors.append(_error("LLM_RUNTIME_REQUEST_INVALID", "/input_sha256", "input hash must equal context package hash"))
    hint = document.get("technical_session_cache_hint")
    if hint is not None and hint["provider_id"] != document["provider_id"]:
        errors.append(_error("LLM_RUNTIME_REQUEST_INVALID", "/technical_session_cache_hint/provider_id", "cache provider must match request provider"))
    return errors


def _result_errors(document: Mapping[str, JsonValue]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    tokens = document["token_usage"]
    if tokens["total_tokens"] != tokens["input_tokens"] + tokens["output_tokens"]:
        errors.append(_error("LLM_RUNTIME_RESULT_INVALID", "/token_usage/total_tokens", "total tokens must equal input plus output"))
    if tokens.get("cached_input_tokens", 0) > tokens["input_tokens"]:
        errors.append(_error("LLM_RUNTIME_RESULT_INVALID", "/token_usage/cached_input_tokens", "cached input cannot exceed input tokens"))
    if document["status"] == "succeeded" and document["output"]["revision"] != document["target_revision"]:
        errors.append(_error("LLM_RUNTIME_RESULT_INVALID", "/output/revision", "output revision must equal target revision"))
    if _timestamp(document["started_at"]) > _timestamp(document["finished_at"]):
        errors.append(_error("LLM_RUNTIME_RESULT_INVALID", "/finished_at", "finished time must not precede start time"))
    return errors


def _timestamp(value: JsonValue) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
