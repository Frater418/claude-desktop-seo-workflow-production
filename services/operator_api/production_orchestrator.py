from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar, Mapping

from jsonschema import Draft202012Validator, FormatChecker

from services.agent_gateway.evidence_store import AgentGatewayStore, AgentGatewayStoreError
from services.transition_service import process_transition

from .event_store import EventStore, EventStoreError
from .hermes_runs_client import HermesRunsError, HermesRunWaiting
from .models import (
    JsonValue,
    ProductionConfirmRequest,
    ProductionConfirmResult,
    ProductionSteeredRerunRequest,
    ProductionTechnicalRetryRequest,
    ToolInteractionDecisionRequest,
)
from .production_bundles import ProductionBundleAssembler, ProductionBundleError
from .production_execution_store import (
    ProductionExecutionError,
    ProductionExecutionStore,
)
from .repository import ProjectRepository, RepositoryError
from .runtime import RuntimeProviderError
from .step_agent_results import StepAgentResultError
from .step_validation import StepValidationError


def _parsed_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _evidence_blocks_technical_retry(
    evidence: Mapping[str, Any],
    source_execution: Mapping[str, Any],
) -> bool:
    dispatch = source_execution.get("dispatch")
    llm_request = dispatch.get("llm_request") if isinstance(dispatch, Mapping) else None
    source_request_id = llm_request.get("llm_run_request_id") if isinstance(llm_request, Mapping) else None
    if not isinstance(source_request_id, str) or not source_request_id:
        return True

    binding = evidence.get("operation_binding")
    if not isinstance(binding, Mapping):
        return True
    if "llm_run_request_id" in binding:
        evidence_request_id = binding.get("llm_run_request_id")
        if not isinstance(evidence_request_id, str) or not evidence_request_id:
            return True
        belongs_to_source = evidence_request_id == source_request_id
        return belongs_to_source and not _operation_binding_is_replay_safe(binding)

    evidence_created_at = _parsed_timestamp(evidence.get("created_at"))
    source_created_at = _parsed_timestamp(source_execution.get("created_at"))
    if evidence_created_at is None or source_created_at is None:
        return True
    belongs_to_source = evidence_created_at >= source_created_at
    return belongs_to_source and not _operation_binding_is_replay_safe(binding)


def _operation_binding_is_replay_safe(binding: Mapping[str, Any]) -> bool:
    return (
        binding.get("confirmation_scope") == "none"
        and binding.get("cost_mode") == "none"
        and binding.get("side_effect") in {"none", "read_only"}
    )


def _artifact_blocks_technical_retry(
    artifact: Mapping[str, Any],
    source_execution: Mapping[str, Any],
) -> bool:
    if artifact.get("run_id") != source_execution.get("run_id"):
        return False
    artifact_revision = artifact.get("revision")
    expected_revision = source_execution.get("expected_revision")
    if (
        not isinstance(artifact_revision, int)
        or isinstance(artifact_revision, bool)
        or not isinstance(expected_revision, int)
        or isinstance(expected_revision, bool)
    ):
        return True
    return artifact_revision > expected_revision


def _can_resteer_in_progress(
    run: Mapping[str, Any],
    artifacts: list[Mapping[str, Any]],
    executions: list[Mapping[str, Any]],
) -> bool:
    revision = run.get("revision")
    if run.get("status") != "in_progress" or not isinstance(revision, int) or isinstance(revision, bool):
        return False
    if any(
        not isinstance(artifact.get("revision"), int)
        or isinstance(artifact.get("revision"), bool)
        or int(artifact["revision"]) > revision
        for artifact in artifacts
    ):
        return False
    if any(execution.get("status") not in {"completed", "failed", "denied"} for execution in executions):
        return False
    for execution in executions:
        dispatch = execution.get("dispatch")
        if (
            execution.get("status") == "failed"
            and isinstance(dispatch, Mapping)
            and (
                isinstance(dispatch.get("steered_rerun"), Mapping)
                or isinstance(dispatch.get("technical_retry"), Mapping)
            )
        ):
            return True
    return False


