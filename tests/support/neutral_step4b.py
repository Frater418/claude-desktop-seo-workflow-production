from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from services.operator_api.artifact_revision_types import ArtifactIdentity, artifact_id_for
from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet
from services.operator_api.step_validation import GateContext
from services.step4b_preflight.validator import page_content_sha256


@dataclass(frozen=True, slots=True)
class NeutralStep4BFixture:
    output_set: ProviderOutputSet
    bundle: dict
    gate_context: GateContext


def build_neutral_step4b_fixture(root: Path, project: dict, artifact: dict, release: dict, qgr: dict, run: dict) -> NeutralStep4BFixture:
    registry = _load(root / "standards/runtime/official-prompt-registry.json")
    contracts = next(entry["output_contracts"] for entry in registry["entries"] if entry["step_id"] == "4b")
    bundle = _load(root / "tests/fixtures/step4b/non-ahd-product-bundle.json")
    page, staging = bundle["page_spec"], bundle["staging_evidence"]
    revision = int(run["revision"]) + 1
    page.update({"artifact_id": artifact_id_for(ArtifactIdentity(contract_id=contracts[0]["contract_id"], tenant_id=project["tenant"]["tenant_id"], project_id=project["project_id"], run_id=run["run_id"], step_id="4b", revision=revision)), "run_id": run["run_id"], "project_id": project["project_id"], "deployment_id": project["market_deployments"][0]["deployment_id"], "source_artifact_ids": [artifact["artifact_id"]], "step_id": "4b", "revision": revision, "candidate_status": "awaiting_gate", "language": "de", "locale": "de-DE"})
    page["service_area"]["areas"] = ["Germany"]
    graph = {"@context": "https://schema.org", "@graph": [{"@id": "https://simulated-neutral.example/page#product", "@type": "Product", "name": "Simulated neutral page"}]}
    page["jsonld"] = {"level": "basic", "graph": graph, "graph_hash": hashlib.sha256(json.dumps(graph, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()).hexdigest()}
    page["content_sha256"] = page_content_sha256(page)
    staging["content_sha256"] = page["content_sha256"]
    content = json.dumps(page, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    output = ProviderOutput(contract_id=contracts[0]["contract_id"], content_bytes=content, content_sha256=hashlib.sha256(content).hexdigest(), content_type="application/json", tenant_id=project["tenant"]["tenant_id"], project_id=project["project_id"], run_id=run["run_id"], step_id="4b", idempotency_key="idem-simulated-neutral-step4b", parent_revision=revision - 1, target_revision=revision, created_at=datetime(2026, 8, 20, 12, 35, tzinfo=UTC))
    supporting = tuple(ProviderOutput(contract_id=contract["contract_id"], content_bytes=json.dumps(staging, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(), content_sha256=hashlib.sha256(json.dumps(staging, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()).hexdigest(), content_type="application/json", tenant_id=project["tenant"]["tenant_id"], project_id=project["project_id"], run_id=run["run_id"], step_id="4b", idempotency_key="idem-simulated-neutral-step4b", parent_revision=revision - 1, target_revision=revision, created_at=datetime(2026, 8, 20, 12, 35, tzinfo=UTC)) for contract in contracts[1:])
    bundle.update({"page_spec": page, "staging_evidence": staging, "project": project, "predecessor_artifact": artifact, "predecessor_release": release, "gate_record": qgr})
    domain = {"schema_id": "simulated-neutral-step4b", "schema_version": "1.0.0", "artifact_sha256": output.content_sha256, "validator_result": "passed"}
    return NeutralStep4BFixture(ProviderOutputSet.from_registry(registry, primary=output, supporting=supporting), bundle, GateContext.model_validate({"configured_tools": [], "available_tools": [], "not_applicable_decisions": {}, "evidence_by_gate": {"qg-domain-contract": domain}}))


def _load(path: Path) -> dict: return json.loads(path.read_text(encoding="utf-8"))
