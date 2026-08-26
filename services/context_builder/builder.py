from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TypeAlias

from services.runtime_contracts.llm_records import RuntimeContractValidator


JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | Mapping[str, "JsonValue"] | Sequence["JsonValue"]
SourceDescriptor: TypeAlias = Mapping[str, JsonValue]
SOURCE_RANKS = {
    "official_prompt": 1,
    "output_contract": 2,
    "project_intake": 3,
    "project_v2": 3,
    "released_predecessor": 4,
    "released_supporting_artifact": 4,

    "rejected_artifact": 5,
    "revision_request": 6,
    "operator_instruction": 6,
    "decision": 7,
    "quality_gate_run": 7,
    "blocker": 7,
    "resolution": 7,
    "evidence": 8,
}
TRUST_RANKS = {"trusted": 0, "operator_asserted": 1, "untrusted": 2, "not_applicable": 3}
RFC3339_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")


@dataclass(frozen=True, slots=True)
class ContextBuildError(Exception):
    code: str
    path: str
    message: str
    remediation: str

    def __str__(self) -> str:
        return f"{self.code}:{self.path}:{self.message}"


def canonical_json_bytes(value: JsonValue) -> bytes:
    _assert_json(value, "/")
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(value: JsonValue) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def build_context_package(
    specification: Mapping[str, JsonValue],
    source_descriptors: Sequence[SourceDescriptor],
    source_bytes: Mapping[str, bytes],
    prompt_registry: Mapping[str, JsonValue],
    runtime_validator: RuntimeContractValidator,
) -> dict[str, JsonValue]:
    trigger = _text(specification, "trigger")
    if trigger in {"retry", "resume"}:
        raise ContextBuildError("ERROR_CONTEXT_SOURCE_INVALID", "/trigger", "retry and resume reuse an existing package", "Revalidate the stored package instead of constructing a new one.")
    supplied_sources = [_source(source, source_bytes, index) for index, source in enumerate(source_descriptors)]
    entry = _active_entry(prompt_registry, _text(specification, "step_id"))
    sources = [*_registry_sources(entry, source_bytes, specification), *supplied_sources]
    ordered = sorted(sources, key=_source_key)
    numbered = [{**source, "include_order": index} for index, source in enumerate(ordered, start=1)]
    project = next((source for source in numbered if source["source_kind"] in {"project_intake", "project_v2"}), None)
    if project is None:
        raise ContextBuildError("ERROR_CONTEXT_SOURCE_INVALID", "/sources", "project context source is required", "Provide intake for Step 0 or released Project V2 afterwards.")
    package: dict[str, JsonValue] = {
        "context_package_id": _text(specification, "context_package_id"), "schema_version": "1.0.0",
        "tenant_id": _text(specification, "tenant_id"), "project_id": _text(specification, "project_id"), "run_id": _text(specification, "run_id"),
        "step_id": _text(specification, "step_id"), "logical_session_id": _text(specification, "logical_session_id"),
        "logical_session_revision": specification["logical_session_revision"], "trigger": trigger, "target_revision": specification["target_revision"],
        "prompt": {name: entry[name] for name in ("prompt_id", "prompt_version", "prompt_path", "prompt_sha256")},
        "project_context": {"binding_mode": project["source_kind"], "source_id": project["source_id"], "revision": project["revision"], "logical_ref": project["logical_ref"], "content_sha256": project["content_sha256"]},
        "worker_profile_ref": specification["worker_profile_ref"], "output_contracts": entry["output_contracts"], "sources": numbered,
        "source_manifest_sha256": sha256(numbered), "builder_provenance": {"builder_version": "1.0.0", "created_at": _text(specification, "created_at"), "created_by": _text(specification, "created_by")},
    }
    if trigger == "revision":
        package["revision_context"] = specification["revision_context"]
    package["package_sha256"] = sha256(package)
    result = runtime_validator.validate("context-package", package)
    if not result.valid:
        first = result.errors[0]
        raise ContextBuildError("ERROR_CONTEXT_SCHEMA_INVALID", first.path, first.message, "Correct the package input contract.")
    return json.loads(canonical_json_bytes(package))


def _active_entry(registry: Mapping[str, JsonValue], step_id: str) -> Mapping[str, JsonValue]:
    entries = registry.get("entries")
    if not isinstance(entries, Sequence):
        raise ContextBuildError("ERROR_CONTEXT_PROMPT_BINDING_INVALID", "/entries", "prompt registry entries are required", "Inject the approved active prompt registry.")
    matches = [entry for entry in entries if isinstance(entry, Mapping) and entry.get("step_id") == step_id and entry.get("active") is True]
    if len(matches) != 1:
        raise ContextBuildError("ERROR_CONTEXT_PROMPT_BINDING_INVALID", "/step_id", "exactly one active prompt entry is required", "Repair the prompt registry selection.")
    return matches[0]


