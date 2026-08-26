from __future__ import annotations

import hashlib
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
from services.transition_service import process_transition

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
    supporting_artifacts: tuple[tuple[ArtifactRecord, bytes], ...]
    quality_gate_runs: tuple[dict[str, JsonValue], ...]
    derived_views: Mapping[str, str]
    next_run: dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class StepValidationService:
    root: Path
    prompt_registry: Mapping[str, JsonValue]
    quality_gate_registry: Mapping[str, JsonValue]
    workflow_graph: Mapping[str, JsonValue]

    @classmethod
    def from_root(cls, root: Path) -> StepValidationService:
        return cls(
            root=root,
            prompt_registry=_load_json(root / "standards/runtime/official-prompt-registry.json"),
            quality_gate_registry=_load_json(root / "standards/quality/quality-gate-registry.json"),
            workflow_graph=_load_json(root / "standards/workflow/workflow-graph.json"),
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
        documents = self.validate_output_contracts(output_set)
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
        if output.step_id != "1":
            self._validate_specialized(output.step_id, specialized_bundle)
        parents = _canonical_parents(output.step_id, specialized_bundle)
        records = tuple(build_artifact_record(item, package_input_hash, parents) for item in output_set.outputs)
        supporting = _supporting_artifacts(output.step_id, specialized_bundle)
        gate_artifacts = (
            {"qg-step1-crawl-snapshot": supporting[0][0]}
            if output.step_id == "1" and supporting
            else {}
        )
        qgrs = self._machine_qgrs(output.step_id, records[0], gate_context, gate_artifacts)
        if output.step_id == "1":
            _bind_step1_runtime_projection(specialized_bundle, output, records, qgrs)
            self._validate_specialized(output.step_id, specialized_bundle)
        views = _render(output.step_id, specialized_bundle)
        next_run = self._next_run(output_set, specialized_bundle, records, supporting, qgrs, gate_context)
        qgr_schema = _load_json(self.root / "standards/runtime/quality-gate-run.schema.json")
        if any(list(Draft202012Validator(qgr_schema, format_checker=FormatChecker()).iter_errors(qgr)) for qgr in qgrs):
            raise StepValidationError("ERROR_QUALITY_GATE_RUN_SCHEMA_INVALID", "Generated machine quality-gate run violates its runtime contract.")
        return StepValidationResult(records, supporting, qgrs, views, next_run)

    def validate_output_contracts(self, output_set: ProviderOutputSet) -> tuple[dict[str, JsonValue], ...]:
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

    def _next_run(
        self,
        output_set: ProviderOutputSet,
        bundle: Mapping[str, JsonValue],
        records: tuple[ArtifactRecord, ...],
        supporting: tuple[tuple[ArtifactRecord, bytes], ...],
        qgrs: tuple[dict[str, JsonValue], ...],
        gate_context: GateContext,
    ) -> dict[str, JsonValue]:
        output = output_set.primary
        current_run = bundle.get("current_run")
        if not isinstance(current_run, dict):
            raise StepValidationError(
                "ERROR_PRODUCTION_STATE_INVALID",
                "A canonical in-progress Core run is required for submission.",
            )
        predecessor = bundle.get("predecessor_release") if output.step_id != "0" else None
        if output.step_id != "0" and not isinstance(predecessor, dict):
            raise StepValidationError(
                "ERROR_CONTEXT_PREDECESSOR_INVALID",
                "A released predecessor is required for initial-route submission.",
            )
        from_step = "0" if output.step_id == "0" else str(predecessor["step_id"])
        command = {
            "command_id": f"command-submit-{output.content_sha256[:24]}",
            "tenant_id": output.tenant_id,
            "project_id": output.project_id,
            "run_id": output.run_id,
            "expected_revision": current_run["revision"],
            "idempotency_key": f"idem-submit-{output.content_sha256[:24]}",
            "operation": "submit_for_gate",
            "from_step_id": from_step,
            "to_step_id": output.step_id,
            "input_hash": current_run["input_hash"],
            "output_hash": records[0].content_sha256,
            "requested_at": records[0].created_at,
            "artifacts": [
                {
                    "artifact_id": record.artifact_id,
                    "revision": record.revision,
                    "content_sha256": record.content_sha256,
                }
                for record in records
            ],
            "quality_gates": [
                {
                    "quality_gate_run_id": qgr["quality_gate_run_id"],
                    "result": qgr["result"],
                    "artifact_id": qgr["artifact_id"],
                    "artifact_sha256": qgr["artifact_sha256"],
                }
                for qgr in qgrs
            ],
        }
        result = process_transition(
            command=command,
            run=current_run,
            current_artifact=records[0].model_dump(mode="json"),
            supporting_artifacts=[record.model_dump(mode="json") for record, _ in supporting],
            quality_gate_runs=list(qgrs),
            approval=None,
            predecessor_release=predecessor if isinstance(predecessor, dict) else None,
            context=gate_context.model_dump(mode="json"),
            registry=dict(self.quality_gate_registry),
            graph=dict(self.workflow_graph),
        )
        if not result["ok"]:
            first = result["errors"][0]
            raise StepValidationError(str(first["code"]), str(first["message"]))
        next_run = result["run"]
        if (
            not isinstance(next_run, dict)
            or next_run.get("status") != "awaiting_gate"
            or next_run.get("revision") != output.target_revision
        ):
            raise StepValidationError(
                "ERROR_PRODUCTION_STATE_INVALID",
                "Transition Service returned an invalid awaiting-gate run projection.",
            )
        return next_run

    def _validate_specialized(self, step_id: str, bundle: Mapping[str, JsonValue]) -> None:
        result = _validator(step_id, bundle, self.root)
        if not bool(result.get("valid")):
            raise StepValidationError("ERROR_STEP_PREFLIGHT_INVALID", json.dumps(result.get("errors", []), ensure_ascii=True, sort_keys=True))

    def _machine_qgrs(
        self,
        step_id: str,
        artifact: ArtifactRecord,
        gate_context: Mapping[str, JsonValue],
        artifact_overrides: Mapping[str, ArtifactRecord],
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
            gate_artifact = artifact_overrides.get(gate["gate_id"], artifact)
            records.append({
                "quality_gate_run_id": f"qgr-{step_id.replace('b', 'b').replace('a', 'a')}-{gate['gate_id'][3:]}-{gate_artifact.content_sha256[:8]}",
                "quality_gate_id": gate["gate_id"], "human_gate_id": _human_gate(step_id),
                "tenant_id": gate_artifact.tenant_id, "run_id": gate_artifact.run_id, "step_id": step_id,
                "artifact_id": gate_artifact.artifact_id, "artifact_sha256": gate_artifact.content_sha256, "artifact_revision": gate_artifact.revision,
                "registry_version": self.quality_gate_registry["schema_version"], "policy_version": "1.0.0",
                "result": "passed", "evidence": evidence, "findings": [],
                "checked_at": gate_artifact.created_at, "checker_version": "step-validation-service-1.0.0",
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


def _supporting_artifacts(
    step_id: str,
    bundle: Mapping[str, JsonValue],
) -> tuple[tuple[ArtifactRecord, bytes], ...]:
    if step_id != "1":
        return ()
    artifact_values = bundle.get("crawl_artifacts")
    evidence_values = bundle.get("agent_evidence_records")
    if not isinstance(artifact_values, list) or not isinstance(evidence_values, list):
        raise StepValidationError(
            "ERROR_CRAWL_EVIDENCE_MISSING",
            "Step 1 requires crawl supporting artifact and immutable Agent Evidence records.",
        )
    supporting: list[tuple[ArtifactRecord, bytes]] = []
    for value in artifact_values:
        if not isinstance(value, dict):
            raise StepValidationError("ERROR_CRAWL_EVIDENCE_INVALID", "Crawl supporting artifact is invalid.")
        artifact = ArtifactRecord.model_validate(value)
        matches = [
            evidence
            for evidence in evidence_values
            if isinstance(evidence, dict)
            and evidence.get("content_sha256") == artifact.content_sha256
            and isinstance(evidence.get("result"), dict)
        ]
        if len(matches) != 1:
            raise StepValidationError(
                "ERROR_CRAWL_EVIDENCE_INVALID",
                "Crawl supporting artifact must bind exactly one Agent Evidence result.",
            )
        content = (
            json.dumps(matches[0]["result"], ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        if hashlib.sha256(content).hexdigest() != artifact.content_sha256:
            raise StepValidationError(
                "ERROR_CRAWL_EVIDENCE_HASH_MISMATCH",
                "Crawl supporting artifact bytes do not match the immutable Evidence hash.",
            )
        supporting.append((artifact, content))
    return tuple(supporting)


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
    prior = bundle.get("prior_revision_artifacts")
    prior_artifacts = prior if isinstance(prior, list) else []
    prior_ids = tuple(
        str(artifact["artifact_id"])
        for artifact in prior_artifacts
        if isinstance(artifact, dict)
        and isinstance(artifact.get("artifact_id"), str)
    )
    if step_id == "0":
        return prior_ids
    artifact = bundle.get("source_artifact") if step_id == "1" else bundle.get("predecessor_artifact")
    if not isinstance(artifact, dict) or not isinstance(artifact.get("artifact_id"), str):
        raise StepValidationError("ERROR_CONTEXT_SOURCE_INVALID", "Initial-route step requires a canonical predecessor artifact.")
    return tuple(dict.fromkeys((*prior_ids, artifact["artifact_id"])))


def _bind_step1_runtime_projection(
    bundle: dict[str, JsonValue],
    output: object,
    records: tuple[ArtifactRecord, ...],
    qgrs: tuple[dict[str, JsonValue], ...],
) -> None:
    run = bundle.get("run")
    if not isinstance(run, dict):
        raise StepValidationError(
            "ERROR_CONTEXT_SOURCE_INVALID",
            "Step 1 requires a projected awaiting-gate run record.",
        )
    primary = records[0]
    predecessor = bundle.get("predecessor_release")
    if not isinstance(predecessor, dict):
        raise StepValidationError(
            "ERROR_CONTEXT_SOURCE_INVALID",
            "Step 1 requires the released Gate 0 predecessor projection.",
        )
    artifact_records = [record.model_dump(mode="json") for record in records]
    gate_records = [dict(record) for record in qgrs]
    predecessor_gates = bundle.get("quality_gates")
    if not isinstance(predecessor_gates, list):
        raise StepValidationError(
            "ERROR_CONTEXT_SOURCE_INVALID",
            "Step 1 requires the released Gate 0 quality-gate record.",
        )
    domain_gate = next(
        (record for record in gate_records if record.get("quality_gate_id") == "qg-domain-contract"),
        None,
    )
    if not isinstance(domain_gate, dict):
        raise StepValidationError(
            "ERROR_QUALITY_GATE_BINDING_INVALID",
            "Step 1 requires a current domain-contract quality gate.",
        )
    bundle["artifact"] = artifact_records[0]
    bundle["quality_gates"] = [*predecessor_gates, *gate_records]
    bundle["transition"] = {
        "command_id": f"command-submit-gate-{primary.content_sha256[:16]}",
        "tenant_id": primary.tenant_id,
        "project_id": primary.project_id,
        "run_id": primary.run_id,
        "expected_revision": primary.revision,
        "idempotency_key": f"idem-submit-gate-{primary.content_sha256[:16]}",
        "operation": "submit_for_gate",
        "from_step_id": "0",
        "to_step_id": "1",
        "input_hash": run["input_hash"],
        "output_hash": primary.content_sha256,
        "requested_at": primary.created_at,
        "predecessor_release": {
            key: predecessor[key]
            for key in (
                "step_id",
                "gate_id",
                "status",
                "artifact_id",
                "artifact_sha256",
                "artifact_revision",
            )
        },
        "quality_gate": {
            "quality_gate_run_id": domain_gate["quality_gate_run_id"],
            "result": domain_gate["result"],
            "artifact_id": domain_gate["artifact_id"],
            "artifact_sha256": domain_gate["artifact_sha256"],
        },
        "artifacts": [
            {
                "artifact_id": record.artifact_id,
                "revision": record.revision,
                "content_sha256": record.content_sha256,
            }
            for record in records
        ],
        "quality_gates": [
            {
                "quality_gate_run_id": record["quality_gate_run_id"],
                "result": record["result"],
                "artifact_id": record["artifact_id"],
                "artifact_sha256": record["artifact_sha256"],
            }
            for record in gate_records
        ],
    }
