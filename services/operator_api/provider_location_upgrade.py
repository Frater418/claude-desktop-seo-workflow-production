from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.domain_contract.provider_locations import (
    ProviderLocationBindingError,
    bind_project_provider_locations,
)
from services.domain_contract.validator import validate_project

from .clock import Clock
from .models import JsonValue
from .project_source_revision import ProjectSourceRevisionError, build_logical_session_revision
from .repository import ProjectRepository, RepositoryError


@dataclass(frozen=True, slots=True)
class ProviderLocationUpgradeError(RuntimeError):
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


@dataclass(frozen=True, slots=True)
class ProviderLocationUpgradePreview:
    tenant_id: str
    project_id: str
    current_project_sha256: str
    proposed_project_sha256: str
    preview_hash: str
    changed: bool
    deployment_bindings: tuple[dict[str, JsonValue], ...]
    project_v2: dict[str, JsonValue]
    intake: dict[str, JsonValue]
    logical_session: dict[str, JsonValue]
    intake_sha256: str
    logical_source_stale: bool
    run_id: str
    deployment_id: str

    def public(self) -> dict[str, JsonValue]:
        return {
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "current_project_sha256": self.current_project_sha256,
            "proposed_project_sha256": self.proposed_project_sha256,
            "preview_hash": self.preview_hash,
            "changed": self.changed,
            "deployment_bindings": list(self.deployment_bindings),
            "intake_sha256": self.intake_sha256,
            "logical_source_stale": self.logical_source_stale,
            "run_id": self.run_id,
            "deployment_id": self.deployment_id,
        }


class ProviderLocationUpgradeService:
    def __init__(self, repository: ProjectRepository, repository_root: Path, clock: Clock) -> None:
        self._repository = repository
        self._repository_root = repository_root
        self._clock = clock

    def preview(self, tenant_id: str, project_id: str) -> ProviderLocationUpgradePreview:
        current = self._repository.project_v2(tenant_id, project_id)
        intake = self._repository.intake(tenant_id, project_id)
        reviewed = intake.get("reviewed")
        if not isinstance(reviewed, dict) or reviewed.get("project_v2") != current:
            raise ProviderLocationUpgradeError(
                "ERROR_CONTEXT_SOURCE_INVALID",
                "Accepted intake and canonical Project V2 are not identical before location binding.",
            )
        try:
            registry = _read_object(self._repository_root / "standards/domain/provider-location-registry.json")
            proposed = bind_project_provider_locations(
                current,
                registry,
                infer_missing_targets=True,
                require_verified=True,
            )
        except ProviderLocationBindingError as error:
            raise ProviderLocationUpgradeError(error.code, error.message) from error
        validation = validate_project(proposed, root=self._repository_root)
        if not validation["valid"]:
            first = validation["errors"][0] if validation["errors"] else None
            detail = first.get("code") if isinstance(first, dict) else "ERROR_DOMAIN_CONTRACT_INVALID"
            raise ProviderLocationUpgradeError(
                "ERROR_DOMAIN_CONTRACT_INVALID",
                f"Bound Project V2 failed domain validation: {detail}.",
            )
        upgraded_intake = copy.deepcopy(intake)
        upgraded_reviewed = upgraded_intake.get("reviewed")
        if not isinstance(upgraded_reviewed, dict):
            raise ProviderLocationUpgradeError("ERROR_CONTEXT_SOURCE_INVALID", "Accepted intake review is unavailable.")
        upgraded_reviewed["project_v2"] = proposed
        primary = _primary_active_deployment(proposed)
        current_run = self._repository.current_run(tenant_id, project_id)
        run = self._repository.run(tenant_id, project_id, current_run.run_id)
        logical_session = self._repository.logical_session(tenant_id, project_id)
        project_source = logical_session.get("project_source")
        intake_sha256 = _sha256(upgraded_intake)
        logical_source_stale = not isinstance(project_source, dict) or project_source.get("content_sha256") != intake_sha256
        current_sha = _sha256(current)
        proposed_sha = _sha256(proposed)
        bindings = tuple(_binding_summary(deployment) for deployment in proposed["market_deployments"] if isinstance(deployment, dict))
        preview_payload = {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "current_project_sha256": current_sha,
            "proposed_project_sha256": proposed_sha,
            "run_id": current_run.run_id,
            "deployment_id": primary["deployment_id"],
            "deployment_bindings": bindings,
            "intake_sha256": intake_sha256,
            "logical_session_sha256": _sha256(logical_session),
        }
        return ProviderLocationUpgradePreview(
            tenant_id=tenant_id,
            project_id=project_id,
            current_project_sha256=current_sha,
            proposed_project_sha256=proposed_sha,
            preview_hash=_sha256(preview_payload),
            changed=(
                current_sha != proposed_sha
                or logical_source_stale
                or run.get("deployment_id") != primary["deployment_id"]
            ),
            deployment_bindings=bindings,
            project_v2=proposed,
            intake=upgraded_intake,
            logical_session=logical_session,
            intake_sha256=intake_sha256,
            logical_source_stale=logical_source_stale,
            run_id=current_run.run_id,
            deployment_id=str(primary["deployment_id"]),
        )

    def apply(
        self,
        tenant_id: str,
        project_id: str,
        *,
        preview_hash: str,
        expected_project_sha256: str,
        actor_id: str,
        idempotency_key: str,
        confirmed: bool,
    ) -> dict[str, JsonValue]:
        if not confirmed:
            raise ProviderLocationUpgradeError("ERROR_CONFIRMATION_REQUIRED", "Provider location upgrade requires explicit confirmation.")
        preview = self.preview(tenant_id, project_id)
        if preview.preview_hash != preview_hash or preview.current_project_sha256 != expected_project_sha256:
            raise ProviderLocationUpgradeError("ERR_STALE_REVISION", "Provider location binding preview is stale.")
        if not isinstance(actor_id, str) or not actor_id.strip() or not isinstance(idempotency_key, str) or len(idempotency_key) < 12:
            raise ProviderLocationUpgradeError("ERROR_CONTEXT_SCHEMA_INVALID", "Actor or idempotency identity is invalid.")
        now = self._clock.now()
        upgrade_id = f"location-binding-{hashlib.sha256(idempotency_key.encode('utf-8')).hexdigest()[:24]}"
        try:
            logical_session = build_logical_session_revision(
                preview.logical_session,
                intake_sha256=preview.intake_sha256,
                actor_id=actor_id,
                created_at=now,
                repository_root=self._repository_root,
            )
        except ProjectSourceRevisionError as error:
            raise ProviderLocationUpgradeError(
                "ERROR_CONTEXT_SCHEMA_INVALID",
                str(error),
            ) from error
        audit = {
            "upgrade_id": upgrade_id,
            "tenant_id": tenant_id,
            "project_id": project_id,
            "actor_id": actor_id,
            "applied_at": now,
            "reason": "briefing-derived-provider-location-binding",
            "previous_project_sha256": preview.current_project_sha256,
            "project_v2_sha256": preview.proposed_project_sha256,
            "intake_sha256": _sha256(preview.intake),
            "logical_session_id": logical_session["logical_session_id"],
            "logical_session_sha256": _sha256(logical_session),
            "run_id": preview.run_id,
            "deployment_id": preview.deployment_id,
            "deployment_bindings": list(preview.deployment_bindings),
        }
        try:
            self._repository.replace_project_v2_and_intake(
                tenant_id,
                project_id,
                expected_project_sha256=expected_project_sha256,
                project_v2=preview.project_v2,
                intake=preview.intake,
                logical_session=logical_session,
                run_id=preview.run_id,
                deployment_id=preview.deployment_id,
                audit_record=audit,
            )
        except RepositoryError as error:
            raise ProviderLocationUpgradeError(error.code, error.message) from error
        return {**preview.public(), "upgrade_id": upgrade_id, "applied_at": now}


