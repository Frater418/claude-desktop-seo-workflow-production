"""Controlled Heartweb MCP tools for specialized production agents."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import BaseModel

ROOT = Path(os.environ.get("HEARTWEB_REPOSITORY_ROOT", Path(__file__).resolve().parents[2])).resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import mcp as mcp_sdk  # noqa: E402

local_mcp_path = str(ROOT / "mcp")
if local_mcp_path not in mcp_sdk.__path__:
    mcp_sdk.__path__.append(local_mcp_path)

from mcp.tools.validate_schema_jsonld import validate_text  # noqa: E402
from services.agent_gateway.evidence_store import (  # noqa: E402
    AgentGatewayStore,
    AgentGatewayStoreError,
    scope_operation_binding,
)
from services.agent_gateway.kickoff_preflight import (  # noqa: E402
    KickoffPreflightError,
    build_kickoff_preflight,
)
from services.agentseo_gateway.core import AgentSEOAdapterError, load_provider_target  # noqa: E402
from services.provider_gateway.agentseo_dispatcher import (  # noqa: E402
    AgentSEODispatchContext,
    AgentSEODispatchError,
    AgentSEODispatcher,
)
from services.provider_gateway.core import ProviderGatewayError  # noqa: E402
from services.deterministic_output_fields import canonical_sha256  # noqa: E402
from services.staging_readiness import LocalStagingReadinessError, local_staging_readiness  # noqa: E402
from services.operator_api.provisioning import ProvisionedWorkspaceResolver  # noqa: E402
from services.operator_api.repository import ProjectRepository, RepositoryError, WorkspaceRegistry  # noqa: E402
from services.operator_api.step_agents import StepAgentContractError, load_step_agent_registry  # noqa: E402
from services.quality_gate_runner.screaming_frog import QualityGateError, run_crawl  # noqa: E402
from services.step3_preflight.solver_bridge import SolverBridgeError, derive_step3_plan_fields  # noqa: E402


server = MCPServer("heartweb-agent-gateway", version="1.0.0")


class ToolAuthorizationResponse(BaseModel):
    model_config = {"extra": "forbid"}

    approved: bool = True


def _store() -> AgentGatewayStore:
    return AgentGatewayStore.from_environment()


def _repository(store: AgentGatewayStore) -> ProjectRepository:
    resolver = ProvisionedWorkspaceResolver(WorkspaceRegistry(()), store.customer_root, True)
    return ProjectRepository(resolver)


def _project(store: AgentGatewayStore, tenant_id: str, project_id: str) -> dict[str, Any]:
    return _repository(store).project_v2(tenant_id, project_id)


def _deployment(project: Mapping[str, Any], deployment_id: str) -> dict[str, Any]:
    deployments = project.get("market_deployments")
    if not isinstance(deployments, list):
        raise AgentGatewayStoreError("ERROR_DEPLOYMENT_MISSING", "Project V2 has no market deployments.")
    matches = [row for row in deployments if isinstance(row, dict) and row.get("deployment_id") == deployment_id]
    if len(matches) != 1:
        raise AgentGatewayStoreError(
            "ERROR_DEPLOYMENT_MISSING",
            "The exact active Project V2 deployment is unavailable or ambiguous.",
        )
    deployment = matches[0]
    if deployment.get("market_phase") != "active":
        raise AgentGatewayStoreError(
            "ERROR_DEPLOYMENT_NOT_ACTIVE",
            "Provider tools require an active market deployment.",
        )
    verification = deployment.get("provider_location_verification")
    if not isinstance(verification, dict) or verification.get("status") != "verified":
        raise AgentGatewayStoreError(
            "ERROR_LOCATION_UNVERIFIED",
            "Provider tools require a verified deployment location code.",
        )
    return deployment


def _target(deployment: Mapping[str, Any]) -> dict[str, Any]:
    verification = deployment["provider_location_verification"]
    target = load_provider_target(
        str(verification["target_id"]),
        ROOT / "standards/domain/provider-location-registry.json",
    )
    expected = {
        "status": "verified",
        "provider_id": target["provider_id"],
        "target_id": target["target_id"],
        "target_type": target["target_type"],
        "location_name": target["location_name"],
        "provider_location_code": target["location_code"],
        "verified_at": target["verified_at"],
        "verification_source": target["verification_source"],
    }
    if (
        verification != expected
        or target["country"] != deployment["country_code"]
        or deployment["language"] not in target["languages"]
        or (
            deployment["seo_operating_model"] in {"local", "regional", "programmatic_local"}
            and target["target_type"] == "country"
        )
    ):
        raise AgentGatewayStoreError(
            "ERROR_LOCATION_BINDING_MISMATCH",
            "Project V2 market, language, operating model and persisted provider target do not match the registry.",
        )
    return {
        "provider_id": target["provider_id"],
        "target_id": target["target_id"],
        "target_type": target["target_type"],
        "country": target["country"],
        "location_name": target["location_name"],
        "location_code": target["location_code"],
        "language": deployment["language"],
    }


def _run_bound_deployment(
    store: AgentGatewayStore,
    tenant_id: str,
    project_id: str,
    run_id: str,
    deployment_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    repository = _repository(store)
    project = repository.project_v2(tenant_id, project_id)
    run = repository.run(tenant_id, project_id, run_id)
    bound_deployment_id = run.get("deployment_id")
    if bound_deployment_id is None:
        deployments = project.get("market_deployments")
        primary = [
            row
            for row in deployments
            if isinstance(row, dict)
            and row.get("market_phase") == "active"
            and row.get("deployment_role") == "primary"
        ] if isinstance(deployments, list) else []
        if len(primary) != 1:
            raise AgentGatewayStoreError(
                "ERROR_RUN_DEPLOYMENT_UNBOUND",
                "A legacy run without deployment_id requires exactly one active primary deployment.",
            )
        bound_deployment_id = primary[0]["deployment_id"]
    if bound_deployment_id != deployment_id:
        raise AgentGatewayStoreError(
            "ERROR_RUN_DEPLOYMENT_MISMATCH",
            "The requested deployment_id differs from the canonical run deployment binding.",
        )
    return project, _deployment(project, deployment_id)


def _operation_binding(
    store: AgentGatewayStore,
    tenant_id: str,
    project_id: str,
    run_id: str,
    llm_run_request_id: str,
    operation_id: str,
) -> dict[str, Any]:
    repository = _repository(store)
    run = repository.run(tenant_id, project_id, run_id)
    step_id = run.get("step_id")
    if not isinstance(step_id, str) or run.get("status") != "in_progress":
        raise AgentGatewayStoreError(
            "ERROR_AGENT_RUN_NOT_ACTIVE",
            "A controlled tool can run only for the matching in-progress canonical Heartweb run.",
        )
    registry_document = _json_object(ROOT / "standards/runtime/step-agent-registry.json")
    prompt_registry = _json_object(ROOT / "standards/runtime/official-prompt-registry.json")
    contract = load_step_agent_registry(ROOT, prompt_registry).for_step(step_id)
    matches = [operation for operation in contract.allowed_operations if operation["operation_id"] == operation_id]
    if len(matches) != 1:
        raise AgentGatewayStoreError(
            "ERROR_AGENT_OPERATION_NOT_ALLOWED",
            "The requested tool operation is not allowed for the canonical run Step.",
        )
    operation = dict(matches[0])
    target_revision = int(run["revision"]) + 1
    expected_tool_name = f"mcp__heartweb__{operation_id}"
    if operation["tool_name"] != expected_tool_name:
        raise AgentGatewayStoreError(
            "ERROR_AGENT_TOOL_IDENTITY_INVALID",
            "The registered MCP tool name does not match the controlled Heartweb server namespace.",
        )
    binding = {
        "schema_version": "1.1.0",
        "registry_id": registry_document["registry_id"],
        "registry_version": registry_document["registry_version"],
        "registry_sha256": registry_document["registry_sha256"],
        "step_id": step_id,
        "target_revision": target_revision,
        "agent_contract_id": contract.entry["agent_contract_id"],
        "agent_contract_version": contract.entry["agent_contract_version"],
        "worker_profile_id": contract.worker_profile["worker_profile_id"],
        "worker_profile_version": contract.worker_profile["profile_version"],
        "worker_profile_sha256": contract.worker_profile["profile_sha256"],
        "tool_policy_id": contract.tool_policy["tool_policy_id"],
        "tool_policy_version": contract.tool_policy["policy_version"],
        "tool_policy_sha256": contract.tool_policy["policy_sha256"],
        **operation,
    }
    return scope_operation_binding(
        binding,
        llm_run_request_id=llm_run_request_id,
        evidence_records=store.list_evidence(tenant_id, project_id, run_id),
    )


def _local_operation_binding(
    store: AgentGatewayStore,
    tenant_id: str,
    project_id: str,
    run_id: str,
    llm_run_request_id: str,
    operation_id: str,
) -> dict[str, Any]:
    binding = _operation_binding(store, tenant_id, project_id, run_id, llm_run_request_id, operation_id)
    if binding["confirmation_scope"] != "none" or binding["cost_mode"] != "none":
        raise AgentGatewayStoreError(
            "ERROR_AGENT_TOOL_CONFIRMATION_REQUIRED",
            "This operation requires the exact external authorization path.",
        )
    return binding


def _provider_dispatcher() -> AgentSEODispatcher:
    api_key = (os.environ.get("AGENTSEO_API_KEY") or os.environ.get("MCP_AGENTSEO_API_KEY") or "").strip()
    if not api_key:
        raise AgentGatewayStoreError(
            "ERROR_AGENTSEO_API_KEY_MISSING",
            "The Provider Gateway process has no AgentSEO credential alias.",
        )
    return AgentSEODispatcher(ROOT, api_key)


def _provider_context(
    store: AgentGatewayStore,
    tenant_id: str,
    project_id: str,
    run_id: str,
    deployment_id: str,
    authorization: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> AgentSEODispatchContext:
    repository = _repository(store)
    run = repository.run(tenant_id, project_id, run_id)
    releases = [
        release
        for release in repository.releases(tenant_id, project_id)
        if release.get("status") == "released"
        and release.get("artifact_sha256") == run.get("input_hash")
    ]
    if len(releases) != 1:
        raise AgentGatewayStoreError(
            "ERROR_PREDECESSOR_RELEASE_MISSING",
            "Provider dispatch requires exactly one released predecessor bound to the run input hash.",
        )
    maximum_items = binding.get("max_items")
    if not isinstance(maximum_items, int) or isinstance(maximum_items, bool) or maximum_items < 1:
        raise AgentGatewayStoreError(
            "ERROR_AGENT_TOOL_ITEM_POLICY_INVALID",
            "Provider dispatch requires a positive versioned operation item limit.",
        )
    return AgentSEODispatchContext(
        run_id=run_id,
        project_id=project_id,
        deployment_id=deployment_id,
        revision=int(run["revision"]) + 1,
        source_artifact_ids=(str(releases[0]["artifact_id"]),),
        authorization_id=str(authorization["interaction_id"]),
        maximum_calls=maximum_items,
        maximum_items=maximum_items,
    )


def _json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AgentGatewayStoreError(
            "ERROR_AGENT_CONTRACT_UNREADABLE",
            "A versioned agent contract could not be read as JSON.",
        ) from error
    if not isinstance(value, dict):
        raise AgentGatewayStoreError(
            "ERROR_AGENT_CONTRACT_UNREADABLE",
            "A versioned agent contract must be a JSON object.",
        )
    return value


def _external_authorization(
    *,
    store: AgentGatewayStore,
    tenant_id: str,
    project_id: str,
    run_id: str,
    llm_run_request_id: str,
    operation_id: str,
    request_payload: Mapping[str, Any],
    maximum_cost_usd: float | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    binding = _operation_binding(store, tenant_id, project_id, run_id, llm_run_request_id, operation_id)
    confirmation_scope = binding["confirmation_scope"]
    cost_mode = binding["cost_mode"]
    if confirmation_scope == "none":
        raise AgentGatewayStoreError(
            "ERROR_AGENT_TOOL_CONFIRMATION_POLICY_INVALID",
            "External authorization cannot be requested for a no-confirmation operation.",
        )
    if cost_mode == "none" and maximum_cost_usd is not None:
        raise AgentGatewayStoreError(
            "ERROR_AGENT_TOOL_COST_POLICY_INVALID",
            "A no-cost operation cannot request an operator cost cap.",
        )
    if cost_mode == "bounded":
        if not isinstance(maximum_cost_usd, int | float) or isinstance(maximum_cost_usd, bool) or maximum_cost_usd <= 0:
            raise AgentGatewayStoreError(
                "ERROR_AGENT_TOOL_COST_POLICY_INVALID",
                "A cost-bearing provider request requires a positive exact operator cost cap.",
            )
        policy_cap = binding.get("max_cost_usd")
        if isinstance(policy_cap, int | float) and maximum_cost_usd > policy_cap:
            raise AgentGatewayStoreError(
                "ERROR_AGENT_TOOL_COST_POLICY_INVALID",
                "The requested operator cost cap exceeds the versioned Tool Policy maximum.",
            )
    if cost_mode in {"unknown_blocked", "provider_credits_unreported"} and maximum_cost_usd is not None:
        raise AgentGatewayStoreError(
            "ERROR_AGENT_TOOL_COST_POLICY_INVALID",
            "Provider-managed credits do not accept an invented USD cost cap.",
        )
    if cost_mode in {"bounded", "unknown_blocked", "provider_credits_unreported"} and not isinstance(binding.get("provider_id"), str):
        raise AgentGatewayStoreError(
            "ERROR_AGENT_TOOL_PROVIDER_POLICY_INVALID",
            "A provider operation requires a versioned provider identity.",
        )
    idempotency_key = "tool-idem-" + _sha256(
        {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_id": run_id,
            "llm_run_request_id": llm_run_request_id,
            "operation_id": operation_id,
            "tool_policy_sha256": binding["tool_policy_sha256"],
            "request": dict(request_payload),
        }
    )[:32]
    authorization = store.request_authorization(
        tenant_id=tenant_id,
        project_id=project_id,
        run_id=run_id,
        operation_id=operation_id,
        operation_binding=binding,
        idempotency_key=idempotency_key,
        confirmation_scope=confirmation_scope,
        cost_mode=cost_mode,
        maximum_cost_usd=maximum_cost_usd,
        request_payload=request_payload,
    )
    return authorization, binding


async def _elicited_authorization(
    ctx: Context,
    store: AgentGatewayStore,
    authorization: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    preview = {
        "interaction_id": authorization["interaction_id"],
        "run_id": authorization["run_id"],
        "step_id": binding["step_id"],
        "operation_id": authorization["operation_id"],
        "tool_name": binding["tool_name"],
        "provider_id": binding.get("provider_id"),
        "confirmation_scope": authorization["confirmation_scope"],
        "cost_mode": authorization["cost_mode"],
        "maximum_cost_usd": authorization.get("maximum_cost_usd"),
        "request_sha256": authorization["request_sha256"],
        "idempotency_key": authorization["idempotency_key"],
        "parameters": authorization["request"],
    }
    elicitation = await ctx.elicit(
        "Heartweb requires an exact operator decision for this tool request:\n"
        + json.dumps(preview, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        ToolAuthorizationResponse,
    )
    hermes_approved = (
        elicitation.action == "accept"
        and elicitation.data is not None
        and elicitation.data.approved is True
    )
    current = store.interaction(
        str(authorization["tenant_id"]),
        str(authorization["project_id"]),
        str(authorization["run_id"]),
        str(authorization["interaction_id"]),
    )
    heartweb_approved = current["status"] == "approved"
    if hermes_approved != heartweb_approved:
        raise AgentGatewayStoreError(
            "ERROR_TOOL_AUTHORIZATION_MISMATCH",
            "Hermes approval and the immutable Heartweb operator decision differ.",
        )
    if not hermes_approved:
        if current["status"] == "denied":
            raise AgentGatewayStoreError(
                "ERROR_TOOL_AUTHORIZATION_DENIED",
                "The operator denied the exact external tool request.",
            )
        raise AgentGatewayStoreError(
            "ERROR_TOOL_AUTHORIZATION_CANCELLED",
            "The Hermes tool interaction ended without a matching Heartweb decision.",
        )
    return current


def _failure(error: Exception) -> dict[str, Any]:
    if isinstance(error, (AgentGatewayStoreError, AgentSEOAdapterError, AgentSEODispatchError, QualityGateError, KickoffPreflightError)):
        return {
            "status": "failed",
            "error": {
                "code": error.code,
                "message": error.message,
                "remediation": getattr(error, "remediation", None),
                "details": getattr(error, "details", None),
            },
        }
    if isinstance(error, SolverBridgeError):
        return {"status": "failed", "error": {"code": str(error), "message": "The deterministic Step 3 solver rejected its input."}}
    if isinstance(error, RepositoryError):
        return {"status": "failed", "error": {"code": error.code, "message": error.message}}
    if isinstance(error, StepAgentContractError):
        return {
            "status": "failed",
            "error": {"code": error.code, "message": error.message, "remediation": error.remediation},
        }
    if isinstance(error, ProviderGatewayError):
        return {
            "status": "failed",
            "error": {
                "code": error.code,
                "message": str(error),
                "details": {"violations": list(error.violations)},
            },
        }
    return {
        "status": "failed",
        "error": {
            "code": "ERROR_AGENT_GATEWAY_INTERNAL",
            "message": "The controlled Heartweb tool failed without a valid result.",
        },
    }


def _persist(
    store: AgentGatewayStore,
    *,
    tenant_id: str,
    project_id: str,
    run_id: str,
    operation_id: str,
    evidence_kind: str,
    operation_binding: Mapping[str, Any],
    request_payload: Mapping[str, Any],
    result_payload: Mapping[str, Any],
) -> dict[str, Any]:
    evidence = store.persist_evidence(
        tenant_id=tenant_id,
        project_id=project_id,
        run_id=run_id,
        operation_id=operation_id,
        evidence_kind=evidence_kind,
        operation_binding=operation_binding,
        request_payload=request_payload,
        result_payload=result_payload,
    )
    return {
        "status": "completed",
        "evidence": evidence,
        "evidence_ref": {
            field: evidence[field]
            for field in ("evidence_id", "operation_id", "logical_ref", "content_sha256")
        },
    }


@server.tool()
def prepare_kickoff_preflight(
    tenant_id: str,
    project_id: str,
    run_id: str,
    llm_run_request_id: str,
    deployment_id: str,
) -> dict[str, Any]:
    """Prepare deterministic Step 0 location, artifact-path and competitor URL Evidence."""
    operation_id = "prepare_kickoff_preflight"
    try:
        store = _store()
        repository = _repository(store)
        binding = _local_operation_binding(
            store,
            tenant_id,
            project_id,
            run_id,
            llm_run_request_id,
            operation_id,
        )
        project, _ = _run_bound_deployment(
            store,
            tenant_id,
            project_id,
            run_id,
            deployment_id,
        )
        intake = repository.intake(tenant_id, project_id)
        result = build_kickoff_preflight(
            project_v2=project,
            accepted_intake=intake,
            deployment_id=deployment_id,
            location_table_path=ROOT / "standards/domain/provider-location-registry.json",
            manifest_schema_path=ROOT / "standards/manifest-v2.schema.json",
        )
        return _persist(
            store,
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            operation_id=operation_id,
            evidence_kind="kickoff_preflight",
            operation_binding=binding,
            request_payload={
                "deployment_id": deployment_id,
                "intake_source_sha256": intake["source_sha256"],
            },
            result_payload=result,
        )
    except Exception as error:
        return _failure(error)


@server.tool()
async def run_screaming_frog_crawl(
    tenant_id: str,
    project_id: str,
    run_id: str,
    llm_run_request_id: str,
    deployment_id: str,
    start_url: str,
    ctx: Context,
    url_limit: int = 500,
) -> dict[str, Any]:
    """Run one approved, bounded Screaming Frog crawl for Step 1 and persist typed Evidence."""
    operation_id = "run_screaming_frog_crawl"
    try:
        store = _store()
        project, deployment = _run_bound_deployment(
            store,
            tenant_id,
            project_id,
            run_id,
            deployment_id,
        )
        hosts = {
            row["host"]
            for row in project["entity_domain_gbp"]["domains"]
            if row["domain_id"] in deployment["domain_ids"]
        }
        parsed = urlparse(start_url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in hosts or parsed.path not in {"", "/"}:
            raise AgentGatewayStoreError(
                "ERROR_SCREAMING_FROG_URL_INVALID",
                "The crawl URL must be a root URL for a domain bound to the selected deployment.",
            )
        request_payload = {
            "deployment_id": deployment_id,
            "start_url": start_url,
            "url_limit": url_limit,
        }
        authorization, binding = _external_authorization(
            store=store,
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            llm_run_request_id=llm_run_request_id,
            operation_id=operation_id,
            request_payload=request_payload,
            maximum_cost_usd=None,
        )
        authorization = await _elicited_authorization(ctx, store, authorization, binding)
        workspace = ProvisionedWorkspaceResolver(WorkspaceRegistry(()), store.customer_root, True).resolve(tenant_id, project_id)
        evidence_root = workspace / "v2/operator/evidence" / f"revision-{binding['target_revision']}"
        evidence_root.mkdir(parents=True, exist_ok=True)
        result = run_crawl(
            start_url=start_url,
            evidence_root=evidence_root,
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            deployment_id=deployment_id,
            url_limit=url_limit,
            timeout_seconds=1200,
            policy_step="1",
            multilingual=len(project["market_deployments"]) > 1,
        )
        return _persist(
            store,
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            operation_id=operation_id,
            evidence_kind="screaming_frog_crawl",
            operation_binding=binding,
            request_payload={**request_payload, "authorization_id": authorization["interaction_id"]},
            result_payload=result,
        )
    except Exception as error:
        return _failure(error)


async def _serp_evidence(
    *,
    ctx: Context,
    operation_id: str,
    evidence_kind: str,
    tenant_id: str,
    project_id: str,
    run_id: str,
    llm_run_request_id: str,
    deployment_id: str,
    keyword: str,
    device: str,
) -> dict[str, Any]:
    store = _store()
    _, deployment = _run_bound_deployment(
        store,
        tenant_id,
        project_id,
        run_id,
        deployment_id,
    )
    target = _target(deployment)
    request_payload = {
        "deployment_id": deployment_id,
        "keyword": keyword.strip(),
        "device": device,
        "location_code": target["location_code"],
        "language": target["language"],
        "billing_unit": "credits",
        "provider_usage_reported": False,
    }
    authorization, binding = _external_authorization(
        store=store,
        tenant_id=tenant_id,
        project_id=project_id,
        run_id=run_id,
        llm_run_request_id=llm_run_request_id,
        operation_id=operation_id,
        request_payload=request_payload,
        maximum_cost_usd=None,
    )
    authorization = await _elicited_authorization(ctx, store, authorization, binding)
    result = _provider_dispatcher().serp_analysis(
        context=_provider_context(
            store,
            tenant_id,
            project_id,
            run_id,
            deployment_id,
            authorization,
            binding,
        ),
        keyword=keyword,
        target=target,
        device=device,
    )
    return _persist(
        store,
        tenant_id=tenant_id,
        project_id=project_id,
        run_id=run_id,
        operation_id=operation_id,
        evidence_kind=evidence_kind,
        operation_binding=binding,
        request_payload={**request_payload, "authorization_id": authorization["interaction_id"]},
        result_payload=result,
    )


@server.tool()
async def request_serp_intent_evidence(
    tenant_id: str,
    project_id: str,
    run_id: str,
    llm_run_request_id: str,
    deployment_id: str,
    keyword: str,
    ctx: Context,
    device: str = "desktop",
) -> dict[str, Any]:
    """Request one operator-approved SERP intent analysis for Step 1b."""
    try:
        return await _serp_evidence(
            ctx=ctx,
            operation_id="request_serp_intent_evidence",
            evidence_kind="serp_intent",
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            llm_run_request_id=llm_run_request_id,
            deployment_id=deployment_id,
            keyword=keyword,
            device=device,
        )
    except Exception as error:
        return _failure(error)


@server.tool()
def read_design_evidence(
    tenant_id: str,
    project_id: str,
    run_id: str,
    llm_run_request_id: str,
) -> dict[str, Any]:
    """Read bounded, accepted text design Evidence for Step 1c without guessing from absent screenshots."""
    operation_id = "read_design_evidence"
    try:
        store = _store()
        binding = _local_operation_binding(
            store,
            tenant_id,
            project_id,
            run_id,
            llm_run_request_id,
            operation_id,
        )
        workspace = ProvisionedWorkspaceResolver(WorkspaceRegistry(()), store.customer_root, True).resolve(tenant_id, project_id)
        root = workspace / "v2/operator/design-evidence"
        if not root.exists() or root.is_symlink() or not root.is_dir():
            raise AgentGatewayStoreError(
                "ERROR_DESIGN_EVIDENCE_MISSING",
                "No accepted design Evidence exists for this project.",
            )
        allowed = {".css", ".html", ".json", ".md", ".txt"}
        paths = tuple(path for path in sorted(root.rglob("*")) if path.is_file() and not path.is_symlink())
        if not paths or any(path.suffix.lower() not in allowed for path in paths):
            raise AgentGatewayStoreError(
                "ERROR_DESIGN_EVIDENCE_UNSUPPORTED",
                "Design Evidence must be accepted text tokens, CSS, HTML, JSON, Markdown or text. Binary screenshots require a reviewed extraction first.",
            )
        documents: list[dict[str, Any]] = []
        total = 0
        for path in paths:
            content = path.read_text(encoding="utf-8")
            total += len(content.encode("utf-8"))
            if total > 1_000_000:
                raise AgentGatewayStoreError(
                    "ERROR_DESIGN_EVIDENCE_LIMIT",
                    "Accepted design Evidence exceeds the one-megabyte bounded read limit.",
                )
            documents.append({"path": path.relative_to(root).as_posix(), "content": content})
        request_payload = {"accepted_root": "v2/operator/design-evidence", "document_count": len(documents)}
        return _persist(
            store,
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            operation_id=operation_id,
            evidence_kind="accepted_design_tokens",
            operation_binding=binding,
            request_payload=request_payload,
            result_payload={"documents": documents},
        )
    except Exception as error:
        return _failure(error)


@server.tool()
async def request_keyword_metrics(
    tenant_id: str,
    project_id: str,
    run_id: str,
    llm_run_request_id: str,
    deployment_id: str,
    keywords: list[str],
    ctx: Context,
) -> dict[str, Any]:
    """Request operator-approved, location-bound keyword metrics for Step 2."""
    operation_id = "request_keyword_metrics"
    try:
        store = _store()
        _, deployment = _run_bound_deployment(
            store,
            tenant_id,
            project_id,
            run_id,
            deployment_id,
        )
        target = _target(deployment)
        request_payload = {
            "deployment_id": deployment_id,
            "keywords": keywords,
            "location_code": target["location_code"],
            "language": target["language"],
            "billing_unit": "credits",
            "provider_usage_reported": False,
        }
        authorization, binding = _external_authorization(
            store=store,
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            llm_run_request_id=llm_run_request_id,
            operation_id=operation_id,
            request_payload=request_payload,
            maximum_cost_usd=None,
        )
        authorization = await _elicited_authorization(ctx, store, authorization, binding)
        result = _provider_dispatcher().keyword_metrics(
            context=_provider_context(
                store,
                tenant_id,
                project_id,
                run_id,
                deployment_id,
                authorization,
                binding,
            ),
            keywords=keywords,
            target=target,
        )
        response = _persist(
            store,
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            operation_id=operation_id,
            evidence_kind="keyword_metrics",
            operation_binding=binding,
            request_payload={**request_payload, "authorization_id": authorization["interaction_id"]},
            result_payload=result,
        )
        if result.get("status") != "completed":
            response["status"] = "failed"
            response["error"] = result.get("error")
        return response
    except Exception as error:
        return _failure(error)


@server.tool()
def solve_capacity_matrix(
    tenant_id: str,
    project_id: str,
    run_id: str,
    llm_run_request_id: str,
    step2_candidate: dict[str, Any],
) -> dict[str, Any]:
    """Run the deterministic Step 3 capacity solver and persist its complete machine fields."""
    operation_id = "solve_capacity_matrix"
    try:
        store = _store()
        binding = _local_operation_binding(
            store,
            tenant_id,
            project_id,
            run_id,
            llm_run_request_id,
            operation_id,
        )
        result = derive_step3_plan_fields(step2_candidate)
        return _persist(
            store,
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            operation_id=operation_id,
            evidence_kind="capacity_matrix",
            operation_binding=binding,
            request_payload={"step2_candidate_sha256": _sha256(step2_candidate)},
            result_payload=result,
        )
    except Exception as error:
        return _failure(error)


@server.tool()
async def request_serp_briefing_evidence(
    tenant_id: str,
    project_id: str,
    run_id: str,
    llm_run_request_id: str,
    deployment_id: str,
    keyword: str,
    ctx: Context,
    device: str = "desktop",
) -> dict[str, Any]:
    """Request one operator-approved SERP analysis for a Step 4a Copywriter briefing."""
    try:
        return await _serp_evidence(
            ctx=ctx,
            operation_id="request_serp_briefing_evidence",
            evidence_kind="serp_briefing",
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            llm_run_request_id=llm_run_request_id,
            deployment_id=deployment_id,
            keyword=keyword,
            device=device,
        )
    except Exception as error:
        return _failure(error)


@server.tool()
def validate_jsonld(
    tenant_id: str,
    project_id: str,
    run_id: str,
    llm_run_request_id: str,
    html_or_jsonld: str,
    strict_geo: bool = False,
) -> dict[str, Any]:
    """Validate JSON-LD locally at parse, contract, format and optional GEO levels."""
    operation_id = "validate_jsonld"
    try:
        store = _store()
        binding = _local_operation_binding(
            store,
            tenant_id,
            project_id,
            run_id,
            llm_run_request_id,
            operation_id,
        )
        result = validate_text(html_or_jsonld, strict_geo=strict_geo)
        return _persist(
            store,
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            operation_id=operation_id,
            evidence_kind="jsonld_validation",
            operation_binding=binding,
            request_payload={"content_sha256": _sha256_text(html_or_jsonld), "strict_geo": strict_geo},
            result_payload=result,
        )
    except Exception as error:
        return _failure(error)


@server.tool()
def run_staging_validation(
    tenant_id: str,
    project_id: str,
    run_id: str,
    llm_run_request_id: str,
    page_spec: dict[str, Any],
) -> dict[str, Any]:
    """Run bounded local typed-page readiness simulations and persist four honest reports."""

    operation_id = "run_staging_validation"
    try:
        store = _store()
        binding = _local_operation_binding(
            store,
            tenant_id,
            project_id,
            run_id,
            llm_run_request_id,
            operation_id,
        )
        normalized_page, reports = local_staging_readiness(page_spec, ROOT)
        checks: list[dict[str, Any]] = []
        evidence_refs: list[dict[str, str]] = []
        for report in reports:
            tool = str(report["tool"])
            persisted = _persist(
                store,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
                operation_id=operation_id,
                evidence_kind=f"staging_{tool}_readiness",
                operation_binding=binding,
                request_payload={"page_spec_sha256": canonical_sha256(page_spec), "tool": tool},
                result_payload=report,
            )
            evidence_ref = dict(persisted["evidence_ref"])
            evidence_refs.append(evidence_ref)
            checks.append(
                {
                    "tool": tool,
                    "evidence_id": evidence_ref["evidence_id"],
                    "report_sha256": evidence_ref["content_sha256"],
                    "provenance": {
                        "classification": report["classification"],
                        "source": report["source"],
                    },
                }
            )
        normalized_page["accessibility"]["axe_evidence_id"] = next(check["evidence_id"] for check in checks if check["tool"] == "axe")
        normalized_page["responsive"]["visual_evidence_id"] = next(check["evidence_id"] for check in checks if check["tool"] == "visual")
        normalized_page.pop("content_sha256", None)
        normalized_page["jsonld"].pop("graph_hash", None)
        return {
            "status": "completed",
            "normalized_page_spec": normalized_page,
            "checks": checks,
            "evidence_refs": evidence_refs,
            "provenance_classification": "local_simulated",
        }
    except LocalStagingReadinessError as error:
        return {"status": "failed", "error": {"code": error.code, "message": error.message}}
    except Exception as error:
        return _failure(error)


def _sha256(value: Mapping[str, Any]) -> str:
    return _sha256_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    server.run(transport="stdio")
