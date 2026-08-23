from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from services.operator_api.artifact_revision_types import ArtifactIdentity, artifact_id_for
from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet
from services.operator_api.step_validation import GateContext


@dataclass(frozen=True, slots=True)
class NeutralStep1CFixture:
    output_set: ProviderOutputSet
    bundle: dict
    gate_context: GateContext


def build_neutral_step1c_fixture(root: Path, project: dict, predecessor_artifact: dict, predecessor_release: dict, predecessor_qgr: dict, run: dict) -> NeutralStep1CFixture:
    registry = _load(root / "standards/runtime/official-prompt-registry.json")
    contracts = next(entry["output_contracts"] for entry in registry["entries"] if entry["step_id"] == "1c")
    revision = int(run["revision"]) + 1
    identity = {"tenant_id": project["tenant"]["tenant_id"], "project_id": project["project_id"], "run_id": run["run_id"], "step_id": "1c", "revision": revision}
    design_id = artifact_id_for(ArtifactIdentity(contract_id=contracts[0]["contract_id"], **identity))
    design = _load(root / "tests/fixtures/step1c/positive-design-system.json")
    template = _load(root / "tests/fixtures/step1c/positive-template.json")
    design = _replace(design, {source: predecessor_artifact["artifact_id"] for source in design.get("source_artifact_ids", [])})
    design.update({"artifact_id": design_id, "run_id": run["run_id"], "project_id": project["project_id"], "deployment_id": project["market_deployments"][0]["deployment_id"], "source_artifact_ids": [predecessor_artifact["artifact_id"]], "step_id": "1c", "revision": revision, "candidate_status": "awaiting_gate"})
    template = _replace(template, {source: design_id for source in template.get("source_artifact_ids", [])})
    template.update({"project_id": project["project_id"], "deployment_id": design["deployment_id"], "source_artifact_ids": [design_id]})
    primary = _output(contracts[0]["contract_id"], _canonical(design), identity)
    supporting = _output(contracts[1]["contract_id"], _canonical(template), identity)
    bundle = {"design": design, "templates": [template], "project": project, "predecessor_artifact": predecessor_artifact, "predecessor_release": predecessor_release, "gate_record": predecessor_qgr}
    evidence = {"design_token_hash": primary.content_sha256, "axe_report": "simulated-neutral-passed", "visual_diff_report": "simulated-neutral-passed", "viewport_matrix": "desktop,mobile"}
    domain_evidence = {"schema_id": "simulated-neutral-step1c", "schema_version": "1.0.0", "artifact_sha256": primary.content_sha256, "validator_result": "passed"}
    return NeutralStep1CFixture(ProviderOutputSet.from_registry(registry, primary=primary, supporting=(supporting,)), bundle, GateContext.model_validate({"configured_tools": [], "available_tools": [], "not_applicable_decisions": {}, "evidence_by_gate": {"qg-domain-contract": domain_evidence, "qg-step1c-design-system": evidence}}))


def _output(contract_id: str, content: bytes, identity: dict) -> ProviderOutput:
    return ProviderOutput(contract_id=contract_id, content_bytes=content, content_sha256=hashlib.sha256(content).hexdigest(), content_type="application/json", tenant_id=identity["tenant_id"], project_id=identity["project_id"], run_id=identity["run_id"], step_id=identity["step_id"], idempotency_key="idem-simulated-neutral-step1c-0001", parent_revision=identity["revision"] - 1, target_revision=identity["revision"], created_at=datetime(2026, 8, 20, 12, 15, tzinfo=UTC))


def _replace(value: object, substitutions: dict[str, str]) -> object:
    if isinstance(value, dict):
        return {key: _replace(item, substitutions) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace(item, substitutions) for item in value]
    if isinstance(value, str):
        return substitutions.get(value, value)
    return value


def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
