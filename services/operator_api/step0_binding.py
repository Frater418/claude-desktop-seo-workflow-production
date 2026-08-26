from __future__ import annotations

import hashlib
import json
from typing import Mapping
from urllib.parse import urlsplit

from pydantic import JsonValue

from .provider_outputs import ProviderOutput


class Step0CrossBindingError(RuntimeError):
    """Raised when a legacy Step 0 manifest is not bound to its Project V2 source."""


def validate_step0_cross_binding(
    output: ProviderOutput,
    manifest: Mapping[str, JsonValue],
    bundle: Mapping[str, JsonValue],
) -> None:
    """Reject a provider manifest that is not the immutable source of this Project V2 run."""
    if hashlib.sha256(output.content_bytes).hexdigest() != output.content_sha256:
        raise Step0CrossBindingError("Provider manifest bytes do not match their declared hash.")
    project = bundle.get("project")
    intake = bundle.get("accepted_intake")
    binding = manifest.get("source_binding")
    if not isinstance(project, dict) or not isinstance(intake, dict) or not isinstance(binding, dict):
        raise Step0CrossBindingError("Step 0 requires Project V2, accepted intake, and immutable source binding.")
    deployment = _deployment(project, binding)
    verification = deployment.get("provider_location_verification")
    is_v2 = manifest.get("schema_version") == "2.0.0"
    if not isinstance(verification, dict):
        raise Step0CrossBindingError("Project V2 provider location binding is unavailable.")
    expected = {
        "tenant_id": _nested(project, "tenant", "tenant_id"),
        "project_id": project.get("project_id"),
        "customer_id": _nested(project, "customer", "customer_id"),
        "market_id": deployment.get("market_id"),
        "deployment_id": deployment.get("deployment_id"),
        "language": deployment.get("language"),
        "country": deployment.get("country_code"),
        "project_v2_sha256": _canonical_sha256(project),
        "intake_source_sha256": intake.get("source_sha256"),
    }
    if is_v2:
        expected.update(
            {
                "locale": deployment.get("locale"),
                "provider_target_id": verification.get("target_id"),
                "provider_location_code": verification.get("provider_location_code"),
                "deployment_sha256": _canonical_sha256(deployment),
            }
        )
    if output.tenant_id != expected["tenant_id"] or output.project_id != expected["project_id"]:
        raise Step0CrossBindingError("Provider output identity does not match canonical Project V2.")
    if any(binding.get(key) != value for key, value in expected.items()):
        raise Step0CrossBindingError("Step 0 manifest source binding does not match canonical Project V2 or intake.")
    if manifest.get("project_id") != expected["project_id"] or manifest.get("language") != expected["language"] or manifest.get("country") != expected["country"]:
        raise Step0CrossBindingError("Step 0 manifest identity does not match canonical Project V2.")
    if verification.get("status") == "verified" and manifest.get("location_code") != verification.get("provider_location_code"):
        raise Step0CrossBindingError("Step 0 manifest provider location code does not match canonical Project V2.")
    if is_v2 and (
        manifest.get("deployment_binding") != deployment
        or manifest.get("target_regions") != deployment.get("target_regions")
    ):
        raise Step0CrossBindingError("Step 0 manifest deployment projection does not match canonical Project V2.")
    if _semantic_projection(manifest, project, intake, deployment) is False:
        raise Step0CrossBindingError("Step 0 manifest business semantics do not match canonical Project V2 or accepted intake.")


