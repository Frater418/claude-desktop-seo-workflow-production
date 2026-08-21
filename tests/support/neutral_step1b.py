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
class NeutralStep1BFixture:
    output_set: ProviderOutputSet
    bundle: dict
    gate_context: GateContext


def build_neutral_step1b_fixture(root: Path, project: dict, predecessor_artifact: dict, predecessor_release: dict, predecessor_qgr: dict, run: dict) -> NeutralStep1BFixture:
    registry = _load(root / "standards/runtime/official-prompt-registry.json")
    contract_id = next(entry["output_contracts"][0]["contract_id"] for entry in registry["entries"] if entry["step_id"] == "1b")
    revision = int(run["revision"]) + 1
    artifact_id = artifact_id_for(ArtifactIdentity(contract_id=contract_id, tenant_id=project["tenant"]["tenant_id"], project_id=project["project_id"], run_id=run["run_id"], step_id="1b", revision=revision))
    candidate = _load(root / "tests/fixtures/step1b/positive-architecture.json")
    candidate = _replace(candidate, {source: predecessor_artifact["artifact_id"] for source in candidate.get("source_artifact_ids", [])})
    candidate.update({"artifact_id": artifact_id, "run_id": run["run_id"], "project_id": project["project_id"], "deployment_id": project["market_deployments"][0]["deployment_id"], "source_artifact_ids": [predecessor_artifact["artifact_id"]], "step_id": "1b", "revision": revision, "candidate_status": "awaiting_gate"})
    content = _canonical(candidate)
    output = ProviderOutput(contract_id=contract_id, content_bytes=content, content_sha256=hashlib.sha256(content).hexdigest(), content_type="application/json", tenant_id=project["tenant"]["tenant_id"], project_id=project["project_id"], run_id=run["run_id"], step_id="1b", idempotency_key="idem-simulated-neutral-step1b-0001", parent_revision=revision - 1, target_revision=revision, created_at=datetime(2026, 8, 20, 12, 10, tzinfo=UTC))
    bundle = {"candidate": candidate, "approved_content_ids": [item["content_id"] for item in candidate["content_decisions"]], "project": project, "predecessor_artifact": predecessor_artifact, "predecessor_release": predecessor_release, "gate_record": predecessor_qgr}
    evidence = {"architecture_hash": output.content_sha256, "topic_coverage": str(len(bundle["approved_content_ids"])), "orphan_count": "0", "conflict_count": "0", "validator_result": "simulated-neutral-passed"}
    domain_evidence = {"schema_id": "simulated-neutral-step1b", "schema_version": "1.0.0", "artifact_sha256": output.content_sha256, "validator_result": "passed"}
    return NeutralStep1BFixture(ProviderOutputSet.from_registry(registry, primary=output), bundle, GateContext.model_validate({"configured_tools": [], "available_tools": [], "not_applicable_decisions": {}, "evidence_by_gate": {"qg-domain-contract": domain_evidence, "qg-step1b-architecture-integrity": evidence}}))


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
