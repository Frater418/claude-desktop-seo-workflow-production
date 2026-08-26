"""FastAPI composition root for the contained local Operator API."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI

from services.runtime_contracts.llm_records import RuntimeContractError, RuntimeContractValidator
from services.agent_gateway.evidence_store import AgentGatewayStore

from .app_dependencies import load_dependencies
from .app_errors import ApiError, register_error_handlers
from .app_routes import register_read_routes
from .artifact_revisions import ArtifactRevisionError
from .clock import Clock, SystemClock
from .command_execution import _operator_record, _transition, register_command_route
from .delivery_admission import DeliveryAdmission
from .delivery_persistence import DeliveryExportRepository
from .delivery_repository import DeliverySnapshotRepository
from .delivery_routes import register_delivery_routes
from .diagnostic_trace_routes import register_diagnostic_trace_routes
from .event_store import EventStoreError
from .intake_project_generator import IntakeProjectGenerator
from .hermes_runtime_provider import HermesRuntimeProvider
from .local_e2e import LocalWorkflowService
from .next_runs import NextRunService
from .package4_routes import register_package4_routes
from .production_routes import register_production_routes
from .production_execution_store import ProductionExecutionStore
from .production_orchestrator import ProductionOrchestrator
from .project_deletion import ProjectDeletionService
from .project_deletion_routes import register_project_deletion_routes
from .provisioning import ProvisionedWorkspaceResolver, WorkspaceProvisioner
from .recovery_inventory import RecoveryInventory
from .repository import ProjectRepository, RepositoryError, WorkspaceRegistry
from .runtime import LocalFixtureProvider, LocalRuntimeService
from .step_agents import StepAgentContractError, load_step_agent_registry


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Injected dependency mode for production and isolated tests."""

    repository_root: Path
    allow_unready: bool = False
    provisioning_root: Path | None = None
    provisioning_enabled: bool = False
    execution_mode: str = "real"
    fixture_provider: LocalFixtureProvider | None = None
    operator_id: str = "operator-heartweb-admin"
    clock: Clock = field(default_factory=SystemClock)
    delivery_admission: DeliveryAdmission | None = None
    diagnostic_root: Path | None = None
    intake_project_generator: IntakeProjectGenerator | None = None
    hermes_runtime_provider: HermesRuntimeProvider | None = None


def create_app(registry: WorkspaceRegistry, repository_root: Path, config: AppConfig | None = None) -> FastAPI:
    """Create the only local HTTP adapter around existing core authorities."""
    effective = config or AppConfig(repository_root)
    resolver = ProvisionedWorkspaceResolver(registry, effective.provisioning_root, effective.provisioning_enabled)
    repository = ProjectRepository(resolver)
    delivery_snapshots = DeliverySnapshotRepository(resolver)
    delivery_exports = DeliveryExportRepository(repository)
    delivery_admission = effective.delivery_admission or DeliveryAdmission()
    app = FastAPI(title="Heartweb Local Operator API", version="1.0.0")
    app.state.repository = repository
    app.state.repository_root = effective.repository_root
    app.state.recovery_inventory = RecoveryInventory(resolver)
    app.state.ready = False
    app.state.projection_rebuild_needed = False
    app.state.execution_mode = effective.execution_mode
    app.state.fixture_provider = effective.fixture_provider
    app.state.operator_id = effective.operator_id
    app.state.clock = effective.clock
    app.state.diagnostic_root = effective.diagnostic_root or effective.repository_root / "var/operator-diagnostics/v1"
    app.state.action_previews = {}
    app.state.intake_previews = {}
    app.state.intake_generations = {}
    app.state.planning_capacity_previews = {}
    app.state.intake_project_generator = effective.intake_project_generator
    app.state.production_previews = {}
    app.state.production_executions = {}
    app.state.production_execution_store = ProductionExecutionStore(repository)
    app.state.project_deletion_service = ProjectDeletionService(
        repository,
        resolver,
        effective.clock,
        effective.operator_id,
    )
    app.state.production_orchestrator = None
    app.state.runtime_validator = None
    app.state.worker_profile = None
    app.state.step_agent_registry = None
    app.state.local_workflow = None
    app.state.dependencies = {}
    try:
        app.state.dependencies = load_dependencies(effective.repository_root, registry)
        app.state.next_runs = NextRunService(repository, app.state.dependencies["graph"], app.state.recovery_inventory)
        if effective.hermes_runtime_provider is not None:
            app.state.runtime_validator = _runtime_validator(effective.repository_root)
            app.state.worker_profile = _json(effective.repository_root / "standards/runtime/operator-worker-profile.json")
            app.state.runtime_validator.assert_valid("worker-profile", app.state.worker_profile)
            app.state.step_agent_registry = load_step_agent_registry(
                effective.repository_root,
                _json(effective.repository_root / "standards/runtime/official-prompt-registry.json"),
            )
            app.state.local_workflow = LocalWorkflowService.from_root(
                repository,
                effective.repository_root,
                LocalRuntimeService(
                    effective.execution_mode,
                    effective.fixture_provider,
                    app.state.recovery_inventory,
                    effective.hermes_runtime_provider,
                    app.state.step_agent_registry,
                ),
                app.state.runtime_validator,
                app.state.worker_profile,
                app.state.dependencies["record_schemas"]["artifact-record.schema"],
                app.state.recovery_inventory,
            )
            if effective.hermes_runtime_provider.customer_root is not None:
                app.state.production_orchestrator = ProductionOrchestrator(
                    app=app,
                    repository=repository,
                    executions=app.state.production_execution_store,
                    gateway_evidence=AgentGatewayStore(
                        customer_root=effective.hermes_runtime_provider.customer_root,
                    ),
                )
        app.state.projection_rebuild_needed = app.state.recovery_inventory.blocked()
        app.state.ready = True
    except (OSError, json.JSONDecodeError, RepositoryError, EventStoreError, RuntimeContractError, StepAgentContractError, ValueError) as exc:
        if not effective.allow_unready:
            raise RuntimeError("Operator API dependencies are unavailable.") from exc
    register_error_handlers(app)
    register_read_routes(app, repository)
    register_project_deletion_routes(app, app.state.project_deletion_service)
    register_package4_routes(app, repository, WorkspaceProvisioner(resolver, effective.repository_root, effective.clock), resolver)
    register_production_routes(app, repository)
    register_delivery_routes(app, delivery_snapshots, delivery_exports, app.state.recovery_inventory, delivery_admission)
    register_diagnostic_trace_routes(app, repository, app.state.diagnostic_root)
    register_command_route(app, repository, registry)
    return app


def _runtime_validator(root: Path) -> RuntimeContractValidator:
    runtime = root / "standards/runtime"
    names = (
        "logical-project-session",
        "official-prompt-registry",
        "worker-profile",
        "context-package",
        "llm-run-request",
        "llm-run-result",
    )
    schemas = {name: _json(runtime / f"{name}.schema.json") for name in names}
    return RuntimeContractValidator(schemas, _json(runtime / "official-prompt-registry.json"))


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected object in {path.name}.")
    return value