def _primary_active_deployment(project: dict[str, JsonValue]) -> dict[str, JsonValue]:
    deployments = project.get("market_deployments")
    matches = [
        deployment
        for deployment in deployments
        if isinstance(deployment, dict)
        and deployment.get("market_phase") == "active"
        and deployment.get("deployment_role") == "primary"
    ] if isinstance(deployments, list) else []
    if len(matches) != 1 or not isinstance(matches[0].get("deployment_id"), str):
        raise ProviderLocationUpgradeError(
            "ERROR_PRIMARY_DEPLOYMENT_AMBIGUOUS",
            "Project V2 requires exactly one active primary deployment.",
        )
    return matches[0]


def _binding_summary(deployment: dict[str, Any]) -> dict[str, JsonValue]:
    verification = deployment.get("provider_location_verification")
    if not isinstance(verification, dict):
        raise ProviderLocationUpgradeError("ERROR_PROVIDER_LOCATION_UNVERIFIED", "Deployment provider location is unavailable.")
    return {
        "deployment_id": deployment.get("deployment_id"),
        "market_id": deployment.get("market_id"),
        "country_code": deployment.get("country_code"),
        "language": deployment.get("language"),
        "locale": deployment.get("locale"),
        "target_regions": deployment.get("target_regions"),
        "provider_id": verification.get("provider_id"),
        "provider_target_id": verification.get("target_id"),
        "provider_target_type": verification.get("target_type"),
        "provider_location_name": verification.get("location_name"),
        "provider_location_code": verification.get("provider_location_code"),
        "verification_status": verification.get("status"),
    }


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProviderLocationUpgradeError(
            "ERROR_PROVIDER_LOCATION_REGISTRY_INVALID",
            "Provider location registry cannot be read.",
        ) from error
    if not isinstance(value, dict):
        raise ProviderLocationUpgradeError(
            "ERROR_PROVIDER_LOCATION_REGISTRY_INVALID",
            "Provider location registry is malformed.",
        )
    return value


def _sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
