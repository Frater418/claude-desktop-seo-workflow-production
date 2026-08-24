from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from services.operator_api.artifact_revision_types import ArtifactIdentity, artifact_id_for
from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet
from services.operator_api.step_validation import GateContext


@dataclass(frozen=True, slots=True)
class NeutralStep1Fixture:
    output_set: ProviderOutputSet
    bundle: dict
    gate_context: GateContext


def build_neutral_step1_fixture(root: Path, project: dict, source_artifact: dict, source_release: dict, gate0_approval: dict, gate0_qgr: dict, step1_run: dict) -> NeutralStep1Fixture:
    registry = _load(root / "standards/runtime/official-prompt-registry.json")
    contract_id = next(entry["output_contracts"][0]["contract_id"] for entry in registry["entries"] if entry["step_id"] == "1")
    revision = int(step1_run["revision"]) + 1
    identity = ArtifactIdentity(contract_id=contract_id, tenant_id=project["tenant"]["tenant_id"], project_id=project["project_id"], run_id=step1_run["run_id"], step_id="1", revision=revision)
    artifact_id = artifact_id_for(identity)
    inventory = _inventory(root, project, source_artifact, step1_run, artifact_id, revision)
    content = _canonical(inventory)
    content_hash = hashlib.sha256(content).hexdigest()
    output = ProviderOutput(contract_id=contract_id, content_bytes=content, content_sha256=content_hash, content_type="application/json", tenant_id=identity.tenant_id, project_id=identity.project_id, run_id=identity.run_id, step_id="1", idempotency_key="idem-simulated-neutral-step1-0001", parent_revision=revision - 1, target_revision=revision, created_at=datetime(2026, 8, 20, 12, 5, tzinfo=UTC))
    artifact = _artifact(output, artifact_id, source_artifact["artifact_id"])
    bundle = _bundle(root, project, inventory, content, artifact, source_artifact, source_release, gate0_approval, gate0_qgr, step1_run)
    return NeutralStep1Fixture(ProviderOutputSet.from_registry(registry, primary=output), bundle, _gate_context(content_hash))


def _inventory(root: Path, project: dict, source_artifact: dict, step1_run: dict, artifact_id: str, revision: int) -> dict:
    inventory = _load(root / "tests/fixtures/step1/positive-inventory.json")
    deployment_id = project["market_deployments"][0]["deployment_id"]
    substitutions = {"artifact-step1-0001": artifact_id, "artifact-step0-0001": source_artifact["artifact_id"], "run-step1-0001": step1_run["run_id"], "project-regional-care": project["project_id"], "dep-regional-care-de": deployment_id, "evidence-source-0001": "evidence-neutral-source", "evidence-competitor-0001": "evidence-neutral-competitor", "evidence-existing-url-0001": "evidence-neutral-existing-url", "evidence-crawl-0001": "evidence-neutral-crawl"}
    inventory = _replace(inventory, substitutions)
    inventory.update({"artifact_id": artifact_id, "run_id": step1_run["run_id"], "project_id": project["project_id"], "deployment_id": deployment_id, "step_id": "1", "revision": revision, "source_artifact_ids": [source_artifact["artifact_id"]], "evidence_ids": ["evidence-neutral-source", "evidence-neutral-competitor", "evidence-neutral-existing-url", "evidence-neutral-crawl"], "candidate_status": "awaiting_gate"})
    return inventory


