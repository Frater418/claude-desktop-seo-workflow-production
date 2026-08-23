from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from jsonschema import Draft202012Validator, FormatChecker
from pydantic import JsonValue

from services.canonical_json import canonical_json_bytes
from services.domain_contract.validator import validate_project
from services.quality_gate_registry.evaluator import resolve_required_gates
from services.step1_preflight import validate_step1_preflight
from services.step1_preflight.render import render_topic_inventory
from services.step1b_preflight import render_architecture_html, render_architecture_markdown, validate_step1b_preflight
from services.step1c_preflight import validate_step1c_preflight
from services.step1c_preflight.render import render_step1c
from services.step2_preflight import validate_step2_preflight
from services.step2_preflight.render import render_step2
from services.step3_preflight import validate_step3_preflight
from services.step3_preflight.render import render_step3
from services.step4a_preflight import validate_step4a_preflight
from services.step4a_preflight.render import render_step4a
from services.step4b_preflight import validate_step4b_preflight
from services.step4b_preflight.render import render_step4b

from .artifact_revision_types import ArtifactRecord, build_artifact_record
from .gate_context import GateContext
from .provider_outputs import ProviderOutputSet
from .step0_binding import Step0CrossBindingError, validate_step0_cross_binding


INITIAL_ROUTE_STEPS = frozenset(("0", "1", "1b", "1c", "2", "3", "4a", "4b"))


