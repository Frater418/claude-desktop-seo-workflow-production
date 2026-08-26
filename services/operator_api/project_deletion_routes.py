"""Public preview and confirm routes for managed project deletion."""

from __future__ import annotations

from fastapi import FastAPI

from .models import (
    ProjectDeletionConfirmRequest,
    ProjectDeletionPreviewEnvelope,
    ProjectDeletionResultEnvelope,
)
from .project_deletion import ProjectDeletionError, ProjectDeletionService


def register_project_deletion_routes(app: FastAPI, service: ProjectDeletionService) -> None:
    prefix = "/v1/tenants/{tenant_id}/projects/{project_id}/deletion"

    @app.post(
        f"{prefix}/preview",
        response_model=ProjectDeletionPreviewEnvelope,
        operation_id="previewProjectDeletion",
    )
    def preview_project_deletion(tenant_id: str, project_id: str) -> ProjectDeletionPreviewEnvelope:
        _assert_ready(app)
        return ProjectDeletionPreviewEnvelope(data=service.preview(tenant_id, project_id))

    @app.post(
        f"{prefix}/confirm",
        response_model=ProjectDeletionResultEnvelope,
        operation_id="confirmProjectDeletion",
    )
    def confirm_project_deletion(
        tenant_id: str,
        project_id: str,
        body: ProjectDeletionConfirmRequest,
    ) -> ProjectDeletionResultEnvelope:
        _assert_ready(app)
        return ProjectDeletionResultEnvelope(data=service.confirm(tenant_id, project_id, body))


def _assert_ready(app: FastAPI) -> None:
    if not app.state.ready:
        raise ProjectDeletionError(
            "ERROR_PROJECT_DELETE_RECOVERY_REQUIRED",
            "Operator API recovery is pending.",
        )
    app.state.recovery_inventory.authorize()