def _registry_sources(entry: Mapping[str, JsonValue], source_bytes: Mapping[str, bytes], specification: Mapping[str, JsonValue]) -> list[dict[str, JsonValue]]:
    sources = [_registry_source("official_prompt", f"prompt:{entry['step_id']}", f"prompt-{entry['step_id']}", entry, source_bytes, "prompt_sha256", specification)]
    contracts = entry["output_contracts"]
    if not isinstance(contracts, Sequence):
        raise ContextBuildError("ERROR_CONTEXT_OUTPUT_CONTRACT_INVALID", "/output_contracts", "registry output contracts are required", "Inject ordered output contracts.")
    for index, contract in enumerate(contracts, start=1):
        if not isinstance(contract, Mapping):
            raise ContextBuildError("ERROR_CONTEXT_OUTPUT_CONTRACT_INVALID", "/output_contracts", "registry output contract is invalid", "Inject a valid output contract binding.")
        sources.append(_registry_source("output_contract", f"output-contract:{entry['step_id']}/{index}", f"output-contract-{entry['step_id']}-{index}", contract, source_bytes, "contract_sha256", specification))
    return sources


def _registry_source(kind: str, ref: str, identifier: str, binding: Mapping[str, JsonValue], source_bytes: Mapping[str, bytes], hash_key: str, specification: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    content = source_bytes.get(ref)
    if content is None or hashlib.sha256(content).hexdigest() != binding.get(hash_key):
        raise ContextBuildError("ERROR_CONTEXT_PROMPT_BINDING_INVALID" if kind == "official_prompt" else "ERROR_CONTEXT_OUTPUT_CONTRACT_INVALID", f"/sources/{ref}", "registered source bytes do not match the approved hash", "Supply the exact approved source bytes.")
    return {"source_kind": kind, "source_id": identifier, "tenant_id": _text(specification, "tenant_id"), "project_id": _text(specification, "project_id"), "revision": 1, "logical_ref": ref, "content_sha256": digest_bytes(content), "source_status": "active", "trust_level": "not_applicable"}


def _source(descriptor: SourceDescriptor, source_bytes: Mapping[str, bytes], index: int) -> dict[str, JsonValue]:
    if "include_order" in descriptor or "content_sha256" in descriptor:
        raise ContextBuildError("ERROR_CONTEXT_SOURCE_INVALID", "/sources", "caller cannot provide derived source order or hash", "Remove derived fields from source descriptors.")
    ref = _text(descriptor, "logical_ref")
    content = source_bytes.get(ref)
    if content is None:
        raise ContextBuildError("ERROR_CONTEXT_SOURCE_INVALID", f"/sources/{ref}", "source bytes are missing", "Supply exact bytes for every controlled logical reference.")
    return {**descriptor, "revision": _revision(descriptor.get("revision"), f"/sources/{index}/revision"), "content_sha256": digest_bytes(content)}


def _source_key(source: Mapping[str, JsonValue]) -> tuple[int, int, str, str, int, str]:
    kind = _text(source, "source_kind")
    return (SOURCE_RANKS.get(kind, 9), TRUST_RANKS.get(_text(source, "trust_level"), 4), kind, _text(source, "logical_ref"), _revision(source.get("revision"), "/sources/revision"), _text(source, "content_sha256"))


def _text(mapping: Mapping[str, JsonValue], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str):
        raise ContextBuildError("ERROR_CONTEXT_SCHEMA_INVALID", f"/{key}", "required text field is invalid", "Supply a valid package specification.")
    return value


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_rfc3339_utc(value: JsonValue, path: str) -> datetime:
    if not isinstance(value, str) or RFC3339_TIMESTAMP.fullmatch(value) is None:
        raise ContextBuildError("ERROR_CONTEXT_SCHEMA_INVALID", path, "RFC3339 timestamp with timezone is required", "Supply a timezone-aware RFC3339 timestamp.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ContextBuildError("ERROR_CONTEXT_SCHEMA_INVALID", path, "RFC3339 timestamp is invalid", "Supply a valid timezone-aware RFC3339 timestamp.") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContextBuildError("ERROR_CONTEXT_SCHEMA_INVALID", path, "RFC3339 timestamp timezone is required", "Supply a timezone-aware RFC3339 timestamp.")
    return parsed.astimezone(timezone.utc)


def _revision(value: JsonValue | None, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ContextBuildError("ERROR_CONTEXT_SCHEMA_INVALID", path, "source revision must be an integer greater than zero", "Supply an integer source revision of at least one.")
    return value


def _assert_json(value: JsonValue, path: str) -> None:
    if isinstance(value, (bytes, bytearray, memoryview, set)):
        raise ContextBuildError("ERROR_CONTEXT_SCHEMA_INVALID", path, "unsupported non-JSON value", "Use JSON-compatible values only.")
    if isinstance(value, float) and not math.isfinite(value):
        raise ContextBuildError("ERROR_CONTEXT_SCHEMA_INVALID", path, "non-finite JSON numbers are forbidden", "Use finite JSON values.")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContextBuildError("ERROR_CONTEXT_SCHEMA_INVALID", path, "JSON object keys must be strings", "Use string JSON keys.")
            _assert_json(item, f"{path}{key}/")
    elif isinstance(value, Sequence) and not isinstance(value, str):
        for index, item in enumerate(value):
            _assert_json(item, f"{path}{index}/")
    elif not isinstance(value, (str, int, float, bool, type(None))):
        raise ContextBuildError("ERROR_CONTEXT_SCHEMA_INVALID", path, "unsupported non-JSON value", "Use JSON-compatible values only.")