class StepValidationError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class StepValidationResult:
    artifact_records: tuple[ArtifactRecord, ...]
    quality_gate_runs: tuple[dict[str, JsonValue], ...]
    derived_views: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class StepValidationService:
    root: Path
    prompt_registry: Mapping[str, JsonValue]
    quality_gate_registry: Mapping[str, JsonValue]

    @classmethod
    def from_root(cls, root: Path) -> StepValidationService:
        return cls(
            root=root,
            prompt_registry=_load_json(root / "standards/runtime/official-prompt-registry.json"),
            quality_gate_registry=_load_json(root / "standards/quality/quality-gate-registry.json"),
        )

    def validate(
        self,
        output_set: ProviderOutputSet,
        package_input_hash: str,
        bundle: Mapping[str, JsonValue],
        gate_context: GateContext,
    ) -> StepValidationResult:
        output = output_set.primary
        if output.step_id not in INITIAL_ROUTE_STEPS:
            raise StepValidationError("ERROR_INITIAL_ROUTE_STEP_INVALID", "Step 3b is not an initial-route step.")
        documents = self._validate_output_contracts(output_set)
        specialized_bundle = _bind_provider_documents(output.step_id, bundle, documents)
        specialized_bundle["execution_identity"] = {
            "project_id": output.project_id,
            "run_id": output.run_id,
            "step_id": output.step_id,
            "target_revision": output.target_revision,
        }
        if output.step_id == "0":
            try:
                validate_step0_cross_binding(output, documents[0], specialized_bundle)
            except Step0CrossBindingError as exc:
                raise StepValidationError("ERROR_STEP0_CROSS_BINDING_INVALID", str(exc)) from exc
        self._validate_specialized(output.step_id, specialized_bundle)
        parents = _canonical_parents(output.step_id, specialized_bundle)
        records = tuple(build_artifact_record(item, package_input_hash, parents) for item in output_set.outputs)
        views = _render(output.step_id, specialized_bundle)
        qgrs = self._machine_qgrs(output.step_id, records[0], gate_context)
        qgr_schema = _load_json(self.root / "standards/runtime/quality-gate-run.schema.json")
        if any(list(Draft202012Validator(qgr_schema, format_checker=FormatChecker()).iter_errors(qgr)) for qgr in qgrs):
            raise StepValidationError("ERROR_QUALITY_GATE_RUN_SCHEMA_INVALID", "Generated machine quality-gate run violates its runtime contract.")
        return StepValidationResult(records, qgrs, views)

    def _validate_output_contracts(self, output_set: ProviderOutputSet) -> tuple[dict[str, JsonValue], ...]:
        entry = _entry_for_step(self.prompt_registry, output_set.primary.step_id)
        contracts = entry["output_contracts"]
        if not isinstance(contracts, list) or len(contracts) != len(output_set.outputs):
            raise StepValidationError("ERROR_OUTPUT_CONTRACT_INVALID", "Provider output contracts do not match the official registry.")
        documents: list[dict[str, JsonValue]] = []
        for output, contract in zip(output_set.outputs, contracts, strict=True):
            if not isinstance(contract, dict) or output.contract_id != contract.get("contract_id"):
                raise StepValidationError("ERROR_OUTPUT_CONTRACT_INVALID", "Provider output contract identity is invalid.")
            path = contract.get("contract_path")
            if not isinstance(path, str):
                raise StepValidationError("ERROR_OUTPUT_CONTRACT_INVALID", "Official output contract path is missing.")
            try:
                candidate = json.loads(output.content_bytes)
            except json.JSONDecodeError as exc:
                raise StepValidationError("ERROR_OUTPUT_SCHEMA_INVALID", "Provider output must be JSON for its registered contract.") from exc
            schema = _load_json(self.root / path)
            if list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(candidate)):
                raise StepValidationError("ERROR_OUTPUT_SCHEMA_INVALID", "Provider output does not satisfy its registered schema.")
            if not isinstance(candidate, dict):
                raise StepValidationError("ERROR_OUTPUT_SCHEMA_INVALID", "Provider output must contain an object document.")
            if output.step_id == "2" and output.content_bytes != canonical_json_bytes(candidate):
                raise StepValidationError("ERROR_OUTPUT_CONTRACT_INVALID", "Step 2 provider output must use canonical UTF-8 JSON bytes.")
            documents.append(candidate)
        return tuple(documents)

    def _validate_specialized(self, step_id: str, bundle: Mapping[str, JsonValue]) -> None:
        result = _validator(step_id, bundle, self.root)
        if not bool(result.get("valid")):
            raise StepValidationError("ERROR_STEP_PREFLIGHT_INVALID", json.dumps(result.get("errors", []), ensure_ascii=True, sort_keys=True))

    def _machine_qgrs(
        self,
        step_id: str,
        artifact: ArtifactRecord,
        gate_context: Mapping[str, JsonValue],
    ) -> tuple[dict[str, JsonValue], ...]:
        context = gate_context.model_dump(mode="json")
        resolution = resolve_required_gates(dict(self.quality_gate_registry), step_id, "submit_for_gate", context)
        if not resolution["valid"]:
            raise StepValidationError("ERROR_GATE_APPLICABILITY_INVALID", json.dumps(resolution["errors"], ensure_ascii=True, sort_keys=True))
        registry_gates = {gate["gate_id"]: gate for gate in self.quality_gate_registry["gates"] if isinstance(gate, dict) and isinstance(gate.get("gate_id"), str)}
        for gate_id, evidence in gate_context.evidence_by_gate.items():
            gate = registry_gates.get(gate_id)
            allowed_evidence = (set(gate["evidence_required"]) if gate is not None else set()) | ({"raw_evidence_artifact_sha256"} if gate is not None and gate.get("binding_scope") == "external_evidence" else set())
            if gate is None or set(evidence) != allowed_evidence:
                raise StepValidationError("ERROR_QUALITY_GATE_EVIDENCE_INVALID", "Gate evidence must contain exactly the registered evidence fields.")
        records: list[dict[str, JsonValue]] = []
        for gate in resolution["required_gates"]:
            if gate["stage"] == "human_approval":
                continue
            evidence = gate_context.evidence_by_gate.get(gate["gate_id"])
            allowed_evidence = set(gate["evidence_required"]) | ({"raw_evidence_artifact_sha256"} if gate.get("binding_scope") == "external_evidence" else set())
            if evidence is None or set(evidence) != allowed_evidence:
                raise StepValidationError("ERROR_QUALITY_GATE_EVIDENCE_INVALID", "Required gate evidence is missing or unknown.")
            records.append({
                "quality_gate_run_id": f"qgr-{step_id.replace('b', 'b').replace('a', 'a')}-{gate['gate_id'][3:]}-{artifact.content_sha256[:8]}",
                "quality_gate_id": gate["gate_id"], "human_gate_id": _human_gate(step_id),
                "tenant_id": artifact.tenant_id, "run_id": artifact.run_id, "step_id": step_id,
                "artifact_id": artifact.artifact_id, "artifact_sha256": artifact.content_sha256, "artifact_revision": artifact.revision,
                "registry_version": self.quality_gate_registry["schema_version"], "policy_version": "1.0.0",
                "result": "passed", "evidence": evidence, "findings": [],
                "checked_at": artifact.created_at, "checker_version": "step-validation-service-1.0.0",
            })
        return tuple(records)


def _load_json(path: Path) -> dict[str, JsonValue]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise StepValidationError("ERROR_REGISTRY_INVALID", f"Expected an object in {path}.")
    return payload


