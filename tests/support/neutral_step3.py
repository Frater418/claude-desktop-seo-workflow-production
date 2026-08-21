from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from services.operator_api.artifact_revision_types import ArtifactIdentity, artifact_id_for
from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet
from services.operator_api.step_validation import GateContext
from services.step3_preflight.validator import step2_solver_projection


@dataclass(frozen=True, slots=True)
class NeutralStep3Fixture:
    output_set: ProviderOutputSet
    bundle: dict
    gate_context: GateContext


def build_neutral_step3_fixture(root: Path, project: dict, predecessor_artifact: dict, predecessor_release: dict, predecessor_qgr: dict, predecessor_content: str, run: dict) -> NeutralStep3Fixture:
    registry = _load(root / "standards/runtime/official-prompt-registry.json")
    contract_id = next(entry["output_contracts"][0]["contract_id"] for entry in registry["entries"] if entry["step_id"] == "3")
    fixture = _load(root / "tests/fixtures/step3/non-ahd-solar-fr-ca.json")
    candidate = fixture["candidate"]
    candidate.pop("input_sha256", None)
    candidate.pop("output_sha256", None)
    candidate = _replace(candidate, {source: predecessor_artifact["artifact_id"] for source in candidate.get("source_artifact_ids", [])})
    revision = int(run["revision"]) + 1
    candidate.update({"artifact_id": artifact_id_for(ArtifactIdentity(contract_id=contract_id, tenant_id=project["tenant"]["tenant_id"], project_id=project["project_id"], run_id=run["run_id"], step_id="3", revision=revision)), "run_id": run["run_id"], "project_id": project["project_id"], "deployment_id": project["market_deployments"][0]["deployment_id"], "source_artifact_ids": [predecessor_artifact["artifact_id"]], "step_id": "3", "revision": revision, "candidate_status": "awaiting_gate"})
    solver_input = {"rows": step2_solver_projection(json.loads(predecessor_content))["rows"]}
    solver_output = {key: candidate[key] for key in ("weeks", "mandatory_item_ids", "backlog_item_ids", "vertical_links", "horizontal_links")}
    candidate["solver_input"] = _canonical(solver_input).decode("utf-8")
    candidate["solver_output"] = _canonical(solver_output).decode("utf-8")
    candidate["solver_input_sha256"] = hashlib.sha256(candidate["solver_input"].encode("utf-8")).hexdigest()
    candidate["solver_output_sha256"] = hashlib.sha256(candidate["solver_output"].encode("utf-8")).hexdigest()
    content = _canonical(candidate)
    output = ProviderOutput(contract_id=contract_id, content_bytes=content, content_sha256=hashlib.sha256(content).hexdigest(), content_type="application/json", tenant_id=project["tenant"]["tenant_id"], project_id=project["project_id"], run_id=run["run_id"], step_id="3", idempotency_key="idem-simulated-neutral-step3-0001", parent_revision=revision - 1, target_revision=revision, created_at=datetime(2026, 8, 20, 12, 25, tzinfo=UTC))
    bundle = {"candidate": candidate, "project": project, "predecessor_artifact": predecessor_artifact, "predecessor_release": predecessor_release, "gate_record": predecessor_qgr, "predecessor_content": predecessor_content}
    evidence = {"schema_id": "simulated-neutral-step3", "schema_version": "1.0.0", "artifact_sha256": output.content_sha256, "validator_result": "passed"}
    solver_evidence = {"input_hash": candidate["solver_input_sha256"], "solver_version": "simulated-neutral-1.0.0", "output_hash": candidate["solver_output_sha256"], "allocated_count": str(sum(len(week["item_ids"]) for week in candidate["weeks"])), "backlog_count": str(len(candidate["backlog_item_ids"]))}
    return NeutralStep3Fixture(ProviderOutputSet.from_registry(registry, primary=output), bundle, GateContext.model_validate({"configured_tools": [], "available_tools": [], "not_applicable_decisions": {}, "evidence_by_gate": {"qg-domain-contract": evidence, "qg-step3-deterministic-plan": solver_evidence}}))


def _replace(value: object, substitutions: dict[str, str]) -> object:
    if isinstance(value, dict): return {key: _replace(item, substitutions) for key, item in value.items()}
    if isinstance(value, list): return [_replace(item, substitutions) for item in value]
    if isinstance(value, str): return substitutions.get(value, value)
    return value


def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
