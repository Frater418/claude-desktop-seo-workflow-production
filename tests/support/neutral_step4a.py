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
class NeutralStep4AFixture:
    output_set: ProviderOutputSet
    bundle: dict
    gate_context: GateContext


def build_neutral_step4a_fixture(root: Path, project: dict, artifact: dict, release: dict, qgr: dict, run: dict) -> NeutralStep4AFixture:
    registry = _load(root / "standards/runtime/official-prompt-registry.json")
    contracts = next(entry["output_contracts"] for entry in registry["entries"] if entry["step_id"] == "4a")
    bundle = _load(root / "tests/fixtures/step4a/non-ahd-b2b-bundle.json")
    briefing, ledger = bundle["briefing"], bundle["claim_ledger"]
    revision = int(run["revision"]) + 1
    briefing_id = artifact_id_for(ArtifactIdentity(contract_id=contracts[0]["contract_id"], tenant_id=project["tenant"]["tenant_id"], project_id=project["project_id"], run_id=run["run_id"], step_id="4a", revision=revision))
    briefing.update({"artifact_id": briefing_id, "run_id": run["run_id"], "project_id": project["project_id"], "source_artifact_ids": [artifact["artifact_id"]], "step_id": "4a", "revision": revision, "candidate_status": "awaiting_gate", "claim_ledger_artifact_id": ledger["artifact_id"]})
    graph = {"@context": "https://schema.org", "@graph": [{"@id": "https://simulated-neutral.example/briefing#product", "@type": "Product", "name": "Simulated neutral briefing"}]}
    briefing["jsonld"] = {"level": "basic", "graph": graph, "graph_hash": _hash(graph)}
    briefing["claim_bindings"] = [{"claim_id": claim["claim_id"], "graph_node_id": "https://simulated-neutral.example/briefing#product"} for claim in ledger["claims"]]
    briefing["briefing_sections"] = {
        "audience": "Editors preparing a neutral product comparison briefing.",
        "search_intent": "informational comparison",
        "primary_keyword": "simulated product comparison",
        "content_goal": "Prepare an evidence-bound briefing without external execution claims.",
        "tone": "neutral and evidence-bound",
        "cta_guidance": "Invite a review of the approved briefing before publication.",
        "internal_link_guidance": "Link only to the approved predecessor plan.",
        "copywriter_instructions": "Preserve claim evidence bindings and reviewer controls.",
        "secondary_keywords": ["neutral briefing", "evidence-bound comparison"],
        "outline": ["Direct answer", "Evidence", "Claim review", "Publication checklist"],
        "publication_checklist": ["Verify evidence", "Confirm claim ledger", "Approve JSON-LD"],
        "definitive_language_guidance": {
            "required": True,
            "preferred_patterns": ["evidence indicates", "review before publication"],
            "prohibited_patterns": ["guarantees", "proven outcome"],
            "rationale": "The local fixture must not imply unverified outcomes.",
        },
    }
    briefing["entity_bindings"] = {
        "about": [{"name": "Simulated neutral product", "wikidata_uri": "https://www.wikidata.org/wiki/Q1", "graph_node_id": "https://simulated-neutral.example/briefing#product"}],
        "mentions": [],
    }
    primary = _output(contracts[0]["contract_id"], briefing, project, run, revision)
    supporting = _output(contracts[1]["contract_id"], ledger, project, run, revision)
    bundle.update({"briefing": briefing, "claim_ledger": ledger, "project": project, "predecessor_artifact": artifact, "predecessor_release": release, "gate_record": qgr})
    domain = {"schema_id": "simulated-neutral-step4a", "schema_version": "1.0.0", "artifact_sha256": primary.content_sha256, "validator_result": "passed"}
    claims = {"claim_ledger": "simulated-neutral", "validator_levels": "basic", "schema_hash": briefing["jsonld"]["graph_hash"], "review_decision": "simulated-approved"}
    return NeutralStep4AFixture(ProviderOutputSet.from_registry(registry, primary=primary, supporting=(supporting,)), bundle, GateContext.model_validate({"configured_tools": [], "available_tools": [], "not_applicable_decisions": {}, "evidence_by_gate": {"qg-domain-contract": domain, "qg-step4a-claims-and-schema": claims}}))


def _output(contract_id: str, value: dict, project: dict, run: dict, revision: int) -> ProviderOutput:
    content = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    return ProviderOutput(contract_id=contract_id, content_bytes=content, content_sha256=hashlib.sha256(content).hexdigest(), content_type="application/json", tenant_id=project["tenant"]["tenant_id"], project_id=project["project_id"], run_id=run["run_id"], step_id="4a", idempotency_key="idem-simulated-neutral-step4a", parent_revision=revision - 1, target_revision=revision, created_at=datetime(2026, 8, 20, 12, 30, tzinfo=UTC))


def _hash(value: dict) -> str: return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()).hexdigest()
def _load(path: Path) -> dict: return json.loads(path.read_text(encoding="utf-8"))