def _entry_for_step(registry: Mapping[str, JsonValue], step_id: str) -> dict[str, JsonValue]:
    entries = registry.get("entries")
    selected = [entry for entry in entries if isinstance(entries, list) and isinstance(entry, dict) and entry.get("step_id") == step_id and entry.get("active") is True]
    if len(selected) != 1:
        raise StepValidationError("ERROR_REGISTRY_INVALID", "Expected one active prompt registry entry.")
    return selected[0]


def _validator(step_id: str, bundle: Mapping[str, JsonValue], root: Path) -> Mapping[str, JsonValue]:
    match step_id:
        case "0": return validate_project(dict(bundle["project"]), root=root)
        case "1": return validate_step1_preflight(dict(bundle), root=root)
        case "1b": return validate_step1b_preflight(dict(bundle))
        case "1c": return validate_step1c_preflight(dict(bundle))
        case "2": return validate_step2_preflight(dict(bundle))
        case "3": return validate_step3_preflight(dict(bundle))
        case "4a": return validate_step4a_preflight(dict(bundle), root=root)
        case "4b": return validate_step4b_preflight(dict(bundle), root=root)
        case _: raise StepValidationError("ERROR_INITIAL_ROUTE_STEP_INVALID", "Step is not in the initial route.")


def _bind_provider_documents(step_id: str, bundle: Mapping[str, JsonValue], documents: tuple[dict[str, JsonValue], ...]) -> dict[str, JsonValue]:
    keys = {
        "1": ("inventory",),
        "1b": ("candidate",),
        "2": ("candidate",),
        "3": ("candidate",),
        "4a": ("briefing", "claim_ledger"),
        "4b": ("page_spec", "staging_evidence"),
    }.get(step_id, ())
    if step_id == "1c":
        if len(documents) < 2:
            raise StepValidationError("ERROR_OUTPUT_CONTRACT_INVALID", "Provider documents do not match specialized candidate fields.")
        bound = dict(bundle)
        _bind_document(bound, "design", documents[0])
        templates = list(documents[1:])
        candidate = bound.get("templates")
        if candidate is not None and candidate != templates:
            raise StepValidationError("ERROR_OUTPUT_CONTRACT_INVALID", "Specialized candidate must match the exact provider document.")
        bound["templates"] = templates
        return bound
    if not keys:
        return dict(bundle)
    if len(keys) != len(documents):
        raise StepValidationError("ERROR_OUTPUT_CONTRACT_INVALID", "Provider documents do not match specialized candidate fields.")
    bound = dict(bundle)
    for key, document in zip(keys, documents, strict=True):
        _bind_document(bound, key, document)
    return bound


def _bind_document(bound: dict[str, JsonValue], key: str, document: dict[str, JsonValue]) -> None:
    candidate = bound.get(key)
    if candidate is not None and candidate != document:
        raise StepValidationError("ERROR_OUTPUT_CONTRACT_INVALID", "Specialized candidate must match the exact provider document.")
    bound[key] = document


def _render(step_id: str, bundle: Mapping[str, JsonValue]) -> Mapping[str, str]:
    match step_id:
        case "0": return {}
        case "1": return {"topic-inventory.md": render_topic_inventory(dict(bundle["inventory"]))}
        case "1b": return {"architecture.md": render_architecture_markdown(dict(bundle["candidate"])), "architecture.html": render_architecture_html(dict(bundle["candidate"]))}
        case "1c": return {name.replace("/", "."): content for name, content in render_step1c(dict(bundle)).items()}
        case "2": return {"keyword-evidence.csv": render_step2(dict(bundle))}
        case "3": return {"plan.md": render_step3(dict(bundle))}
        case "4a": return {"briefing.md": render_step4a(dict(bundle))}
        case "4b": return {"landingpage.html": render_step4b(dict(bundle))}
        case _: raise StepValidationError("ERROR_INITIAL_ROUTE_STEP_INVALID", "Step is not in the initial route.")


def _human_gate(step_id: str) -> str:
    return f"GATE-{step_id.upper()}"


def _canonical_parents(step_id: str, bundle: Mapping[str, JsonValue]) -> tuple[str, ...]:
    if step_id == "0":
        return ()
    artifact = bundle.get("source_artifact") if step_id == "1" else bundle.get("predecessor_artifact")
    if not isinstance(artifact, dict) or not isinstance(artifact.get("artifact_id"), str):
        raise StepValidationError("ERROR_CONTEXT_SOURCE_INVALID", "Initial-route step requires a canonical predecessor artifact.")
    return (artifact["artifact_id"],)
