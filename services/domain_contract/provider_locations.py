from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ProviderLocationBindingError(RuntimeError):
    code: str
    message: str
    deployment_id: str | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def bind_project_provider_locations(
    project: Mapping[str, Any],
    registry: Mapping[str, Any],
    *,
    infer_missing_targets: bool,
    require_verified: bool,
) -> dict[str, Any]:
    """Return a Project V2 copy with canonical provider targets bound per deployment."""
    bound = copy.deepcopy(dict(project))
    deployments = bound.get("market_deployments")
    targets = registry.get("targets")
    if not isinstance(deployments, list) or not isinstance(targets, list):
        raise ProviderLocationBindingError(
            "ERROR_PROVIDER_LOCATION_REGISTRY_INVALID",
            "Project deployments or provider location targets are unavailable.",
        )
    target_records = [target for target in targets if isinstance(target, dict)]
    target_by_id = {
        target["target_id"]: target
        for target in target_records
        if isinstance(target.get("target_id"), str)
    }
    if len(target_by_id) != len(target_records):
        raise ProviderLocationBindingError(
            "ERROR_PROVIDER_LOCATION_REGISTRY_INVALID",
            "Provider location target identities are invalid or duplicated.",
        )

    for deployment in deployments:
        if not isinstance(deployment, dict):
            raise ProviderLocationBindingError(
                "ERROR_PROVIDER_LOCATION_BINDING_INVALID",
                "A market deployment is malformed.",
            )
        deployment_id = deployment.get("deployment_id")
        identity = deployment_id if isinstance(deployment_id, str) else None
        verification = deployment.get("provider_location_verification")
        target_id = verification.get("target_id") if isinstance(verification, dict) else None
        if not isinstance(target_id, str) and infer_missing_targets:
            target_id = _infer_target_id(deployment, target_records)
        target = target_by_id.get(target_id) if isinstance(target_id, str) else None
        if target is None:
            if require_verified:
                raise ProviderLocationBindingError(
                    "ERROR_PROVIDER_LOCATION_TARGET_REQUIRED",
                    "No exact provider location target can be derived from the deployment and briefing regions.",
                    identity,
                )
            continue
        canonical = _canonical_verification(target)
        deployment["provider_location_verification"] = canonical
        if require_verified and canonical["status"] != "verified":
            raise ProviderLocationBindingError(
                "ERROR_PROVIDER_LOCATION_UNVERIFIED",
                f"Provider target {target_id} is not verified for production use.",
                identity,
            )
        _assert_target_compatibility(deployment, target, identity)

    try:
        version = tuple(int(part) for part in str(bound.get("schema_version", "0.0.0")).split("."))
    except ValueError:
        version = (0, 0, 0)
    if version < (1, 2, 0):
        bound["schema_version"] = "1.2.0"
    return bound


def _infer_target_id(deployment: Mapping[str, Any], targets: list[dict[str, Any]]) -> str:
    candidates = [
        target
        for target in targets
        if target.get("status") == "verified"
        and target.get("country_code") == deployment.get("country_code")
        and deployment.get("language") in target.get("languages", [])
        and _scope_compatible(deployment.get("seo_operating_model"), target.get("target_type"))
        and _region_compatible(deployment, target)
    ]
    if len(candidates) != 1:
        raise ProviderLocationBindingError(
            "ERROR_PROVIDER_LOCATION_TARGET_AMBIGUOUS" if candidates else "ERROR_PROVIDER_LOCATION_TARGET_REQUIRED",
            "The deployment does not resolve to exactly one verified provider location target.",
            deployment.get("deployment_id") if isinstance(deployment.get("deployment_id"), str) else None,
        )
    return str(candidates[0]["target_id"])


def _canonical_verification(target: Mapping[str, Any]) -> dict[str, Any]:
    verified = target.get("status") == "verified"
    return {
        "status": "verified" if verified else "unknown",
        "provider_id": target.get("provider_id"),
        "target_id": target.get("target_id"),
        "target_type": target.get("target_type"),
        "location_name": target.get("location_name"),
        "provider_location_code": target.get("location_code") if verified else None,
        "verified_at": target.get("verified_at") if verified else None,
        "verification_source": target.get("verification_source") if verified else None,
    }


def _assert_target_compatibility(
    deployment: Mapping[str, Any],
    target: Mapping[str, Any],
    deployment_id: str | None,
) -> None:
    if target.get("country_code") != deployment.get("country_code") or deployment.get("language") not in target.get("languages", []):
        raise ProviderLocationBindingError(
            "ERROR_PROVIDER_LOCATION_GEO_MISMATCH",
            "Provider target country or language does not match its market deployment.",
            deployment_id,
        )
    if not _scope_compatible(deployment.get("seo_operating_model"), target.get("target_type")):
        raise ProviderLocationBindingError(
            "ERROR_PROVIDER_LOCATION_SCOPE_MISMATCH",
            "Provider target granularity does not match the deployment SEO operating model.",
            deployment_id,
        )
    if not _region_compatible(deployment, target):
        raise ProviderLocationBindingError(
            "ERROR_PROVIDER_LOCATION_REGION_MISMATCH",
            "Provider target does not match the briefing-derived target regions.",
            deployment_id,
        )


def _scope_compatible(operating_model: object, target_type: object) -> bool:
    if operating_model in {"national", "international", "digital"}:
        return target_type == "country"
    if operating_model in {"local", "regional", "programmatic_local"}:
        return target_type in {"region", "city", "postal_code"}
    return False


def _region_compatible(deployment: Mapping[str, Any], target: Mapping[str, Any]) -> bool:
    if target.get("target_type") == "country":
        return True
    regions = deployment.get("target_regions")
    if not isinstance(regions, list):
        return False
    target_labels = {
        _normalized(label)
        for label in (target.get("location_name"), *(target.get("aliases") if isinstance(target.get("aliases"), list) else []))
        if isinstance(label, str)
    }
    return any(_normalized(region) in target_labels for region in regions if isinstance(region, str))


def _normalized(value: str) -> str:
    return " ".join(value.casefold().strip().split())