def _technical_retry_runtime_request(
    source_request: Mapping[str, str],
    *,
    retry_key: str,
    requested_at: str,
) -> dict[str, str]:
    required = ("tenant_id", "project_id", "run_id", "step_id", "actor_id", "llm_run_request_id")
    if any(not isinstance(source_request.get(field), str) or not source_request[field] for field in required):
        raise ProductionExecutionError(
            "ERROR_TECHNICAL_RETRY_INVALID",
            "The source execution does not contain a complete runtime identity.",
        )
    if not retry_key or not requested_at:
        raise ProductionExecutionError(
            "ERROR_TECHNICAL_RETRY_INVALID",
            "The technical retry identity or timestamp is missing.",
        )
    seed = _sha256_text(f"{source_request['llm_run_request_id']}|{retry_key}|technical-retry")
    retry = dict(source_request)
    retry.update(
        {
            "llm_run_request_id": f"llm-request-retry-{seed[:24]}",
            "llm_run_result_id": f"llm-result-retry-{seed[:24]}",
            "correlation_id": f"correlation-retry-{seed[:24]}",
            "idempotency_key": f"idempotency-retry-{seed[:24]}",
            "requested_at": requested_at,
            "trigger": "retry",
        }
    )
    return retry


@dataclass(frozen=True, slots=True)
class ProductionOrchestrator:
    _TECHNICAL_RETRY_CODES: ClassVar[frozenset[str]] = frozenset(
        {
            "ERROR_LLM_BACKEND_UNAVAILABLE",
            "ERROR_LLM_BACKEND_TIMEOUT",
            "ERROR_LLM_BACKEND_STREAM_UNAVAILABLE",
            "ERROR_LLM_BACKEND_RESPONSE_INVALID",
            "ERROR_LLM_BACKEND_RUN_FAILED",
            "ERROR_LOCATION_BINDING_MISMATCH",
            "ERROR_SCHEMA_VALIDATION",
            "ERROR_STEP_AGENT_EVENT_EVIDENCE_UNAVAILABLE",
            "ERROR_STEP_AGENT_OUTPUT_ENVELOPE_INVALID",
            "ERROR_STEP_AGENT_TOOL_FAILED",
        }
    )

    app: Any
    repository: ProjectRepository
    executions: ProductionExecutionStore
    gateway_evidence: AgentGatewayStore

    def start(
        self,
        request: ProductionConfirmRequest,
        snapshot: Mapping[str, Any],
    ) -> ProductionConfirmResult:
        intent = request.intent
        execution_id = self.executions.execution_id(
            intent.tenant_id,
            intent.project_id,
            intent.run_id,
            request.idempotency_key,
        )
        existing = self.executions.optional(intent.tenant_id, intent.project_id, execution_id)
        if existing is not None:
            return self.readback(existing, replay=True)
        execution_hash = _sha256_text(f"{request.preview_hash}|{request.idempotency_key}")
        runtime_request = {
            "tenant_id": intent.tenant_id,
            "project_id": intent.project_id,
            "run_id": intent.run_id,
            "step_id": intent.step_id,
            "context_package_id": f"context-{execution_hash[:24]}",
            "llm_run_request_id": f"llm-request-{execution_hash[:24]}",
            "llm_run_result_id": f"llm-result-{execution_hash[:24]}",
            "correlation_id": f"correlation-{execution_hash[:24]}",
            "idempotency_key": f"idempotency-{execution_hash[:24]}",
            "actor_id": self.app.state.operator_id,
            "requested_at": str(snapshot["requested_at"]),
        }
        workflow = self.app.state.local_workflow
        if workflow is None:
            raise RuntimeProviderError(
                "ERROR_RUNTIME_PROVIDER_BLOCKED",
                "The real Heartweb workflow runtime is unavailable.",
            )
        prepared = workflow.runtime.prepare_agent_dispatch(
            self.repository,
            self.app.state.repository_root,
            self.app.state.runtime_validator,
            runtime_request,
        )
        record = self.executions.create(
            prepared,
            preview_hash=request.preview_hash,
            idempotency_key=request.idempotency_key,
            created_at=str(snapshot["requested_at"]),
        )
        try:
            execution = workflow.runtime.start_agent_dispatch(prepared)
            record = self.executions.bind_handle(
                record,
                execution.handle,
                updated_at=self.app.state.clock.now(),
            )
        except (RuntimeProviderError, ProductionExecutionError):
            raise
        except Exception as error:
            raise RuntimeProviderError(
                "ERROR_LLM_BACKEND_UNAVAILABLE",
                "The Hermes Step-agent run could not be started safely.",
            ) from error
        return self.readback(record, replay=False)

    def refresh(
        self,
        tenant_id: str,
        project_id: str,
        execution_id: str,
    ) -> ProductionConfirmResult:
        record = self.executions.get(tenant_id, project_id, execution_id)
        if record["status"] in {"completed", "failed", "denied"}:
            return self.readback(record, replay=True)
        workflow = self.app.state.local_workflow
        registry = self.app.state.step_agent_registry
        if workflow is None or registry is None or workflow.runtime.hermes_provider is None:
            raise RuntimeProviderError(
                "ERROR_RUNTIME_PROVIDER_BLOCKED",
                "The real Heartweb workflow runtime is unavailable.",
            )
        prepared, execution = self.executions.reconstruct(
            record,
            repository_root=self.app.state.repository_root,
            step_agent_registry=registry,
        )
        if execution is None:
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_RECOVERY_REQUIRED",
                "The persisted production execution has no safely bound Hermes run identity.",
            )
        try:
            observed = workflow.runtime.hermes_provider.inspect_step(execution)
            if observed is None:
                record = self.executions.update(
                    record,
                    status="running",
                    updated_at=self.app.state.clock.now(),
                )
            elif isinstance(observed, HermesRunWaiting):
                pending = tuple(
                    interaction
                    for interaction in self.gateway_evidence.list_interactions(
                        tenant_id,
                        project_id,
                        str(record["run_id"]),
                    )
                    if interaction["status"] == "awaiting_approval"
                )
                if len(pending) != 1:
                    workflow.runtime.hermes_provider.stop_step(execution)
                    record = self.executions.update(
                        record,
                        status="failed",
                        updated_at=self.app.state.clock.now(),
                        error={
                            "code": "ERROR_TOOL_AUTHORIZATION_AMBIGUOUS",
                            "message": "Hermes waiting state must bind exactly one pending Heartweb tool interaction.",
                        },
                    )
                else:
                    record = self.executions.update(
                        record,
                        status=observed.status,
                        updated_at=self.app.state.clock.now(),
                        interaction_ids=[str(pending[0]["interaction_id"])],
                    )
            else:
                prepared_result = workflow.runtime.finalize_agent_dispatch(
                    self.repository,
                    self.app.state.repository_root,
                    self.app.state.runtime_validator,
                    prepared,
                    observed,
                )
                completion = self._persist_artifacts(prepared_result, record)
                record = self.executions.update(
                    record,
                    status="completed",
                    updated_at=self.app.state.clock.now(),
                    completion=completion,
                )
        except (
            AgentGatewayStoreError,
            HermesRunsError,
            ProductionBundleError,
            RuntimeProviderError,
            StepAgentResultError,
            StepValidationError,
        ) as error:
            code = getattr(error, "code", "ERROR_LLM_BACKEND_RUN_FAILED")
            message = getattr(error, "message", str(error))
            record = self.executions.update(
                record,
                status="failed",
                updated_at=self.app.state.clock.now(),
                error={"code": str(code), "message": str(message)},
            )
        return self.readback(record, replay=False)

    def decide(
        self,
        tenant_id: str,
        project_id: str,
        execution_id: str,
        interaction_id: str,
        request: ToolInteractionDecisionRequest,
    ) -> ProductionConfirmResult:
        record = self.executions.get(tenant_id, project_id, execution_id)
        if record["status"] not in {"interaction_required", "approval_required"}:
            raise ProductionExecutionError(
                "ERROR_TOOL_AUTHORIZATION_INVALID",
                "Production execution is not waiting for a tool decision.",
            )
        if record["interaction_ids"] != [interaction_id]:
            raise ProductionExecutionError(
                "ERROR_TOOL_AUTHORIZATION_MISMATCH",
                "The requested interaction is not the execution's unique pending interaction.",
            )
        registry = self.app.state.step_agent_registry
        workflow = self.app.state.local_workflow
        if registry is None or workflow is None or workflow.runtime.hermes_provider is None:
            raise RuntimeProviderError(
                "ERROR_RUNTIME_PROVIDER_BLOCKED",
                "The real Heartweb workflow runtime is unavailable.",
            )
        _, execution = self.executions.reconstruct(
            record,
            repository_root=self.app.state.repository_root,
            step_agent_registry=registry,
        )
        if execution is None:
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_RECOVERY_REQUIRED",
                "Production execution has no safely bound Hermes run identity.",
            )
        decision = self.gateway_evidence.decide_interaction(
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=str(record["run_id"]),
            interaction_id=interaction_id,
            expected_request_sha256=request.expected_request_sha256,
            decision="approved" if request.approved else "denied",
            actor_id=self.app.state.operator_id,
            reason=request.reason,
            decided_at=self.app.state.clock.now(),
        )
        try:
            workflow.runtime.hermes_provider.approve_step(execution, allow=request.approved)
            if request.approved:
                record = self.executions.update(
                    record,
                    status="running",
                    updated_at=self.app.state.clock.now(),
                    interaction_ids=[interaction_id],
                )
            else:
                workflow.runtime.hermes_provider.stop_step(execution)
                record = self.executions.update(
                    record,
                    status="denied",
                    updated_at=self.app.state.clock.now(),
                    interaction_ids=[interaction_id],
                    error={
                        "code": "ERROR_TOOL_AUTHORIZATION_DENIED",
                        "message": "The operator denied the exact tool request.",
                        "decision_sha256": decision["decision"]["decision_sha256"],
                    },
                )
        except HermesRunsError as error:
            record = self.executions.update(
                record,
                status="failed",
                updated_at=self.app.state.clock.now(),
                error={"code": error.code, "message": str(error)},
            )
        return self.readback(record, replay=False)

    def technical_retry(
        self,
        tenant_id: str,
        project_id: str,
        execution_id: str,
        request: ProductionTechnicalRetryRequest,
    ) -> ProductionConfirmResult:
        source = self.executions.get(tenant_id, project_id, execution_id)
        if source["record_sha256"] != request.expected_execution_sha256:
            raise ProductionExecutionError(
                "ERR_STALE_REVISION",
                "The failed execution changed after the retry preview was shown.",
            )
        error = source.get("error")
        error_code = error.get("code") if isinstance(error, dict) else None
        if source["status"] != "failed" or error_code not in self._TECHNICAL_RETRY_CODES:
            raise ProductionExecutionError(
                "ERROR_TECHNICAL_RETRY_NOT_ALLOWED",
                "Only a retryable terminal Hermes failure can start a technical retry.",
            )
        if source["interaction_ids"]:
            raise ProductionExecutionError(
                "ERROR_TECHNICAL_RETRY_UNSAFE",
                "Technical retry is blocked after a tool interaction was created.",
            )
        run_id = str(source["run_id"])
        if any(
            _evidence_blocks_technical_retry(evidence, source)
            for evidence in self.gateway_evidence.list_evidence(tenant_id, project_id, run_id)
        ):
            raise ProductionExecutionError(
                "ERROR_TECHNICAL_RETRY_UNSAFE",
                "Technical retry is blocked after immutable tool Evidence exists for the source execution.",
            )
        if any(
            _artifact_blocks_technical_retry(artifact, source)
            for artifact in self.repository.artifacts(tenant_id, project_id)
        ):
            raise ProductionExecutionError(
                "ERROR_TECHNICAL_RETRY_UNSAFE",
                "Technical retry is blocked after canonical artifacts exist.",
            )
        workflow = self.app.state.local_workflow
        registry = self.app.state.step_agent_registry
        if workflow is None or registry is None or workflow.runtime.hermes_provider is None:
            raise RuntimeProviderError(
                "ERROR_RUNTIME_PROVIDER_BLOCKED",
                "The real Heartweb workflow runtime is unavailable.",
            )
        source_prepared, _ = self.executions.reconstruct(
            source,
            repository_root=self.app.state.repository_root,
            step_agent_registry=registry,
        )
        if self.repository.run(tenant_id, project_id, run_id) != source_prepared.run:
            raise ProductionExecutionError(
                "ERR_STALE_REVISION",
                "The canonical Core run no longer matches the failed execution snapshot.",
            )
        retry_key = f"{request.idempotency_key}-retry-{execution_id[-8:]}"
        retry_request = _technical_retry_runtime_request(
            source_prepared.request,
            retry_key=retry_key,
            requested_at=str(source["updated_at"]),
        )
        prepared = workflow.runtime.prepare_agent_retry(
            source_prepared,
            self.app.state.runtime_validator,
            retry_request,
        )
        if (
            prepared.dispatch.official_prompt != source_prepared.dispatch.official_prompt
            or prepared.dispatch.registry != source_prepared.dispatch.registry
            or prepared.dispatch.worker_profile != source_prepared.dispatch.worker_profile
            or prepared.dispatch.source_bytes != source_prepared.dispatch.source_bytes
        ):
            raise ProductionExecutionError(
                "ERR_STALE_REVISION",
                "The versioned Step-agent resources changed after the failed execution.",
            )
        retry = self.executions.create(
            prepared,
            preview_hash=str(source["preview_hash"]),
            idempotency_key=retry_key,
            created_at=self.app.state.clock.now(),
            technical_retry={
                "source_execution_id": execution_id,
                "source_record_sha256": str(source["record_sha256"]),
                "reason": request.reason,
            },
        )
        if retry["status"] != "prepared":
            return self.readback(retry, replay=True)
        try:
            execution = workflow.runtime.start_agent_dispatch(prepared)
            retry = self.executions.bind_handle(
                retry,
                execution.handle,
                updated_at=self.app.state.clock.now(),
            )
        except (RuntimeProviderError, ProductionExecutionError):
            raise
        except Exception as failure:
            self.executions.update(
                retry,
                status="failed",
                updated_at=self.app.state.clock.now(),
                error={
                    "code": "ERROR_LLM_BACKEND_UNAVAILABLE",
                    "message": "The technical retry could not start a new Hermes run.",
                },
            )
            raise RuntimeProviderError(
                "ERROR_LLM_BACKEND_UNAVAILABLE",
                "The technical retry could not start a new Hermes run.",
            ) from failure
        return self.readback(retry, replay=False)

    def steered_rerun(
        self,
        tenant_id: str,
        project_id: str,
        execution_id: str,
        request: ProductionSteeredRerunRequest,
    ) -> ProductionConfirmResult:
        source = self.executions.get(tenant_id, project_id, execution_id)
        if source["record_sha256"] != request.expected_execution_sha256:
            raise ProductionExecutionError(
                "ERR_STALE_REVISION",
                "The reviewed production execution changed before the rerun was confirmed.",
            )
        if source["status"] != "completed":
            raise ProductionExecutionError(
                "ERROR_STEERED_RERUN_NOT_ALLOWED",
                "A fachlicher rerun requires one completed candidate execution.",
            )
        run_id = str(source["run_id"])
        step_id = str(source["step_id"])
        new_execution_id = self.executions.execution_id(
            tenant_id,
            project_id,
            run_id,
            request.idempotency_key,
        )
        workflow = self.app.state.local_workflow
        registry = self.app.state.step_agent_registry
        if workflow is None or registry is None or workflow.runtime.hermes_provider is None:
            raise RuntimeProviderError(
                "ERROR_RUNTIME_PROVIDER_BLOCKED",
                "The real Heartweb workflow runtime is unavailable.",
            )
        existing_execution = self.executions.optional(
            tenant_id,
            project_id,
            new_execution_id,
        )
        if existing_execution is not None:
            if existing_execution["status"] != "prepared":
                return self.readback(existing_execution, replay=True)
            prepared, _ = self.executions.reconstruct(
                existing_execution,
                repository_root=self.app.state.repository_root,
                step_agent_registry=registry,
            )
            execution = workflow.runtime.start_agent_dispatch(prepared)
            existing_execution = self.executions.bind_handle(
                existing_execution,
                execution.handle,
                updated_at=self.app.state.clock.now(),
            )
            return self.readback(existing_execution, replay=True)
        run_executions = self.executions.list_for_run(tenant_id, project_id, run_id)
        active = [
            record
            for record in run_executions
            if record["status"] not in {"completed", "failed", "denied"}
        ]
        if active:
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_AMBIGUOUS",
                "Another active production execution already owns this Core run.",
            )

        run = self.repository.run(tenant_id, project_id, run_id)
        if run.get("step_id") != step_id or run.get("status") not in {"awaiting_gate", "in_progress"}:
            raise ProductionExecutionError(
                "ERROR_STEERED_RERUN_NOT_ALLOWED",
                "The Core run must be awaiting review or recovering this exact rerun.",
            )
        run_artifacts = [
            artifact
            for artifact in self.repository.artifacts(tenant_id, project_id)
            if artifact.get("run_id") == run_id
            and artifact.get("step_id") == step_id
        ]
        artifacts = [
            artifact
            for artifact in run_artifacts
            if artifact.get("revision") == run["revision"]
        ]
        gates = [
            gate
            for gate in self.repository.quality_gate_runs(tenant_id, project_id)
            if gate.get("run_id") == run_id
            and gate.get("artifact_revision") == run["revision"]
        ]
        domain_gate = next(
            (gate for gate in gates if gate.get("quality_gate_id") == "qg-domain-contract"),
            None,
        )
        primary_id = domain_gate.get("artifact_id") if isinstance(domain_gate, dict) else None
        primary = next(
            (
                artifact
                for artifact in artifacts
                if artifact.get("artifact_id") == primary_id
                and artifact.get("content_sha256") == request.expected_artifact_sha256
                and artifact.get("revision") == request.expected_artifact_revision
            ),
            None,
        )
        if not isinstance(primary, dict):
            raise ProductionExecutionError(
                "ERR_STALE_REVISION",
                "The reviewed artifact hash or revision is no longer current.",
            )
        if any(
            approval.get("artifact_id") == primary["artifact_id"]
            and approval.get("artifact_sha256") == primary["content_sha256"]
            and approval.get("artifact_revision") == primary["revision"]
            and approval.get("decision") == "approved"
            for approval in self.repository.collection(tenant_id, project_id, "approvals")
        ):
            raise ProductionExecutionError(
                "ERR_APPROVAL_STALE",
                "An approved artifact cannot be rerun as a rejected candidate.",
            )
        revisions = {
            int(artifact["revision"])
            for artifact in self.repository.artifacts(tenant_id, project_id)
            if artifact.get("run_id") == run_id and artifact.get("step_id") == step_id
        }
        failed_steered_attempts = sum(
            1
            for execution in run_executions
            if execution.get("status") == "failed"
            and isinstance(execution.get("dispatch"), Mapping)
            and isinstance(execution["dispatch"].get("steered_rerun"), Mapping)
        )
        attempt_number = max(len(revisions), failed_steered_attempts + 1)
        if attempt_number < 1 or attempt_number > 3:
            raise ProductionExecutionError(
                "ERR_RETRY_EXHAUSTED",
                "The maximum of three fachliche revision attempts is exhausted.",
            )

        seed = _canonical_sha256(
            {
                "source_execution_id": execution_id,
                "source_record_sha256": source["record_sha256"],
                "request": request.model_dump(mode="json"),
            }
        )
        revision_request_id = f"revision-{seed[:24]}"
        steering_id = f"steering-{seed[:24]}"
        existing_revision = self.repository.optional_operator_record(
            tenant_id,
            project_id,
            "revision-request",
            revision_request_id,
        )
        existing_steering = self.repository.optional_operator_record(
            tenant_id,
            project_id,
            "production-steering",
            steering_id,
        )
        if (existing_revision is None) != (existing_steering is None):
            raise ProductionExecutionError(
                "ERROR_PRODUCTION_EXECUTION_RECOVERY_REQUIRED",
                "Steered rerun recovery has only one of its two immutable operator records.",
            )
        if existing_revision is not None and existing_steering is not None:
            if existing_revision.get("requested_at") != existing_steering.get("created_at"):
                raise ProductionExecutionError(
                    "ERR_IDEMPOTENCY_CONFLICT",
                    "Stored rerun records disagree on their immutable timestamp.",
                )
            requested_at = str(existing_steering["created_at"])
        else:
            requested_at = self.app.state.clock.now()
        steering = {
            "steering_id": steering_id,
            "schema_version": "1.0.0",
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_id": run_id,
            "step_id": step_id,
            "revision_request_id": revision_request_id,
            "source_artifact": {
                "artifact_id": primary["artifact_id"],
                "content_sha256": primary["content_sha256"],
                "revision": primary["revision"],
            },
            "findings": list(request.findings),
            "instruction": request.instruction,
            "immutable_constraints": list(request.immutable_constraints),
            "status": "active",
            "created_by": self.app.state.operator_id,
            "created_at": requested_at,
        }
        steering_sha256 = _canonical_sha256(steering)
        revision_request = {
            "revision_request_id": revision_request_id,
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_id": run_id,
            "step_id": step_id,
            "current_artifact_id": primary["artifact_id"],
            "current_content_sha256": primary["content_sha256"],
            "current_revision": primary["revision"],
            "artifact": {
                "artifact_id": primary["artifact_id"],
                "content_sha256": primary["content_sha256"],
                "revision": primary["revision"],
            },
            "affected_sections": list(request.affected_sections),
            "problem": "\n".join(request.findings),
            "expected_result": request.instruction,
            "immutable_constraints": list(request.immutable_constraints),
            "evidence": [
                {
                    "evidence_id": f"evidence-steering-{seed[:16]}",
                    "content_sha256": steering_sha256,
                }
            ],
            "reviewer_feedback": "\n".join(request.findings),
            "attempt_number": attempt_number,
            "status": "open",
            "requested_by": "reviewer-heartweb-admin",
            "requested_at": requested_at,
        }
        schemas = self.app.state.dependencies["record_schemas"]
        _validate_record(schemas["production-steering.schema"], steering, "ERROR_STEERING_INVALID")
        _validate_record(schemas["revision-request.schema"], revision_request, "ERROR_CONTEXT_REVISION_BINDING_INVALID")

        command = {
            "command_id": f"command-revise-{seed[:24]}",
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_id": run_id,
            "expected_revision": run["revision"],
            "idempotency_key": f"idem-revise-{seed[:24]}",
            "operation": "revise",
            "from_step_id": step_id,
            "to_step_id": step_id,
            "input_hash": run["input_hash"],
            "requested_at": requested_at,
        }
        _validate_record(schemas["transition-command.schema"], command, "ERROR_CONTEXT_SCHEMA_INVALID")
        if run["status"] == "in_progress" and (
            existing_revision != revision_request or existing_steering != steering
        ) and not _can_resteer_in_progress(run, run_artifacts, run_executions):
            raise ProductionExecutionError(
                "ERR_IDEMPOTENCY_CONFLICT",
                "An in-progress run cannot be rebound to different steering content.",
            )
        if run["status"] == "in_progress":
            transition = {"ok": True, "run": run, "errors": []}
        else:
            transition = process_transition(
                command=command,
                run=run,
                current_artifact=primary,
                supporting_artifacts=artifacts,
                quality_gate_runs=gates,
                approval=None,
                predecessor_release=None,
                context={},
                registry=self.app.state.dependencies["gate_registry"],
                graph=self.app.state.dependencies["graph"],
            )
            if not transition["ok"]:
                first = transition["errors"][0]
                raise ProductionExecutionError(str(first["code"]), str(first["message"]))
        self.repository.write_operator_record(
            tenant_id,
            project_id,
            "revision-request",
            revision_request,
        )
        self.repository.write_operator_record(
            tenant_id,
            project_id,
            "production-steering",
            steering,
        )
        event = {
            "event_id": f"event-revise-{seed[:24]}",
            "event_type": "run.resumed",
            "schema_version": "2.0.0",
            "occurred_at": requested_at,
            "correlation_id": f"corr-revise-{seed[:24]}",
            "idempotency_key": f"idem-revise-{seed[:24]}",
            "identity": {
                "tenant_id": tenant_id,
                "project_id": project_id,
                "run_id": run_id,
                "step_id": step_id,
                "revision": run["revision"],
            },
            "integration_mode": "live",
            "live_connection_id": "live-heartweb-local",
            "payload": {"resume_request_id": command["command_id"]},
        }
        EventStore.from_repository_root(
            self.app.state.repository_root,
            self.repository.workspace(tenant_id, project_id),
        ).append(event)
        next_run = transition["run"]
        self.repository.write_run(tenant_id, project_id, next_run)

        runtime_request = {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_id": run_id,
            "step_id": step_id,
            "context_package_id": f"context-revision-{seed[:24]}",
            "llm_run_request_id": f"llm-request-revision-{seed[:24]}",
            "llm_run_result_id": f"llm-result-revision-{seed[:24]}",
            "correlation_id": f"correlation-revision-{seed[:24]}",
            "idempotency_key": f"idempotency-revision-{seed[:24]}",
            "actor_id": self.app.state.operator_id,
            "requested_at": requested_at,
            "trigger": "revision",
            "revision_request_id": revision_request_id,
            "steering_id": steering_id,
            "steering_logical_ref": f"operator:steering/{steering_id}",
            "rejected_artifact_id": str(primary["artifact_id"]),
            "rejected_artifact_sha256": str(primary["content_sha256"]),
        }
        prepared = workflow.runtime.prepare_agent_dispatch(
            self.repository,
            self.app.state.repository_root,
            self.app.state.runtime_validator,
            runtime_request,
        )
        rerun = self.executions.create(
            prepared,
            preview_hash=seed,
            idempotency_key=request.idempotency_key,
            created_at=requested_at,
            steered_rerun={
                "source_execution_id": execution_id,
                "source_record_sha256": str(source["record_sha256"]),
                "revision_request_id": revision_request_id,
                "steering_id": steering_id,
                "source_artifact_sha256": str(primary["content_sha256"]),
            },
        )
        execution = workflow.runtime.start_agent_dispatch(prepared)
        rerun = self.executions.bind_handle(
            rerun,
            execution.handle,
            updated_at=self.app.state.clock.now(),
        )
        return self.readback(rerun, replay=False)

    def readback(
        self,
        record: Mapping[str, JsonValue],
        *,
        replay: bool,
    ) -> ProductionConfirmResult:
        tenant_id = str(record["tenant_id"])
        project_id = str(record["project_id"])
        run_id = str(record["run_id"])
        execution_id = str(record["execution_id"])
        interactions = [
            interaction
            for interaction in self.gateway_evidence.list_interactions(tenant_id, project_id, run_id)
            if interaction["interaction_id"] in record["interaction_ids"]
        ]
        return ProductionConfirmResult(
            replay=replay,
            execution_id=execution_id,
            status=str(record["status"]),
            preview_hash=str(record["preview_hash"]),
            readback_urls=(
                f"/v1/tenants/{tenant_id}/projects/{project_id}/production/executions/{execution_id}",
                f"/v1/tenants/{tenant_id}/projects/{project_id}/production/executions/{execution_id}/interactions",
                f"/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}",
                f"/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}/artifacts",
                f"/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}/quality-gates",
            ),
            canonical={
                "execution": _public_execution(record),
                "interactions": interactions,
                "completion": record["completion"],
            },
        )

    def _persist_artifacts(
        self,
        prepared: Any,
        record: Mapping[str, JsonValue],
    ) -> dict[str, JsonValue]:
        assembler = ProductionBundleAssembler(
            repository=self.repository,
            repository_root=self.app.state.repository_root,
            revisions=self.app.state.local_workflow.artifacts.revisions,
            gateway_evidence=self.gateway_evidence,
        )
        assembled = assembler.assemble(
            prepared.provider_outputs,
            llm_run_request_id=str(prepared.llm_request["llm_run_request_id"]),
            actor_id=self.app.state.operator_id,
            decided_at=self.app.state.clock.now(),
        )
        persisted = self.app.state.local_workflow.artifacts.persist(
            prepared.provider_outputs,
            prepared.context_package["package_sha256"],
            assembled.bundle,
            assembled.gate_context,
        )
        current_run = self.repository.run(
            str(record["tenant_id"]),
            str(record["project_id"]),
            str(record["run_id"]),
        )
        artifacts = [
            item
            for item in self.repository.artifacts(str(record["tenant_id"]), str(record["project_id"]))
            if item.get("run_id") == record["run_id"]
            and item.get("revision") == current_run["revision"]
        ]
        gates = [
            item
            for item in self.repository.quality_gate_runs(str(record["tenant_id"]), str(record["project_id"]))
            if item.get("run_id") == record["run_id"]
            and item.get("artifact_revision") == current_run["revision"]
        ]
        return {
            "run": current_run,
            "artifacts": artifacts,
            "quality_gate_runs": gates,
            "artifact_revision": persisted.model_dump(mode="json"),
            "llm_result": prepared.llm_result,
        }