def _deployment(project: Mapping[str, JsonValue], binding: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
    deployments = project.get("market_deployments")
    if not isinstance(deployments, list):
        raise Step0CrossBindingError("Project V2 deployments are unavailable.")
    matched = [value for value in deployments if isinstance(value, dict) and value.get("deployment_id") == binding.get("deployment_id")]
    if len(matched) != 1:
        raise Step0CrossBindingError("Step 0 manifest deployment is not declared by canonical Project V2.")
    return matched[0]


def _nested(value: Mapping[str, JsonValue], parent: str, child: str) -> JsonValue:
    nested = value.get(parent)
    return nested.get(child) if isinstance(nested, dict) else None


def _semantic_projection(
    manifest: Mapping[str, JsonValue],
    project: Mapping[str, JsonValue],
    intake: Mapping[str, JsonValue],
    deployment: Mapping[str, JsonValue],
) -> bool:
    customer = project.get("customer")
    reviewed = intake.get("reviewed")
    audiences = project.get("target_audiences")
    services = project.get("core_services")
    regions = deployment.get("target_regions")
    if not isinstance(customer, dict) or not isinstance(reviewed, dict) or not isinstance(audiences, list) or not isinstance(services, list) or not isinstance(regions, list):
        raise Step0CrossBindingError("Project V2 semantic fields are unavailable.")
    customer_name = customer.get("name")
    intake_name = reviewed.get("project_name")
    intake_project = reviewed.get("project_v2")
    service_names = tuple(
        service if isinstance(service, str) else service.get("name")
        for service in services
        if isinstance(service, (str, dict))
    )
    entity_domain = project.get("entity_domain_gbp")
    brand = entity_domain.get("brand") if isinstance(entity_domain, dict) else None
    manifest_entities = manifest.get("entities")
    manifest_services = manifest_entities.get("core_services") if isinstance(manifest_entities, dict) else None
    manifest_service_names = tuple(
        service.get("name")
        for service in manifest_services
        if isinstance(service, dict)
    ) if isinstance(manifest_services, list) else ()
    domain_hosts = _deployment_domain_hosts(project, deployment)
    manifest_host = _domain_host(manifest.get("domain"))
    audience = manifest.get("target_audience")
    content_focus = manifest.get("content_focus")
    secondary_regions = manifest.get("secondary_regions")
    if not isinstance(customer_name, str) or not isinstance(intake_name, str) or not isinstance(intake_project, dict) or not isinstance(manifest_host, str) or not isinstance(audience, str) or not audience.strip() or not isinstance(content_focus, str) or not content_focus.strip() or not isinstance(brand, dict) or not isinstance(manifest_entities, dict) or not isinstance(secondary_regions, list):
        raise Step0CrossBindingError("Step 0 manifest semantic fields are unavailable.")
    return (
        manifest.get("project_name") == customer_name
        and intake_name == customer_name
        and intake_project == project
        and manifest_host in domain_hosts
        and manifest.get("business_goal") == project.get("business_goal")
        and manifest_entities.get("brand_entity") == brand.get("name")
        and manifest_service_names == service_names
        and manifest.get("primary_region") == (regions[0] if regions else None)
        and tuple(secondary_regions) == tuple(regions[1:])
    )


def _deployment_domain_hosts(project: Mapping[str, JsonValue], deployment: Mapping[str, JsonValue]) -> tuple[str, ...]:
    entity = project.get("entity_domain_gbp")
    domain_ids = deployment.get("domain_ids")
    if not isinstance(entity, dict) or not isinstance(domain_ids, list):
        raise Step0CrossBindingError("Project V2 deployment domains are unavailable.")
    domains = entity.get("domains")
    if not isinstance(domains, list):
        raise Step0CrossBindingError("Project V2 domains are unavailable.")
    by_id = {item.get("domain_id"): item.get("host") for item in domains if isinstance(item, dict)}
    hosts = tuple(by_id.get(domain_id) for domain_id in domain_ids)
    if not hosts or not all(isinstance(host, str) for host in hosts):
        raise Step0CrossBindingError("Project V2 deployment domain references are invalid.")
    return tuple(hosts)


def _domain_host(value: JsonValue | None) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlsplit(value)
    return parsed.hostname if parsed.scheme in {"http", "https"} and parsed.path in {"", "/"} and not parsed.query and not parsed.fragment else None


def _canonical_sha256(value: Mapping[str, JsonValue]) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