def _bundle(root: Path, project: dict, inventory: dict, content: bytes, artifact: dict, source_artifact: dict, source_release: dict, gate0_approval: dict, gate0_qgr: dict, step1_run: dict) -> dict:
    bundle = _load(root / "tests/fixtures/step1/positive-bundle.json")
    content_hash = artifact["content_sha256"]
    crawl_artifact = dict(artifact, producer_version="simulated-neutral-crawl", storage_key=artifact["storage_key"].replace("content.md", "simulated-crawl.json"))
    snapshot = copy.deepcopy(bundle["crawl_snapshots"][0])
    snapshot.update({"schema_version": "1.1.0", "run_id": step1_run["run_id"], "project_id": project["project_id"], "deployment_id": inventory["deployment_id"], "final_url": snapshot["start_url"], "status": "passed", "limit_hit": False, "findings": {key: 0 for key in ("status_4xx", "status_5xx", "internal_html_4xx", "resource_4xx", "non_indexable", "missing_titles", "missing_titles_indexable", "missing_meta_descriptions", "missing_meta_descriptions_indexable", "missing_h1", "missing_h1_indexable", "missing_h2_indexable", "canonical_issues", "canonical_issues_indexable", "internal_link_issues", "redirect_issues", "broken_internal_links", "hreflang_issues", "structured_data_issues", "critical_security_issues", "security_issues")}, "policy_disposition": {"policy_id": "heartweb-crawl-disposition", "policy_version": "1.0.0", "step_id": "1", "result": "passed", "advisory_findings": [], "waiver_required_findings": [], "blocking_findings": [], "waived_findings": [], "waiver_ids": []}})
    crawl_gate = _quality_gate(step1_run["run_id"], "qgr-simulated-neutral-step1-crawl", "qg-step1-crawl-snapshot", artifact, content_hash)
    inventory_gate = _quality_gate(step1_run["run_id"], "qgr-simulated-neutral-step1-contract", "qg-domain-contract", artifact, content_hash)
    evidence = _replace(bundle["evidence_records"], {"tenant-heartweb": project["tenant"]["tenant_id"], "project-regional-care": project["project_id"], "evidence-source-0001": "evidence-neutral-source", "evidence-competitor-0001": "evidence-neutral-competitor", "evidence-existing-url-0001": "evidence-neutral-existing-url", "evidence-crawl-0001": "evidence-neutral-crawl"})
    for record in evidence:
        if record["evidence_id"] == "evidence-neutral-crawl":
            record.update({"content_sha256": content_hash, "publisher": "Simulated neutral crawl", "source_ref": "https://simulated-neutral.example/crawl"})
    run = dict(step1_run, revision=artifact["revision"], status="awaiting_gate", input_hash=source_artifact["content_sha256"], output_hash=content_hash, idempotency_key="idem-simulated-neutral-step1-0001", created_at="2026-08-20T12:05:00Z")
    run.pop("gate_context", None)
    bundle.update({"project": project, "inventory": inventory, "inventory_bytes": content.decode("ascii"), "artifact": artifact, "source_artifact": source_artifact, "run": run, "gate0_approval": gate0_approval, "quality_gates": [gate0_qgr, crawl_gate, inventory_gate], "evidence_records": evidence, "crawl_snapshots": [snapshot], "crawl_artifacts": [crawl_artifact], "crawl_snapshot_hashes": {step1_run["run_id"]: content_hash}, "waivers": [], "approval": None, "as_of": gate0_approval["decided_at"], "gate_context": _preflight_context(), "transition": {"command_id": "command-simulated-neutral-step1-submit", "tenant_id": project["tenant"]["tenant_id"], "project_id": project["project_id"], "run_id": step1_run["run_id"], "expected_revision": artifact["revision"], "idempotency_key": "idem-simulated-neutral-step1-submit", "operation": "submit_for_gate", "from_step_id": "0", "to_step_id": "1", "input_hash": source_artifact["content_sha256"], "output_hash": content_hash, "artifacts": [{"artifact_id": artifact["artifact_id"], "revision": artifact["revision"], "content_sha256": content_hash}], "requested_at": "2026-08-20T12:05:30Z", "predecessor_release": {key: source_release[key] for key in ("step_id", "gate_id", "status", "artifact_id", "artifact_sha256", "artifact_revision")}, "quality_gate": {"quality_gate_run_id": inventory_gate["quality_gate_run_id"], "result": "passed", "artifact_id": artifact["artifact_id"], "artifact_sha256": content_hash}}})
    return bundle


def _artifact(output: ProviderOutput, artifact_id: str, source_artifact_id: str) -> dict:
    return {"artifact_id": artifact_id, "tenant_id": output.tenant_id, "project_id": output.project_id, "run_id": output.run_id, "step_id": "1", "revision": output.target_revision, "input_hash": "0" * 64, "content_sha256": output.content_sha256, "parent_artifact_ids": [source_artifact_id], "contract_version": "2.0.0", "producer_version": "simulated-neutral-step1", "storage_key": f"tenants/{output.tenant_id}/projects/{output.project_id}/runs/{output.run_id}/artifacts/{artifact_id}/content.md", "created_at": "2026-08-20T12:05:00Z"}


def _quality_gate(run_id: str, qgr_id: str, gate_id: str, artifact: dict, content_hash: str) -> dict:
    evidence = {"schema_id": "simulated-neutral-step1", "schema_version": "1.0.0", "artifact_sha256": content_hash, "validator_result": "passed", "crawl_manifest": "simulated-neutral-crawl", "start_url": "https://simulated-neutral.example/", "tool_version": "simulated-1.0.0", "export_hashes": content_hash, "url_count": "1", "issues_overview": "none"}
    return {"quality_gate_run_id": qgr_id, "quality_gate_id": gate_id, "human_gate_id": "GATE-1", "tenant_id": artifact["tenant_id"], "run_id": run_id, "step_id": "1", "artifact_id": artifact["artifact_id"], "artifact_sha256": content_hash, "artifact_revision": artifact["revision"], "registry_version": "1.1.0", "policy_version": "1.0.0", "result": "passed", "evidence": evidence, "findings": [], "checked_at": "2026-08-20T12:05:30Z", "checker_version": "simulated-neutral-step1"}


def _gate_context(content_hash: str) -> GateContext:
    domain_evidence = {"schema_id": "simulated-neutral-step1", "schema_version": "1.0.0", "artifact_sha256": content_hash, "validator_result": "passed"}
    crawl_evidence = {"crawl_manifest": "simulated-neutral-crawl", "start_url": "https://simulated-neutral.example/", "tool_version": "simulated-1.0.0", "export_hashes": content_hash, "url_count": "1", "issues_overview": "none"}
    return GateContext.model_validate({"site_status": "existing_site", "configured_tools": [], "available_tools": ["jsonschema", "screaming-frog-cli"], "not_applicable_decisions": {"qg-step1-independent-search-verification": {"reason": "Simulated neutral route has no independent search source."}}, "evidence_by_gate": {"qg-domain-contract": domain_evidence, "qg-step1-crawl-snapshot": crawl_evidence}})


def _preflight_context() -> dict:
    return {"site_status": "existing_site", "multilingual": False, "ymyl": False, "local": False, "production": False, "configured_tools": [], "available_tools": ["jsonschema", "screaming-frog-cli"], "not_applicable_decisions": {"qg-step1-independent-search-verification": {"reason": "Simulated neutral route has no independent search source."}}}


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
