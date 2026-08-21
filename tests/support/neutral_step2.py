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
class NeutralStep2Fixture:
    output_set: ProviderOutputSet
    bundle: dict
    gate_context: GateContext


def build_neutral_step2_fixture(root: Path, project: dict, predecessor_artifact: dict, predecessor_release: dict, predecessor_qgr: dict, run: dict) -> NeutralStep2Fixture:
    registry = _load(root / "standards/runtime/official-prompt-registry.json")
    contract_id = next(entry["output_contracts"][0]["contract_id"] for entry in registry["entries"] if entry["step_id"] == "2")
    fixture = _load(root / "tests/fixtures/step2/non-ahd-solar-fr-ca.json")
    candidate = fixture["candidate"]
    candidate = _replace(candidate, {source: predecessor_artifact["artifact_id"] for source in candidate.get("source_artifact_ids", [])})
    deployment = project["market_deployments"][0]
    candidate.update({"artifact_id": artifact_id_for(ArtifactIdentity(contract_id=contract_id, tenant_id=project["tenant"]["tenant_id"], project_id=project["project_id"], run_id=run["run_id"], step_id="2", revision=int(run["revision"]) + 1)), "run_id": run["run_id"], "project_id": project["project_id"], "deployment_id": deployment["deployment_id"], "source_artifact_ids": [predecessor_artifact["artifact_id"]], "step_id": "2", "revision": int(run["revision"]) + 1, "candidate_status": "awaiting_gate", "language": "de", "geo": {"country_code": "DE", "provider_location_code": 276}})
    candidate["evidence_ids"] = [row["evidence_id"] for pillar in candidate["pillars"] for row in pillar["rows"]]
    records = _provider_records(candidate, predecessor_artifact["artifact_id"])
    for record in records:
        for exchange in (record["request"], record["response"]):
            exchange.update({"run_id": run["run_id"], "project_id": project["project_id"], "deployment_id": deployment["deployment_id"], "language": candidate["language"], "geo": candidate["geo"]})
        raw = record["response"]["raw_response"]
        record["response"]["raw_response_sha256"] = _hash(raw)
        row = next(row for pillar in candidate["pillars"] for row in pillar["rows"] if row["evidence_id"] == record["evidence_id"])
        row["raw_response_sha256"] = record["response"]["raw_response_sha256"]
    content = _canonical(candidate)
    output = ProviderOutput(contract_id=contract_id, content_bytes=content, content_sha256=hashlib.sha256(content).hexdigest(), content_type="application/json", tenant_id=project["tenant"]["tenant_id"], project_id=project["project_id"], run_id=run["run_id"], step_id="2", idempotency_key="idem-simulated-neutral-step2-0001", parent_revision=int(run["revision"]), target_revision=int(run["revision"]) + 1, created_at=datetime(2026, 8, 20, 12, 20, tzinfo=UTC))
    bundle = {"candidate": candidate, "project": project, "predecessor_artifact": predecessor_artifact, "predecessor_release": predecessor_release, "gate_record": predecessor_qgr, "provider_evidence_records": records}
    evidence = {"schema_id": "simulated-neutral-step2", "schema_version": "1.0.0", "artifact_sha256": output.content_sha256, "validator_result": "passed"}
    provider_evidence = {"request_hash": records[0]["request"]["request_sha256"], "raw_response_hash": records[0]["response"]["raw_response_sha256"], "provider_job_id": records[0]["response"]["provider_job_id"], "market_assertion": "simulated-neutral-geo-bound", "cost": "0.5", "raw_evidence_artifact_sha256": output.content_sha256}
    return NeutralStep2Fixture(ProviderOutputSet.from_registry(registry, primary=output), bundle, GateContext.model_validate({"configured_tools": [], "available_tools": [], "not_applicable_decisions": {}, "evidence_by_gate": {"qg-domain-contract": evidence, "qg-step2-provider-evidence": provider_evidence}}))


def _hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()


def _provider_records(candidate: dict, source_artifact_id: str) -> list[dict]:
    records = []
    for pillar in candidate["pillars"]:
        for index, row in enumerate(pillar["rows"], start=1):
            request = {"schema_version": "2.0.0", "request_id": f"request-simulated-neutral-{index:04d}", "run_id": candidate["run_id"], "project_id": candidate["project_id"], "deployment_id": candidate["deployment_id"], "revision": 1, "source_artifact_ids": [source_artifact_id], "evidence_ids": [row["evidence_id"]], "decision_records": [{"decision_id": f"decision-simulated-neutral-{index:04d}", "outcome": "research", "evidence_ids": [row["evidence_id"]]}], "candidate_status": "candidate", "provider": row["provider"], "operation": "keyword_metrics", "idempotency_key": f"simulated-neutral-{index:04d}", "request_sha256": "d" * 64, "geo": candidate["geo"], "language": candidate["language"], "device": "mobile", "cost": {"currency": "USD", "maximum": 1}, "gateway_route": "provider_gateway"}
            raw_response = {"keyword": row["keyword"]}
            response = {"schema_version": "2.0.0", "response_id": f"response-simulated-neutral-{index:04d}", "request_id": request["request_id"], "run_id": candidate["run_id"], "project_id": candidate["project_id"], "deployment_id": candidate["deployment_id"], "revision": 1, "source_artifact_ids": [source_artifact_id], "evidence_ids": [row["evidence_id"]], "decision_records": request["decision_records"], "candidate_status": "candidate", "provider": row["provider"], "provider_job_id": f"job-simulated-neutral-{index:04d}", "status": "completed", "geo": candidate["geo"], "language": candidate["language"], "device": "mobile", "cost": {"currency": "USD", "actual": 0.5}, "raw_response": raw_response, "raw_response_sha256": _hash(raw_response)}
            row["raw_response_sha256"] = response["raw_response_sha256"]
            records.append({"evidence_id": row["evidence_id"], "request": request, "response": response})
    return records


def _replace(value: object, substitutions: dict[str, str]) -> object:
    if isinstance(value, dict): return {key: _replace(item, substitutions) for key, item in value.items()}
    if isinstance(value, list): return [_replace(item, substitutions) for item in value]
    if isinstance(value, str): return substitutions.get(value, value)
    return value


def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
