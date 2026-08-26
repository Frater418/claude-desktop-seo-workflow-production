"""Explicit preview and confirmation routes for real workflow production."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import FastAPI
from pydantic import JsonValue

from .models import (
    ActionBlocker,
    DataEnvelope,
    ProductionConfirmRequest,
    ProductionConfirmResult,
    ProductionIntent,
    ProductionPreview,
    ProductionSteeredRerunRequest,
    ProductionTechnicalRetryRequest,
    ToolInteractionDecisionRequest,
)
from .package4 import Package4Error
from .event_store import EventStoreError
from .production_execution_store import ProductionExecutionError
from .repository import ProjectRepository, RepositoryError
from .runtime import RuntimeProviderError
from services.agent_gateway.evidence_store import AgentGatewayStoreError


_SUPPORTED_PRODUCTION_STEPS = frozenset(("0", "1", "1b", "1c", "2", "3", "4a", "4b"))


def register_production_routes(app: FastAPI, repository: ProjectRepository) -> None:
    @app.post(
        "/v1/tenants/{tenant_id}/projects/{project_id}/production/preview",
        response_model=ProductionPreview,
        operation_id="previewProductionRun",
    )
    def preview_production_run(
        tenant_id: str,
        project_id: str,
        intent: ProductionIntent,
    ) -> ProductionPreview:
        _assert_route_identity(tenant_id, project_id, intent)
        preview, snapshot = _preview(app, repository, intent)
        app.state.production_previews[preview.preview_hash] = snapshot
        return preview

    @app.post(
        "/v1/tenants/{tenant_id}/projects/{project_id}/production/confirm",
        response_model=ProductionConfirmResult,
        operation_id="confirmProductionRun",
    )
    def confirm_production_run(
        tenant_id: str,
        project_id: str,
        request: ProductionConfirmRequest,
    ) -> ProductionConfirmResult:
        _assert_route_identity(tenant_id, project_id, request.intent)
        preview, current_snapshot = _preview(app, repository, request.intent)
        stored_snapshot = app.state.production_previews.get(request.preview_hash)
        if (
            request.preview_hash != preview.preview_hash
            or stored_snapshot is None
            or stored_snapshot["canonical"] != current_snapshot["canonical"]
        ):
            raise Package4Error(
                "ERR_STALE_REVISION",
                "Die Produktionsvorschau ist nicht mehr aktuell. Bitte Vorschau neu laden.",
            )
        if not preview.allowed:
            blocker = preview.blockers[0]
            raise Package4Error(blocker.code, blocker.message)
        orchestrator = app.state.production_orchestrator
        if orchestrator is None:
            raise Package4Error(
                "ERROR_RUNTIME_PROVIDER_BLOCKED",
                "Die reale Heartweb-Hermes-Runtime ist nicht verfügbar.",
            )
        try:
            return orchestrator.start(request, stored_snapshot)
        except (RuntimeProviderError, ProductionExecutionError, AgentGatewayStoreError) as error:
            raise Package4Error(error.code, error.message) from error

    @app.get(
        "/v1/tenants/{tenant_id}/projects/{project_id}/production/executions/{execution_id}",
        response_model=ProductionConfirmResult,
        operation_id="getProductionExecution",
    )
    def get_production_execution(
        tenant_id: str,
        project_id: str,
        execution_id: str,
    ) -> ProductionConfirmResult:
        orchestrator = _orchestrator(app)
        try:
            record = app.state.production_execution_store.get(tenant_id, project_id, execution_id)
            return orchestrator.readback(record, replay=True)
        except (RuntimeProviderError, ProductionExecutionError, AgentGatewayStoreError) as error:
            raise Package4Error(error.code, error.message) from error

    @app.get(
        "/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}/production/execution",
        response_model=ProductionConfirmResult,
        operation_id="getActiveProductionExecution",
    )
    def get_active_production_execution(
        tenant_id: str,
        project_id: str,
        run_id: str,
    ) -> ProductionConfirmResult:
        orchestrator = _orchestrator(app)
        try:
            active = tuple(
                record
                for record in app.state.production_execution_store.list_for_run(tenant_id, project_id, run_id)
                if record["status"] not in {"completed", "failed", "denied"}
            )
            if not active:
                raise ProductionExecutionError(
                    "ERROR_PRODUCTION_EXECUTION_NOT_FOUND",
                    "No active production execution exists for this run.",
                )
            if len(active) != 1:
                raise ProductionExecutionError(
                    "ERROR_PRODUCTION_EXECUTION_AMBIGUOUS",
                    "More than one active production execution exists for this run.",
                )
            return orchestrator.readback(active[0], replay=True)
        except (RuntimeProviderError, ProductionExecutionError, AgentGatewayStoreError) as error:
            raise Package4Error(error.code, error.message) from error

    @app.get(
        "/v1/tenants/{tenant_id}/projects/{project_id}/runs/{run_id}/production/latest-execution",
        response_model=ProductionConfirmResult,
        operation_id="getLatestProductionExecution",
    )
    def get_latest_production_execution(
        tenant_id: str,
        project_id: str,
        run_id: str,
    ) -> ProductionConfirmResult:
        try:
            records = app.state.production_execution_store.list_for_run(tenant_id, project_id, run_id)
            if not records:
                raise ProductionExecutionError(
                    "ERROR_PRODUCTION_EXECUTION_NOT_FOUND",
                    "No production execution exists for this run.",
                )
            latest = max(records, key=lambda record: (str(record["updated_at"]), str(record["execution_id"])))
            return _orchestrator(app).readback(latest, replay=True)
        except (RuntimeProviderError, ProductionExecutionError, AgentGatewayStoreError) as error:
            raise Package4Error(error.code, error.message) from error

    @app.post(
        "/v1/tenants/{tenant_id}/projects/{project_id}/production/executions/{execution_id}/refresh",
        response_model=ProductionConfirmResult,
        operation_id="refreshProductionExecution",
    )
    def refresh_production_execution(
        tenant_id: str,
        project_id: str,
        execution_id: str,
    ) -> ProductionConfirmResult:
        try:
            return _orchestrator(app).refresh(tenant_id, project_id, execution_id)
        except (RuntimeProviderError, ProductionExecutionError, AgentGatewayStoreError) as error:
            raise Package4Error(error.code, error.message) from error

    @app.post(
        "/v1/tenants/{tenant_id}/projects/{project_id}/production/executions/{execution_id}/technical-retry",
        response_model=ProductionConfirmResult,
        operation_id="retryProductionExecutionTechnically",
    )
    def retry_production_execution_technically(
        tenant_id: str,
        project_id: str,
        execution_id: str,
        request: ProductionTechnicalRetryRequest,
    ) -> ProductionConfirmResult:
        try:
            return _orchestrator(app).technical_retry(
                tenant_id,
                project_id,
                execution_id,
                request,
            )
        except (RuntimeProviderError, ProductionExecutionError, AgentGatewayStoreError) as error:
            raise Package4Error(error.code, error.message) from error

    @app.post(
        "/v1/tenants/{tenant_id}/projects/{project_id}/production/executions/{execution_id}/steered-rerun",
        response_model=ProductionConfirmResult,
        operation_id="rerunProductionExecutionWithSteering",
    )
    def rerun_production_execution_with_steering(
        tenant_id: str,
        project_id: str,
        execution_id: str,
        request: ProductionSteeredRerunRequest,
    ) -> ProductionConfirmResult:
        try:
            return _orchestrator(app).steered_rerun(
                tenant_id,
                project_id,
                execution_id,
                request,
            )
        except (
            RuntimeProviderError,
            ProductionExecutionError,
            AgentGatewayStoreError,
            RepositoryError,
            EventStoreError,
        ) as error:
            raise Package4Error(error.code, error.message) from error

    @app.get(
        "/v1/tenants/{tenant_id}/projects/{project_id}/production/executions/{execution_id}/interactions",
        response_model=DataEnvelope,
        operation_id="listProductionInteractions",
    )
    def list_production_interactions(
        tenant_id: str,
        project_id: str,
        execution_id: str,
    ) -> DataEnvelope:
        result = get_production_execution(tenant_id, project_id, execution_id)
        return DataEnvelope(data=result.canonical["interactions"])

    @app.post(
        "/v1/tenants/{tenant_id}/projects/{project_id}/production/executions/{execution_id}/interactions/{interaction_id}/decision",
        response_model=ProductionConfirmResult,
        operation_id="decideProductionInteraction",
    )
    def decide_production_interaction(
        tenant_id: str,
        project_id: str,
        execution_id: str,
        interaction_id: str,
        request: ToolInteractionDecisionRequest,
    ) -> ProductionConfirmResult:
        try:
            return _orchestrator(app).decide(
                tenant_id,
                project_id,
                execution_id,
                interaction_id,
                request,
            )
        except (RuntimeProviderError, ProductionExecutionError, AgentGatewayStoreError) as error:
            raise Package4Error(error.code, error.message) from error


def _preview(
    app: FastAPI,
    repository: ProjectRepository,
    intent: ProductionIntent,
) -> tuple[ProductionPreview, dict[str, Any]]:
    run = repository.run(intent.tenant_id, intent.project_id, intent.run_id)
    artifacts = [
        item
        for item in repository.artifacts(intent.tenant_id, intent.project_id)
        if item.get("run_id") == intent.run_id
    ]
    blockers: list[ActionBlocker] = []

    if run.get("step_id") != intent.step_id:
        blockers.append(_blocker("ERROR_PRODUCTION_RUN_MISMATCH", "Der Run gehört nicht zum angezeigten Schritt.", "Projektablauf neu laden."))
    if run.get("revision") != intent.expected_revision:
        blockers.append(_blocker("ERR_STALE_REVISION", "Die Run-Revision hat sich geändert.", "Produktionsvorschau neu laden."))
    if run.get("status") != "in_progress":
        blockers.append(_blocker("ERROR_PRODUCTION_STATE_INVALID", "Die Produktion kann nur für einen gestarteten Schritt ausgeführt werden.", "Den Schritt zuerst über die sichtbare Startaktion starten."))
    if artifacts:
        blockers.append(_blocker("ERROR_PRODUCTION_RESULT_EXISTS", "Für diesen Run existiert bereits ein unveränderliches Ergebnis.", "Das vorhandene Ergebnis prüfen und zur Freigabe einreichen."))
    if app.state.execution_mode != "real" or app.state.production_orchestrator is None:
        blockers.append(_blocker("ERROR_RUNTIME_PROVIDER_BLOCKED", "Die reale Heartweb-Hermes-Runtime ist nicht verfügbar.", "Console vollständig schließen und über die Heartweb-Verknüpfung neu starten. Bleibt der Fehler bestehen, Runtime-Konfiguration prüfen."))
    if intent.step_id not in _SUPPORTED_PRODUCTION_STEPS:
        blockers.append(_unsupported_step_blocker(intent.step_id))

    canonical: dict[str, JsonValue] = {
        "intent": intent.model_dump(mode="json"),
        "run": run,
        "artifacts": artifacts,
        "execution_mode": app.state.execution_mode,
        "production_contract_version": "1.0.0",
    }
    preview_hash = hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    consequence: dict[str, JsonValue] = {
        "title": f"Schritt {intent.step_id} wirklich produzieren",
        "summary": "Heartweb startet einen realen Hermes-Lauf, validiert das Ergebnis und speichert nur ein vertragskonformes Artefakt.",
        "cost_notice": "Der bestätigte Lauf kann Modell- oder Providerkosten verursachen.",
        "next_state": "Ergebnis liegt zur Maschinenprüfung und anschließenden Operatorprüfung bereit.",
    }
    snapshot = {
        "canonical": canonical,
        "requested_at": app.state.clock.now(),
    }
    return ProductionPreview(
        intent=intent,
        allowed=not blockers,
        blockers=tuple(blockers),
        consequence=consequence,
        preview_hash=preview_hash,
    ), snapshot


def _assert_route_identity(tenant_id: str, project_id: str, intent: ProductionIntent) -> None:
    if intent.tenant_id != tenant_id or intent.project_id != project_id:
        raise Package4Error("ERR_TENANT_ISOLATION", "Die Produktionsidentität stimmt nicht mit dem geöffneten Projekt überein.")


def _orchestrator(app: FastAPI) -> Any:
    orchestrator = app.state.production_orchestrator
    if orchestrator is None:
        raise Package4Error(
            "ERROR_RUNTIME_PROVIDER_BLOCKED",
            "Die reale Heartweb-Hermes-Runtime ist nicht verfügbar.",
        )
    return orchestrator


def _blocker(code: str, message: str, remediation: str) -> ActionBlocker:
    return ActionBlocker(code=code, message=message, remediation=remediation)


def _unsupported_step_blocker(step_id: str) -> ActionBlocker:
    return _blocker(
        "ERROR_PRODUCTION_STEP_UNSUPPORTED",
        f"Schritt {step_id} ist nicht Teil der aktiven Heartweb-Produktionssequenz.",
        "Die aktive Step-Agent-Registry und den kanonischen Workflowgraphen prüfen.",
    )
