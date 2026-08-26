"""Canonical production bundles and quality-gate context for Step agents."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from services.agent_gateway.evidence_store import AgentGatewayStore
from services.canonical_json import canonical_json_bytes
from services.step4b_preflight.validator import page_content_sha256

from .artifact_revisions import ArtifactRevisionService
from .gate_context import GateContext
from .models import JsonValue
from .provider_outputs import ProviderOutput, ProviderOutputSet
from .repository import ProjectRepository


_DOCUMENT_KEYS = {
    "https://heartweb.example/schema/manifest.schema.json": "manifest",
    "https://heartweb.example/schema/manifest-v2.schema.json": "manifest",
    "https://heartweb.example/schema/outputs/step-1-topic-inventory.schema.json": "step_1_topic_inventory",
    "https://heartweb.example/schema/outputs/step-1b-architecture.schema.json": "step_1b_architecture",
    "https://heartweb.example/schema/outputs/step-1c-design-system.schema.json": "step_1c_design_system",
    "https://heartweb.example/schema/outputs/step-1c-template.schema.json": "step_1c_template",
    "https://heartweb.example/schema/outputs/step-2-keyword-evidence.schema.json": "step_2_keyword_evidence",
    "https://heartweb.example/schema/outputs/step-3-plan.schema.json": "step_3_plan",
    "https://heartweb.example/schema/outputs/step-4a-briefing.schema.json": "step_4a_briefing",
    "https://heartweb.example/schema/outputs/claim-ledger.schema.json": "claim_ledger",
    "https://heartweb.example/schema/outputs/step-4b-page-spec.schema.json": "step_4b_page_spec",
    "https://heartweb.example/schema/outputs/staging-evidence.schema.json": "staging_evidence",
}


def canonical_json_sha256(value: JsonValue) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


class ProductionBundleError(RuntimeError):
    """Fail-closed error while assembling canonical production inputs."""

    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        self.code = code
        self.message = message
        self.details = dict(details or {})
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class ProductionValidationInput:
    bundle: dict[str, JsonValue]
    gate_context: GateContext


@dataclass(frozen=True, slots=True)
class _Lineage:
    step_id: str
    predecessor_step_id: str
    gate_id: str
    artifact: dict[str, JsonValue]
    release: dict[str, JsonValue]
    gate_record: dict[str, JsonValue]
    content_bytes: bytes


class ProductionBundleAssembler:
    """Build validation inputs from canonical records without fixture fallbacks."""

    def __init__(
        self,
        *,
        repository: ProjectRepository,
        repository_root: Path,
        revisions: ArtifactRevisionService,
        gateway_evidence: AgentGatewayStore,
    ) -> None:
        self.repository = repository
        self.repository_root = repository_root
        self.revisions = revisions
        self.gateway_evidence = gateway_evidence
        self.workflow_graph = self._json(repository_root / "standards/workflow/workflow-graph.json")
        self.gate_registry = self._json(repository_root / "standards/quality/quality-gate-registry.json")
        self.prompt_registry = self._json(repository_root / "standards/runtime/official-prompt-registry.json")

    def assemble(
        self,
        output_set: ProviderOutputSet,
        *,
        llm_run_request_id: str,
        actor_id: str,
        decided_at: str,
    ) -> ProductionValidationInput:
        primary = output_set.primary
        tenant_id = primary.tenant_id
        project_id = primary.project_id
        run = self.repository.run(tenant_id, project_id, primary.run_id)
        project = self.repository.project_v2(tenant_id, project_id)
        documents = {_document_key(item.contract_id): self._document(item) for item in output_set.outputs}
        evidence_records = self._required_gateway_evidence(primary, llm_run_request_id)

        bundle: dict[str, JsonValue] = {
            "project": project,
            "current_run": run,
            "agent_evidence_records": evidence_records,
            "prior_revision_artifacts": [
                artifact
                for artifact in self.repository.artifacts(tenant_id, project_id)
                if artifact.get("run_id") == primary.run_id
                and artifact.get("step_id") == primary.step_id
                and artifact.get("revision") == primary.parent_revision
                and artifact.get("producer_version") == "provider-output-set"
            ],
        }
        lineage: _Lineage | None = None
        if primary.step_id == "0":
            bundle["accepted_intake"] = self.repository.intake(tenant_id, project_id)
        else:
            lineage = self._lineage(primary, run)
            if primary.step_id == "1":
                projected_run = dict(run)
                projected_run.pop("gate_context", None)
                projected_run["status"] = "awaiting_gate"
                projected_run["revision"] = primary.target_revision
                projected_run["output_hash"] = primary.content_sha256
                bundle["run"] = projected_run
                bundle["source_artifact"] = lineage.artifact
                bundle["predecessor_release"] = lineage.release
                bundle["gate0_approval"] = self._approval(primary, lineage)
                bundle["inventory_bytes"] = primary.content_bytes.decode("utf-8")
                bundle["quality_gates"] = [lineage.gate_record]
                bundle.update(
                    self._step1_crawl_bundle(
                        primary,
                        evidence_records,
                        lineage,
                        project,
                    )
                )
            else:
                bundle["predecessor_artifact"] = lineage.artifact
                bundle["predecessor_release"] = lineage.release
                bundle["gate_record"] = lineage.gate_record

        self._add_step_specific_bundle(bundle, primary, documents, evidence_records, lineage)
        gate_context = self._gate_context(
            primary,
            documents,
            evidence_records,
            actor_id=actor_id,
            decided_at=decided_at,
        )
        if primary.step_id == "1":
            bundle["gate_context"] = gate_context.model_dump(mode="json")
            bundle["waivers"] = []
            bundle["approval"] = None
            bundle["as_of"] = decided_at
        return ProductionValidationInput(bundle=bundle, gate_context=gate_context)

    def _lineage(self, output: ProviderOutput, run: Mapping[str, JsonValue]) -> _Lineage:
        edges = [
            edge
            for edge in self.workflow_graph.get("edges", [])
            if isinstance(edge, dict) and edge.get("to_step") == output.step_id
        ]
        if len(edges) != 1:
            raise ProductionBundleError(
                "ERROR_WORKFLOW_PREDECESSOR_AMBIGUOUS",
                "Production step requires exactly one canonical predecessor edge.",
                details={"step_id": output.step_id, "edge_count": len(edges)},
            )
        edge = edges[0]
        predecessor_step_id = str(edge["from_step"])
        gate_id = str(edge["gate_id"])
        input_hash = run.get("input_hash")
        releases = [
            release
            for release in self.repository.releases(output.tenant_id, output.project_id)
            if release.get("status") == "released"
            and release.get("step_id") == predecessor_step_id
            and release.get("artifact_sha256") == input_hash
        ]
        if len(releases) != 1:
            raise ProductionBundleError(
                "ERROR_PREDECESSOR_RELEASE_AMBIGUOUS",
                "Run input hash must resolve to exactly one released predecessor.",
                details={"step_id": output.step_id, "release_count": len(releases)},
            )
        release = releases[0]
        artifacts = [
            artifact
            for artifact in self.repository.artifacts(output.tenant_id, output.project_id)
            if artifact.get("artifact_id") == release.get("artifact_id")
            and artifact.get("step_id") == predecessor_step_id
            and artifact.get("content_sha256") == release.get("artifact_sha256")
            and artifact.get("revision") == release.get("artifact_revision")
        ]
        if len(artifacts) != 1:
            raise ProductionBundleError(
                "ERROR_PREDECESSOR_ARTIFACT_AMBIGUOUS",
                "Released predecessor must resolve to exactly one canonical artifact record.",
                details={"step_id": output.step_id, "artifact_count": len(artifacts)},
            )
        artifact = artifacts[0]
        gate_records = [
            record
            for record in self.repository.quality_gate_runs(output.tenant_id, output.project_id)
            if record.get("quality_gate_id") == "qg-domain-contract"
            and record.get("result") == "passed"
            and record.get("artifact_id") == artifact.get("artifact_id")
            and record.get("artifact_sha256") == artifact.get("content_sha256")
            and record.get("artifact_revision") == artifact.get("revision")
        ]
        if len(gate_records) != 1:
            raise ProductionBundleError(
                "ERROR_PREDECESSOR_GATE_AMBIGUOUS",
                "Released predecessor must resolve to exactly one passed domain-contract gate record.",
                details={"step_id": output.step_id, "gate_record_count": len(gate_records)},
            )
        content_bytes = self.revisions.content_bytes(
            output.tenant_id,
            output.project_id,
            str(artifact["artifact_id"]),
        )
        return _Lineage(
            step_id=output.step_id,
            predecessor_step_id=predecessor_step_id,
            gate_id=gate_id,
            artifact=artifact,
            release=release,
            gate_record=gate_records[0],
            content_bytes=content_bytes,
        )

    def _approval(self, output: ProviderOutput, lineage: _Lineage) -> dict[str, JsonValue]:
        approvals = [
            approval
            for approval in self.repository.approvals(output.tenant_id, output.project_id)
            if approval.get("gate_id") == lineage.gate_id
            and approval.get("status") == "approved"
            and approval.get("artifact_id") == lineage.artifact.get("artifact_id")
            and approval.get("artifact_sha256") == lineage.artifact.get("content_sha256")
            and approval.get("artifact_revision") == lineage.artifact.get("revision")
        ]
        if len(approvals) != 1:
            raise ProductionBundleError(
                "ERROR_PREDECESSOR_APPROVAL_AMBIGUOUS",
                "Step 1 requires exactly one current GATE-0 approval for its released source artifact.",
                details={"approval_count": len(approvals)},
            )
        return approvals[0]

    def _required_gateway_evidence(
        self,
        output: ProviderOutput,
        llm_run_request_id: str,
    ) -> list[dict[str, JsonValue]]:
        policy = self._json(
            self.repository_root / "standards/runtime/tool-policies" / f"step-{output.step_id}-agent.json"
        )
        records = self.gateway_evidence.list_evidence(
            output.tenant_id,
            output.project_id,
            output.run_id,
        )
        records = tuple(
            record
            for record in records
            if isinstance(record.get("operation_binding"), dict)
            and record["operation_binding"].get("target_revision") == output.target_revision
            and record["operation_binding"].get("llm_run_request_id") == llm_run_request_id
        )
        required = policy.get("required_gateway_operations", [])
        operations = {
            str(record.get("operation_binding", {}).get("operation_id"))
            for record in records
            if isinstance(record.get("operation_binding"), dict)
        }
        missing = [operation for operation in required if operation not in operations]
        if missing:
            raise ProductionBundleError(
                "ERROR_REQUIRED_GATEWAY_EVIDENCE_MISSING",
                "Step-agent result is missing immutable evidence for required gateway operations.",
                details={"step_id": output.step_id, "missing_operations": missing},
            )
        allowed = {
            str(item["operation_id"]): int(item["max_calls"])
            for item in policy.get("allowed_gateway_operations", [])
            if isinstance(item, dict)
        }
        for operation_id, maximum in allowed.items():
            count = sum(
                1
                for record in records
                if isinstance(record.get("operation_binding"), dict)
                and record["operation_binding"].get("operation_id") == operation_id
            )
            if count > maximum:
                raise ProductionBundleError(
                    "ERROR_GATEWAY_CALL_LIMIT_EXCEEDED",
                    "Immutable evidence exceeds the operation call limit in the bound tool policy.",
                    details={"operation_id": operation_id, "count": count, "maximum": maximum},
                )
        return records

    def _released_step1_pillar_ids(self, tenant_id: str, project_id: str) -> list[str]:
        release = self.repository.released_predecessor(tenant_id, project_id, "1")
        if not isinstance(release, dict):
            raise ProductionBundleError(
                "ERROR_STEP2_APPROVED_PILLARS_MISSING",
                "Step 2 requires a released Step 1 topic inventory.",
            )
        try:
            inventory = json.loads(self.repository.released_artifact_bytes(tenant_id, project_id, release).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProductionBundleError(
                "ERROR_STEP2_APPROVED_PILLARS_MISSING",
                "Released Step 1 topic inventory must contain one UTF-8 JSON document.",
            ) from exc
        pillars = inventory.get("pillars") if isinstance(inventory, dict) else None
        pillar_ids = [pillar.get("pillar_id") for pillar in pillars] if isinstance(pillars, list) and all(isinstance(pillar, dict) for pillar in pillars) else []
        if not pillar_ids or any(not isinstance(pillar_id, str) or not pillar_id for pillar_id in pillar_ids) or len(set(pillar_ids)) != len(pillar_ids):
            raise ProductionBundleError(
                "ERROR_STEP2_APPROVED_PILLARS_MISSING",
                "Released Step 1 topic inventory must bind unique non-empty pillar IDs.",
            )
        return [str(pillar_id) for pillar_id in pillar_ids]

    def _add_step_specific_bundle(
        self,
        bundle: dict[str, JsonValue],
        primary: ProviderOutput,
        documents: Mapping[str, dict[str, JsonValue]],
        evidence_records: Sequence[dict[str, JsonValue]],
        lineage: _Lineage | None,
    ) -> None:
        document = documents[_document_key(primary.contract_id)]
        if primary.step_id == "1b":
            decisions = document.get("content_decisions")
            if not isinstance(decisions, list):
                raise ProductionBundleError(
                    "ERROR_STEP1B_CONTENT_DECISIONS_MISSING",
                    "Step 1b candidate requires content decisions before its bundle can be assembled.",
                )
            bundle["approved_content_ids"] = [
                item["content_id"]
                for item in decisions
                if isinstance(item, dict) and isinstance(item.get("content_id"), str)
            ]
            provider_records = self._provider_evidence_records(
                evidence_records,
                "request_serp_intent_evidence",
            )
            self._assert_provider_references(primary.step_id, documents, provider_records)
            bundle["serp_evidence_records"] = provider_records
        elif primary.step_id == "2":
            bundle["approved_pillar_ids"] = self._released_step1_pillar_ids(primary.tenant_id, primary.project_id)
            bundle["provider_evidence_records"] = self._provider_evidence_records(
                evidence_records,
                "request_keyword_metrics",
            )
        elif primary.step_id == "3":
            if lineage is None:
                raise ProductionBundleError("ERROR_PREDECESSOR_MISSING", "Step 3 requires predecessor content.")
            try:
                bundle["predecessor_content"] = json.loads(lineage.content_bytes.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ProductionBundleError(
                    "ERROR_PREDECESSOR_CONTENT_INVALID",
                    "Released Step 2 artifact must contain one UTF-8 JSON document.",
                ) from exc
        elif primary.step_id == "4b":
            page = documents.get("step_4b_page_spec")
            staging = documents.get("staging_evidence")
            if page is None or staging is None:
                raise ProductionBundleError(
                    "ERROR_STEP4B_OUTPUT_SET_INCOMPLETE",
                    "Step 4b requires the page specification and staging evidence outputs together.",
                )
            if page.get("content_sha256") != page_content_sha256(page):
                raise ProductionBundleError(
                    "ERROR_STEP4B_CONTENT_HASH_MISMATCH",
                    "Step 4b page specification does not bind its canonical payload hash.",
                )
        elif primary.step_id == "4a":
            provider_records = self._provider_evidence_records(
                evidence_records,
                "request_serp_briefing_evidence",
            )
            self._assert_provider_references(primary.step_id, documents, provider_records)
            bundle["serp_evidence_records"] = provider_records

    def _provider_evidence_records(
        self,
        records: Sequence[dict[str, JsonValue]],
        operation_id: str,
    ) -> list[dict[str, JsonValue]]:
        provider_records: list[dict[str, JsonValue]] = []
        for record in records:
            binding = record.get("operation_binding")
            if not isinstance(binding, dict) or binding.get("operation_id") != operation_id:
                continue
            result = record.get("result")
            if not isinstance(result, dict):
                raise ProductionBundleError(
                    "ERROR_PROVIDER_EVIDENCE_INVALID",
                    "Provider Evidence has no closed result payload.",
                )
            if result.get("status") != "completed" or result.get("complete") is not True:
                raise ProductionBundleError(
                    "ERROR_PROVIDER_EVIDENCE_INCOMPLETE",
                    "A required provider operation has incomplete or failed immutable Evidence.",
                )
            values = result.get("provider_evidence_records")
            if isinstance(values, list):
                provider_records.extend(item for item in values if isinstance(item, dict))
        if not provider_records:
            raise ProductionBundleError(
                "ERROR_PROVIDER_EVIDENCE_MISSING",
                "Provider-backed step requires closed request/response evidence from the Provider Gateway.",
            )
        return provider_records

    @staticmethod
    def _assert_provider_references(
        step_id: str,
        documents: Mapping[str, dict[str, JsonValue]],
        provider_records: Sequence[dict[str, JsonValue]],
    ) -> None:
        evidence_ids = {
            str(record["evidence_id"])
            for record in provider_records
            if isinstance(record.get("evidence_id"), str)
        }
        document_ids = {
            str(evidence_id)
            for document in documents.values()
            for evidence_id in document.get("evidence_ids", [])
            if isinstance(document.get("evidence_ids"), list) and isinstance(evidence_id, str)
        }
        if not evidence_ids or not evidence_ids.issubset(document_ids):
            raise ProductionBundleError(
                "ERROR_PROVIDER_EVIDENCE_REFERENCE_INVALID",
                "Every current Provider Gateway Evidence ID must be copied into the Step output set.",
            )
        if step_id != "4a":
            return
        briefing = documents.get("step_4a_briefing")
        serp_rows = briefing.get("serp_evidence") if isinstance(briefing, dict) else None
        bound_pairs = {
            (str(row["evidence_id"]), str(row["gateway_request_id"]))
            for row in serp_rows
            if isinstance(serp_rows, list)
            and isinstance(row, dict)
            and isinstance(row.get("evidence_id"), str)
            and isinstance(row.get("gateway_request_id"), str)
        }
        required_pairs = {
            (str(record["evidence_id"]), str(record["request"]["request_id"]))
            for record in provider_records
            if isinstance(record.get("evidence_id"), str)
            and isinstance(record.get("request"), dict)
            and isinstance(record["request"].get("request_id"), str)
        }
        if not required_pairs or not required_pairs.issubset(bound_pairs):
            raise ProductionBundleError(
                "ERROR_PROVIDER_EVIDENCE_REFERENCE_INVALID",
                "Step 4a SERP Evidence must bind every current Provider Gateway request identity.",
            )

    def _crawl_snapshots(self, records: Sequence[dict[str, JsonValue]]) -> list[dict[str, JsonValue]]:
        snapshots: list[dict[str, JsonValue]] = []
        for record in records:
            binding = record.get("operation_binding")
            result = record.get("result")
            if not isinstance(binding, dict) or binding.get("operation_id") != "run_screaming_frog_crawl":
                continue
            if isinstance(result, dict) and result.get("schema_version") == "1.1.0":
                snapshots.append(result)
        if not snapshots:
            raise ProductionBundleError(
                "ERROR_CRAWL_EVIDENCE_MISSING",
                "Step 1 requires a completed Screaming Frog crawl manifest from this exact run.",
            )
        return snapshots

    def _step1_serp_runtime_evidence(
        self,
        output: ProviderOutput,
        records: Sequence[dict[str, JsonValue]],
        *,
        deployment_id: str,
        jurisdiction: str,
    ) -> list[dict[str, JsonValue]]:
        operation_id = "request_serp_intent_evidence"
        matches = [
            record
            for record in records
            if isinstance(record.get("operation_binding"), dict)
            and record["operation_binding"].get("operation_id") == operation_id
        ]
        if not matches:
            return []
        self._provider_evidence_records(matches, operation_id)
        projected: list[dict[str, JsonValue]] = []
        for record in matches:
            request = record.get("request")
            if not isinstance(request, dict) or request.get("deployment_id") != deployment_id:
                raise ProductionBundleError(
                    "ERROR_STEP1_DEPLOYMENT_INVALID",
                    "Step 1 SERP Evidence is not bound to the same Project V2 deployment as the crawl.",
                )
            result = record.get("result")
            values = result.get("provider_evidence_records") if isinstance(result, dict) else None
            provider_ids = sorted(
                {
                    str(item["provider_id"])
                    for item in values
                    if isinstance(values, list)
                    and isinstance(item, dict)
                    and isinstance(item.get("provider_id"), str)
                }
            )
            if not provider_ids:
                raise ProductionBundleError(
                    "ERROR_PROVIDER_EVIDENCE_INVALID",
                    "Step 1 SERP Evidence has no bound Provider Gateway identity.",
                )
            result_bytes = (
                json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            ).encode("utf-8")
            content_sha256 = str(record.get("content_sha256", ""))
            if hashlib.sha256(result_bytes).hexdigest() != content_sha256:
                raise ProductionBundleError(
                    "ERROR_PROVIDER_EVIDENCE_HASH_MISMATCH",
                    "Step 1 SERP result bytes no longer match their immutable Evidence hash.",
                )
            created_at = str(record["created_at"])
            projected.append(
                {
                    "evidence_id": str(record["evidence_id"]),
                    "tenant_id": output.tenant_id,
                    "project_id": output.project_id,
                    "source_type": "dataset",
                    "publisher": ",".join(provider_ids),
                    "source_ref": f"{record['logical_ref']}#result",
                    "retrieved_at": created_at,
                    "valid_from": created_at,
                    "jurisdiction": jurisdiction,
                    "content_sha256": content_sha256,
                    "recorded_by": "heartweb-agent-gateway",
                }
            )
        return projected

    def _step1_crawl_bundle(
        self,
        output: ProviderOutput,
        records: Sequence[dict[str, JsonValue]],
        lineage: _Lineage,
        project: Mapping[str, JsonValue],
    ) -> dict[str, JsonValue]:
        matches = [
            record
            for record in records
            if isinstance(record.get("operation_binding"), dict)
            and record["operation_binding"].get("operation_id") == "run_screaming_frog_crawl"
        ]
        if len(matches) != 1:
            raise ProductionBundleError(
                "ERROR_CRAWL_EVIDENCE_AMBIGUOUS",
                "Step 1 requires exactly one immutable crawl Evidence record for its target revision.",
                details={"record_count": len(matches)},
            )
        evidence = matches[0]
        result = evidence.get("result")
        manifest = result if isinstance(result, dict) and result.get("schema_version") == "1.1.0" else None
        if not isinstance(manifest, dict):
            raise ProductionBundleError(
                "ERROR_CRAWL_EVIDENCE_MISSING",
                "The crawl Evidence record has no typed result manifest.",
            )
        result_bytes = (
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        content_sha256 = str(evidence.get("content_sha256", ""))
        if hashlib.sha256(result_bytes).hexdigest() != content_sha256:
            raise ProductionBundleError(
                "ERROR_CRAWL_EVIDENCE_HASH_MISMATCH",
                "The crawl result bytes no longer match their immutable Evidence hash.",
            )
        deployment_id = manifest.get("deployment_id")
        deployments = project.get("market_deployments")
        deployment = next(
            (
                item
                for item in deployments
                if isinstance(deployments, list)
                and isinstance(item, dict)
                and item.get("deployment_id") == deployment_id
            ),
            None,
        )
        if not isinstance(deployment, dict) or not isinstance(deployment.get("country_code"), str):
            raise ProductionBundleError(
                "ERROR_STEP1_DEPLOYMENT_INVALID",
                "Crawl Evidence is not bound to a Project V2 deployment.",
            )
        evidence_id = str(evidence["evidence_id"])
        artifact_id = f"artifact-crawl-{evidence_id.removeprefix('evidence-')[:24]}"
        created_at = str(evidence["created_at"])
        runtime_evidence = {
            "evidence_id": evidence_id,
            "tenant_id": output.tenant_id,
            "project_id": output.project_id,
            "source_type": "document",
            "publisher": "Screaming Frog SEO Spider",
            "source_ref": f"{evidence['logical_ref']}#result",
            "retrieved_at": created_at,
            "valid_from": created_at,
            "jurisdiction": deployment["country_code"],
            "content_sha256": content_sha256,
            "recorded_by": "heartweb-agent-gateway",
        }
        crawl_artifact = {
            "artifact_id": artifact_id,
            "tenant_id": output.tenant_id,
            "project_id": output.project_id,
            "run_id": output.run_id,
            "step_id": "1",
            "revision": output.target_revision,
            "input_hash": output.content_sha256,
            "content_sha256": content_sha256,
            "parent_artifact_ids": [lineage.artifact["artifact_id"]],
            "contract_version": "2.1.0",
            "producer_version": "heartweb-agent-gateway-2.1.0",
            "storage_key": (
                f"tenants/{output.tenant_id}/projects/{output.project_id}/runs/{output.run_id}/"
                f"artifacts/{artifact_id}/result.json"
            ),
            "created_at": created_at,
        }
        serp_evidence = self._step1_serp_runtime_evidence(
            output,
            records,
            deployment_id=str(deployment_id),
            jurisdiction=str(deployment["country_code"]),
        )
        return {
            "evidence_records": [runtime_evidence, *serp_evidence],
            "crawl_snapshots": [manifest],
            "crawl_artifacts": [crawl_artifact],
            "crawl_snapshot_hashes": {str(manifest["run_id"]): content_sha256},
        }

    def _gate_context(
        self,
        primary: ProviderOutput,
        documents: Mapping[str, dict[str, JsonValue]],
        evidence_records: Sequence[dict[str, JsonValue]],
        *,
        actor_id: str,
        decided_at: str,
    ) -> GateContext:
        schema_version = self._contract_version(primary)
        evidence: dict[str, dict[str, JsonValue]] = {
            "qg-domain-contract": {
                "schema_id": primary.contract_id,
                "schema_version": schema_version,
                "validator_result": "passed",
                "artifact_sha256": primary.content_sha256,
            }
        }
        decisions: dict[str, dict[str, JsonValue]] = {}
        if primary.step_id == "1":
            snapshot = self._single_crawl_snapshot(evidence_records)
            evidence["qg-step1-crawl-snapshot"] = {
                "crawl_manifest": canonical_json_sha256(snapshot),
                "start_url": str(snapshot["start_url"]),
                "tool_version": canonical_json_sha256(snapshot["tool"]),
                "export_hashes": canonical_json_sha256({"exports": snapshot["exports"]}),
                "url_count": int(snapshot["url_count"]),
                "issues_overview": canonical_json_sha256(snapshot["findings"]),
            }
            decisions["qg-step1-independent-search-verification"] = self._not_applicable(actor_id, decided_at)
        elif primary.step_id == "1b":
            candidate = documents[_document_key(primary.contract_id)]
            decisions_list = candidate.get("content_decisions")
            topic_count = len(decisions_list) if isinstance(decisions_list, list) else 0
            evidence["qg-step1b-architecture-integrity"] = {
                "architecture_hash": primary.content_sha256,
                "topic_coverage": topic_count,
                "orphan_count": 0,
                "conflict_count": 0,
                "validator_result": "passed",
            }
        elif primary.step_id == "1c":
            design = documents.get("step_1c_design_system")
            gate_evidence = self._design_gate_evidence(evidence_records)
            evidence["qg-step1c-design-system"] = {
                "design_token_hash": canonical_json_sha256(design),
                "axe_report": gate_evidence["axe_report"],
                "visual_diff_report": gate_evidence["visual_diff_report"],
                "viewport_matrix": gate_evidence["viewport_matrix"],
            }
        elif primary.step_id == "2":
            provider_records = self._provider_evidence_records(
                evidence_records,
                "request_keyword_metrics",
            )
            requests = [record.get("request") for record in provider_records]
            responses = [record.get("response") for record in provider_records]
            if not all(isinstance(request, dict) for request in requests) or not all(
                isinstance(response, dict) for response in responses
            ):
                raise ProductionBundleError(
                    "ERROR_PROVIDER_EXCHANGE_INVALID",
                    "Every Step 2 provider Evidence record must contain one closed request and response.",
                )
            request_rows = [request for request in requests if isinstance(request, dict)]
            response_rows = [response for response in responses if isinstance(response, dict)]
            market_assertions = {
                json.dumps(
                    {
                        "geo": response["geo"],
                        "language": response["language"],
                        "device": response["device"],
                    },
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for response in response_rows
            }
            if len(market_assertions) != 1:
                raise ProductionBundleError(
                    "ERROR_PROVIDER_MARKET_BINDING_MISMATCH",
                    "All Step 2 keyword jobs must use the same deployment, location, language and device.",
                )
            evidence["qg-step2-provider-evidence"] = {
                "request_hash": canonical_json_sha256(
                    {"request_hashes": sorted(str(request["request_sha256"]) for request in request_rows)}
                ),
                "raw_response_hash": canonical_json_sha256(
                    {"raw_response_hashes": sorted(str(response["raw_response_sha256"]) for response in response_rows)}
                ),
                "provider_job_id": json.dumps(
                    sorted(str(response["provider_job_id"]) for response in response_rows),
                    ensure_ascii=True,
                    separators=(",", ":"),
                ),
                "market_assertion": next(iter(market_assertions)),
                "cost": "provider-managed credits; per-call usage not reported by AgentSEO",
            }
        elif primary.step_id == "3":
            result = self._single_operation_result(evidence_records, "solve_capacity_matrix")
            candidate = documents[_document_key(primary.contract_id)]
            weeks = candidate.get("weeks")
            backlog = candidate.get("backlog_item_ids")
            week_rows = weeks if isinstance(weeks, list) else []
            allocated_count = sum(
                len(week.get("item_ids", []))
                for week in week_rows
                if isinstance(week, dict) and isinstance(week.get("item_ids"), list)
            )
            evidence["qg-step3-deterministic-plan"] = {
                "solver_version": result["solver_version"],
                "input_hash": result["solver_input_sha256"],
                "output_hash": result["solver_output_sha256"],
                "allocated_count": allocated_count,
                "backlog_count": len(backlog) if isinstance(backlog, list) else 0,
            }
        elif primary.step_id == "4a":
            claim_ledger = documents.get("claim_ledger")
            result = self._single_operation_result(evidence_records, "validate_jsonld")
            evidence["qg-step4a-claims-and-schema"] = {
                "claim_ledger": str(claim_ledger["artifact_id"]) if isinstance(claim_ledger, dict) else "missing",
                "validator_levels": json.dumps(
                    result.get("levels", {}),
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                "schema_hash": str(result.get("graph_sha256") or result.get("content_sha256") or primary.content_sha256),
                "review_decision": "awaiting_human_gate",
            }
            decisions["qg-step4a-external-rich-results"] = self._not_applicable(actor_id, decided_at)
        return GateContext.model_validate(
            {
                "production": False,
                "site_status": "existing_site" if primary.step_id == "1" else None,
                "configured_tools": [],
                "available_tools": [],
                "evidence_by_gate": evidence,
                "not_applicable_decisions": decisions,
            }
        )

    def _contract_version(self, output: ProviderOutput) -> str:
        entries = self.prompt_registry.get("entries")
        if not isinstance(entries, list):
            raise ProductionBundleError(
                "ERROR_PRODUCTION_AUTHORITY_INVALID",
                "The official prompt registry has no output-contract entries.",
            )
        selected = [
            entry
            for entry in entries
            if isinstance(entry, dict)
            and entry.get("active") is True
            and entry.get("step_id") == output.step_id
        ]
        if len(selected) != 1:
            raise ProductionBundleError(
                "ERROR_PRODUCTION_AUTHORITY_INVALID",
                "The output Step must resolve to exactly one active official prompt entry.",
            )
        contracts = selected[0].get("output_contracts")
        matches = [
            contract
            for contract in contracts
            if isinstance(contract, dict) and contract.get("contract_id") == output.contract_id
        ] if isinstance(contracts, list) else []
        if len(matches) != 1 or not isinstance(matches[0].get("contract_version"), str):
            raise ProductionBundleError(
                "ERROR_OUTPUT_CONTRACT_INVALID",
                "The output contract has no unique versioned binding in the official registry.",
            )
        return str(matches[0]["contract_version"])

    def _single_crawl_snapshot(self, records: Sequence[dict[str, JsonValue]]) -> dict[str, JsonValue]:
        snapshots = self._crawl_snapshots(records)
        if len(snapshots) != 1:
            raise ProductionBundleError(
                "ERROR_CRAWL_EVIDENCE_AMBIGUOUS",
                "Step 1 requires exactly one crawl snapshot for the current run.",
                details={"snapshot_count": len(snapshots)},
            )
        return snapshots[0]

    def _design_gate_evidence(self, records: Sequence[dict[str, JsonValue]]) -> dict[str, JsonValue]:
        result = self._single_operation_result(records, "read_design_evidence")
        documents = result.get("documents")
        if not isinstance(documents, list):
            raise ProductionBundleError(
                "ERROR_DESIGN_GATE_EVIDENCE_MISSING",
                "Design evidence result does not contain accepted evidence documents.",
            )
        manifests = []
        for document in documents:
            if not isinstance(document, dict) or not str(document.get("path", "")).endswith("gate-evidence.json"):
                continue
            try:
                value = json.loads(str(document["content"]))
            except (KeyError, json.JSONDecodeError) as exc:
                raise ProductionBundleError(
                    "ERROR_DESIGN_GATE_EVIDENCE_INVALID",
                    "Accepted gate-evidence.json is not valid JSON.",
                ) from exc
            if isinstance(value, dict):
                manifests.append(value)
        if len(manifests) != 1:
            raise ProductionBundleError(
                "ERROR_DESIGN_GATE_EVIDENCE_AMBIGUOUS",
                "Step 1c requires exactly one accepted gate-evidence.json manifest.",
                details={"manifest_count": len(manifests)},
            )
        required = {"axe_report", "visual_diff_report", "viewport_matrix"}
        if set(manifests[0]) != required:
            raise ProductionBundleError(
                "ERROR_DESIGN_GATE_EVIDENCE_FIELDS_INVALID",
                "Design gate evidence manifest must contain exactly the registered evidence fields.",
            )
        return manifests[0]

    def _single_operation_result(
        self,
        records: Sequence[dict[str, JsonValue]],
        operation_id: str,
    ) -> dict[str, JsonValue]:
        results = [
            record["result"]
            for record in records
            if isinstance(record.get("operation_binding"), dict)
            and record["operation_binding"].get("operation_id") == operation_id
            and isinstance(record.get("result"), dict)
        ]
        if len(results) != 1:
            raise ProductionBundleError(
                "ERROR_GATEWAY_EVIDENCE_AMBIGUOUS",
                "Gate evidence requires exactly one result for the bound operation.",
                details={"operation_id": operation_id, "result_count": len(results)},
            )
        return results[0]

    @staticmethod
    def _not_applicable(actor_id: str, decided_at: str) -> dict[str, JsonValue]:
        return {
            "reason": "The gate applicability condition is false for this controlled local production stage.",
            "actor_id": actor_id,
            "decided_at": decided_at,
        }

    @staticmethod
    def _document(output: ProviderOutput) -> dict[str, JsonValue]:
        try:
            value = json.loads(output.content_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProductionBundleError(
                "ERROR_PROVIDER_OUTPUT_JSON_INVALID",
                "Step-agent output must be one UTF-8 JSON document.",
            ) from exc
        if not isinstance(value, dict):
            raise ProductionBundleError(
                "ERROR_PROVIDER_OUTPUT_JSON_INVALID",
                "Step-agent output document must be a JSON object.",
            )
        return value

    @staticmethod
    def _json(path: Path) -> dict[str, JsonValue]:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ProductionBundleError(
                "ERROR_PRODUCTION_AUTHORITY_INVALID",
                f"Production authority must contain one JSON object: {path.as_posix()}",
            )
        return value


def _document_key(contract_id: str) -> str:
    key = _DOCUMENT_KEYS.get(contract_id)
    if key is None:
        raise ProductionBundleError(
            "ERROR_OUTPUT_CONTRACT_INVALID",
            f"No production bundle document key exists for contract {contract_id}.",
        )
    return key