def _public_execution(record: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    dispatch = record["dispatch"]
    if not isinstance(dispatch, dict):
        raise ProductionExecutionError(
            "ERROR_PRODUCTION_EXECUTION_INVALID",
            "Production execution dispatch is unavailable.",
        )
    return {
        "schema_version": record["schema_version"],
        "execution_id": record["execution_id"],
        "tenant_id": record["tenant_id"],
        "project_id": record["project_id"],
        "run_id": record["run_id"],
        "step_id": record["step_id"],
        "expected_revision": record["expected_revision"],
        "status": record["status"],
        "hermes": record["hermes"],
        "interaction_ids": record["interaction_ids"],
        "agent_contract_binding": dispatch["agent_contract_binding"],
        "technical_retry": dispatch.get("technical_retry"),
        "steered_rerun": dispatch.get("steered_rerun"),
        "context_package_id": dispatch["context_package"]["context_package_id"],
        "context_package_sha256": dispatch["context_package"]["package_sha256"],
        "llm_run_request_id": dispatch["llm_request"]["llm_run_request_id"],
        "created_at": record["created_at"],
        "updated_at": record["updated_at"],
        "record_sha256": record["record_sha256"],
        "error": record["error"],
    }


def _validate_record(
    schema: Mapping[str, Any],
    record: Mapping[str, Any],
    code: str,
) -> None:
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record),
        key=lambda item: (tuple(str(part) for part in item.absolute_path), item.message),
    )
    if errors:
        first = errors[0]
        pointer = "/" + "/".join(str(part) for part in first.absolute_path)
        raise ProductionExecutionError(code, f"{pointer}: {first.message}")


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    import hashlib

    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()
