"""FastAPI composition root for the contained local Operator API."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI

from .app_dependencies import load_dependencies
from .app_errors import ApiError, register_error_handlers
from .app_routes import register_read_routes
from .artifact_revisions import ArtifactRevisionError
from .clock import Clock, SystemClock
from .command_execution import _operator_record, _transition, register_command_route
from .event_store import EventStoreError
from .next_runs import NextRunService
from .package4_routes import register_package4_routes
from .provisioning import ProvisionedWorkspaceResolver, WorkspaceProvisioner
from .recovery_inventory import RecoveryInventory
from .repository import ProjectRepository, RepositoryError, WorkspaceRegistry
from .runtime import LocalFixtureProvider


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


def create_app(registry: WorkspaceRegistry, repository_root: Path, config: AppConfig | None = None) -> FastAPI:
    """Create the only local HTTP adapter around existing core authorities."""
    effective = config or AppConfig(repository_root)
    resolver = ProvisionedWorkspaceResolver(registry, effective.provisioning_root, effective.provisioning_enabled)
    repository = ProjectRepository(resolver)
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
    app.state.action_previews = {}
    app.state.intake_previews = {}
    app.state.dependencies = {}
    try:
        app.state.dependencies = load_dependencies(effective.repository_root, registry)
        app.state.next_runs = NextRunService(repository, app.state.dependencies["graph"], app.state.recovery_inventory)
        app.state.projection_rebuild_needed = app.state.recovery_inventory.blocked()
        app.state.ready = True
    except (OSError, json.JSONDecodeError, RepositoryError, EventStoreError, ValueError) as exc:
        if not effective.allow_unready:
            raise RuntimeError("Operator API dependencies are unavailable.") from exc
    register_error_handlers(app)
    register_read_routes(app, repository)
    register_package4_routes(app, repository, WorkspaceProvisioner(resolver, effective.repository_root, effective.clock), resolver)
    register_command_route(app, repository, registry)
    return app
