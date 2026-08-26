from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.domain_contract.validator import validate_project

from .models import JsonValue
from .project_source_revision import ProjectSourceRevisionError, build_logical_session_revision
from .repository import ProjectRepository, RepositoryError


@dataclass(frozen=True, slots=True)
class PlanningCapacityError(RuntimeError):
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


@dataclass(frozen=True, slots=True)
class PlanningCapacityPreview:
    tenant_id: str
    project_id: str
    current_project_sha256: str
    proposed_project_sha256: str
    preview_hash: str
    capacity: dict[str, JsonValue]
    project_v2: dict[str, JsonValue]
    intake: dict[str, JsonValue]
    logical_session: dict[str, JsonValue]
    run_id: str
    deployment_id: str
    changed: bool

    def public(self) -> dict[str, JsonValue]:
        return {
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "current_project_sha256": self.current_project_sha256,
            "proposed_project_sha256": self.proposed_project_sha256,
            "preview_hash": self.preview_hash,
            "capacity": self.capacity,
            "run_id": self.run_id,
            "deployment_id": self.deployment_id,
            "changed": self.changed,
        }


class PlanningCapacityService:
    def __init__(self, repository: ProjectRepository, repository_root: Path) -> None:
        self._repository = repository
        self._repository_root = repository_root

    def preview(
        self,
        tenant_id: str,
        project_id: str,
        *,
        minimum: float,
        maximum: float,
        actor_id: str,
        confirmed_at: str,
    ) -> PlanningCapacityPreview:
        if minimum < 0 or maximum < minimum or maximum > 168:
            raise PlanningCapacityError(
                "ERROR_PLANNING_CAPACITY_INVALID",
                "Weekly capacity requires 0 <= minimum <= maximum <= 168.",
            )
        current = self._repository.project_v2(tenant_id, project_id)
        intake = self._repository.intake(tenant_id, project_id)
        reviewed = intake.get("reviewed")
        if not isinstance(reviewed, dict) or reviewed.get("project_v2") != current:
            raise PlanningCapacityError(
                "ERROR_CONTEXT_SOURCE_INVALID",
                "Accepted intake and canonical Project V2 are not identical before capacity confirmation.",
            )
        proposed = copy.deepcopy(current)
        capacity: dict[str, JsonValue] = {
            "min": minimum,
            "max": maximum,
            "source": "operator_confirmed",
            "provisional": False,
            "confirmed_by": actor_id,
            "confirmed_at": confirmed_at,
        }
        proposed["schema_version"] = "1.3.0"
        proposed["planning_capacity"] = capacity
        validation = validate_project(proposed, root=self._repository_root)
        if not validation["valid"]:
            first = validation["errors"][0] if validation["errors"] else None
            code = first.get("code") if isinstance(first, dict) else "ERROR_DOMAIN_CONTRACT_INVALID"
            raise PlanningCapacityError(
                "ERROR_DOMAIN_CONTRACT_INVALID",
                f"Capacity-bound Project V2 failed domain validation: {code}.",
            )
        upgraded_intake = copy.deepcopy(intake)
        upgraded_reviewed = upgraded_intake.get("reviewed")
        if not isinstance(upgraded_reviewed, dict):
            raise PlanningCapacityError("ERROR_CONTEXT_SOURCE_INVALID", "Accepted intake review is unavailable.")
        upgraded_reviewed["project_v2"] = proposed
        current_run = self._repository.current_run(tenant_id, project_id)
        run = self._repository.run(tenant_id, project_id, current_run.run_id)
        deployment_id = run.get("deployment_id")
        if not isinstance(deployment_id, str):
            deployment_id = _primary_deployment_id(proposed)
        current_sha = _sha256(current)
        proposed_sha = _sha256(proposed)
        preview_payload = {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "current_project_sha256": current_sha,
            "proposed_project_sha256": proposed_sha,
            "capacity": capacity,
            "run_id": current_run.run_id,
            "deployment_id": deployment_id,
        }
        return PlanningCapacityPreview(
            tenant_id=tenant_id,
            project_id=project_id,
            current_project_sha256=current_sha,
            proposed_project_sha256=proposed_sha,
            preview_hash=_sha256(preview_payload),
            capacity=capacity,
            project_v2=proposed,
            intake=upgraded_intake,
            logical_session=self._repository.logical_session(tenant_id, project_id),
            run_id=current_run.run_id,
            deployment_id=deployment_id,
            changed=current_sha != proposed_sha,
        )

    def apply(
        self,
        preview: PlanningCapacityPreview,
        *,
        idempotency_key: str,
        confirmed: bool,
    ) -> dict[str, JsonValue]:
        if not confirmed:
            raise PlanningCapacityError("ERROR_CONFIRMATION_REQUIRED", "Capacity confirmation requires explicit approval.")
        if len(idempotency_key) < 12:
            raise PlanningCapacityError("ERROR_CONTEXT_SCHEMA_INVALID", "Capacity idempotency identity is invalid.")
        confirmed_at = preview.capacity.get("confirmed_at")
        confirmed_by = preview.capacity.get("confirmed_by")
        if not isinstance(confirmed_at, str) or not isinstance(confirmed_by, str):
            raise PlanningCapacityError("ERROR_CONTEXT_SCHEMA_INVALID", "Capacity confirmation provenance is invalid.")
        intake_sha256 = _sha256(preview.intake)
        try:
            logical_session = build_logical_session_revision(
                preview.logical_session,
                intake_sha256=intake_sha256,
                actor_id=confirmed_by,
                created_at=confirmed_at,
                repository_root=self._repository_root,
            )
        except ProjectSourceRevisionError as error:
            raise PlanningCapacityError("ERROR_CONTEXT_SCHEMA_INVALID", str(error)) from error
        upgrade_id = f"planning-capacity-{hashlib.sha256(idempotency_key.encode('utf-8')).hexdigest()[:24]}"
        audit = {
            "upgrade_id": upgrade_id,
            "tenant_id": preview.tenant_id,
            "project_id": preview.project_id,
            "actor_id": confirmed_by,
            "applied_at": confirmed_at,
            "reason": "operator-confirmed-planning-capacity",
            "previous_project_sha256": preview.current_project_sha256,
            "project_v2_sha256": preview.proposed_project_sha256,
            "intake_sha256": intake_sha256,
            "logical_session_id": logical_session["logical_session_id"],
            "logical_session_sha256": _sha256(logical_session),
            "run_id": preview.run_id,
            "deployment_id": preview.deployment_id,
            "planning_capacity": preview.capacity,
        }
        try:
            self._repository.replace_project_v2_and_intake(
                preview.tenant_id,
                preview.project_id,
                expected_project_sha256=preview.current_project_sha256,
                project_v2=preview.project_v2,
                intake=preview.intake,
                logical_session=logical_session,
                run_id=preview.run_id,
                deployment_id=preview.deployment_id,
                audit_record=audit,
            )
        except RepositoryError as error:
            raise PlanningCapacityError(error.code, error.message) from error
        return {**preview.public(), "upgrade_id": upgrade_id, "applied_at": confirmed_at}


def _primary_deployment_id(project: dict[str, JsonValue]) -> str:
    deployments = project.get("market_deployments")
    matches = [
        item
        for item in deployments
        if isinstance(item, dict)
        and item.get("market_phase") == "active"
        and item.get("deployment_role") == "primary"
        and isinstance(item.get("deployment_id"), str)
    ] if isinstance(deployments, list) else []
    if len(matches) != 1:
        raise PlanningCapacityError(
            "ERROR_PRIMARY_DEPLOYMENT_AMBIGUOUS",
            "Project V2 requires exactly one active primary deployment.",
        )
    return str(matches[0]["deployment_id"])


def _sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
