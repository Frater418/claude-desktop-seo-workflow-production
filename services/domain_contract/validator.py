"""Runtime-neutral Heartweb Foundation domain validator.

Autor: Raphael Rechberger
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


DOMAIN_SCHEMA_NAMES = (
    "project.schema.json",
    "search-deployment.schema.json",
    "entity-domain-gbp.schema.json",
    "risk-compliance.schema.json",
    "market-registry.schema.json",
    "provider-location-registry.schema.json",
)


class DomainContractError(ValueError):
    """Structured Foundation contract failure."""

    def __init__(self, code: str, message: str, path: list | None = None, remediation: str = ""):
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = path or []
        self.remediation = remediation

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "remediation": self.remediation,
        }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DomainContractError(
            "ERROR_DOMAIN_CONTRACT_FILE_MISSING",
            f"Required domain contract file not found: {path}",
            remediation="Restore the versioned contract file and rerun validation.",
        ) from exc
    except json.JSONDecodeError as exc:
        raise DomainContractError(
            "ERROR_DOMAIN_CONTRACT_JSON_INVALID",
            f"Invalid JSON in domain contract file {path}: {exc}",
            remediation="Correct the JSON syntax before running any workflow step.",
        ) from exc


def _contracts(root: Path) -> tuple[Draft202012Validator, dict[str, dict], dict[str, dict]]:
    domain_dir = root / "standards" / "domain"
    schemas = {name: _load_json(domain_dir / name) for name in DOMAIN_SCHEMA_NAMES}
    registry = Registry()
    for schema in schemas.values():
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    validator = Draft202012Validator(
        schemas["project.schema.json"],
        registry=registry,
        format_checker=FormatChecker(),
    )
    market_registry = _load_json(domain_dir / "market-registry.json")
    market_by_id = {market["market_id"]: market for market in market_registry["markets"]}
    provider_registry = _load_json(domain_dir / "provider-location-registry.json")
    provider_by_target_id = {target["target_id"]: target for target in provider_registry["targets"]}
    return validator, market_by_id, provider_by_target_id


def _schema_error(error) -> dict:
    path = list(error.absolute_path)
    message = error.message
    code = "ERROR_DOMAIN_SCHEMA_INVALID"
    remediation = "Correct the project sidecar to match the closed Foundation contract."
    if error.validator == "required" and "'locale' is a required property" in message:
        code = "ERROR_DOMAIN_LOCALE_REQUIRED"
        remediation = "Add the explicit locale to the affected search deployment."
    elif path[:2] == ["risk_compliance", "claim_evidence"]:
        code = "ERROR_COMPLIANCE_YMYL_EVIDENCE_REQUIRED"
        remediation = "Add approved evidence records and the required reviewer policy for the YMYL project."
    return {
        "code": code,
        "message": message,
        "path": path,
        "remediation": remediation,
    }


def _uses_deployment_bound_provider_targets(project: dict) -> bool:
    try:
        version = tuple(int(part) for part in str(project.get("schema_version", "0.0.0")).split("."))
    except ValueError:
        return False
    return version >= (1, 2, 0)


def _uses_confirmed_planning_capacity(project: dict) -> bool:
    try:
        version = tuple(int(part) for part in str(project.get("schema_version", "0.0.0")).split("."))
    except ValueError:
        return False
    return version >= (1, 3, 0)


def _provider_verification(target: dict) -> dict:
    return {
        "status": target["status"],
        "provider_id": target["provider_id"],
        "target_id": target["target_id"],
        "target_type": target["target_type"],
        "location_name": target["location_name"],
        "provider_location_code": target["location_code"],
        "verified_at": target["verified_at"],
        "verification_source": target["verification_source"],
    }


def _semantic_errors(
    project: dict,
    market_by_id: dict[str, dict],
    provider_by_target_id: dict[str, dict],
) -> list[dict]:
    errors: list[dict] = []
    if _uses_confirmed_planning_capacity(project):
        capacity = project.get("planning_capacity")
        if not isinstance(capacity, dict):
            errors.append(
                {
                    "code": "ERROR_DOMAIN_PLANNING_CAPACITY_UNCONFIRMED",
                    "message": "Project V2 has no confirmed weekly planning capacity.",
                    "path": ["planning_capacity"],
                    "remediation": "Confirm the minimum and maximum weekly hours in intake or through the Operator Console.",
                }
            )
        else:
            minimum = capacity.get("min")
            maximum = capacity.get("max")
            if (
                not isinstance(minimum, (int, float))
                or isinstance(minimum, bool)
                or not isinstance(maximum, (int, float))
                or isinstance(maximum, bool)
                or maximum < minimum
                or capacity.get("provisional") is not False
            ):
                errors.append(
                    {
                        "code": "ERROR_DOMAIN_PLANNING_CAPACITY_INVALID",
                        "message": "Project V2 weekly planning capacity is invalid or provisional.",
                        "path": ["planning_capacity"],
                        "remediation": "Confirm a non-provisional range with max greater than or equal to min.",
                    }
                )
    entities = project["entity_domain_gbp"]
    brand_id = entities["brand"]["brand_id"]
    domains = {item["domain_id"] for item in entities["domains"]}
    locations = {item["location_id"]: item for item in entities["physical_locations"]}
    service_areas = {item["service_area_id"]: item for item in entities["service_areas"]}

    for index, deployment in enumerate(project["market_deployments"]):
        base_path = ["market_deployments", index]
        registered = market_by_id.get(deployment["market_id"])
        if registered is None:
            errors.append(
                {
                    "code": "ERROR_DOMAIN_MARKET_UNKNOWN",
                    "message": f"Unknown market_id: {deployment['market_id']}",
                    "path": base_path + ["market_id"],
                    "remediation": "Add a verified market-registry entry or correct the deployment market_id.",
                }
            )
            continue
        for field in ("country_code", "language", "locale", "legal_jurisdiction"):
            if deployment[field] != registered[field]:
                errors.append(
                    {
                        "code": "ERROR_DOMAIN_GEO_MISMATCH",
                        "message": f"Deployment field '{field}' does not match market registry entry '{deployment['market_id']}'.",
                        "path": base_path + [field],
                        "remediation": "Correct the deployment or registry through an approved versioned market update.",
                    }
                )
        verification = deployment["provider_location_verification"]
        if not _uses_deployment_bound_provider_targets(project):
            if verification != registered["provider_location_verification"]:
                errors.append(
                    {
                        "code": "ERROR_DOMAIN_PROVIDER_VERIFICATION_MISMATCH",
                        "message": "Legacy deployment provider verification does not match the market registry.",
                        "path": base_path + ["provider_location_verification"],
                        "remediation": "Migrate the project to schema 1.2 and bind a verified provider target per deployment.",
                    }
                )
        else:
            target_id = verification.get("target_id")
            target = provider_by_target_id.get(target_id)
            if target is None:
                errors.append(
                    {
                        "code": "ERROR_DOMAIN_PROVIDER_TARGET_UNKNOWN",
                        "message": f"Unknown provider target_id: {target_id}",
                        "path": base_path + ["provider_location_verification", "target_id"],
                        "remediation": "Select an exact target_id from the versioned provider-location registry.",
                    }
                )
            else:
                if verification != _provider_verification(target):
                    errors.append(
                        {
                            "code": "ERROR_DOMAIN_PROVIDER_VERIFICATION_MISMATCH",
                            "message": "Deployment provider verification does not match its exact provider target.",
                            "path": base_path + ["provider_location_verification"],
                            "remediation": "Copy the complete verified target binding from the provider-location registry.",
                        }
                    )
                if target["country_code"] != deployment["country_code"] or deployment["language"] not in target["languages"]:
                    errors.append(
                        {
                            "code": "ERROR_DOMAIN_PROVIDER_TARGET_GEO_MISMATCH",
                            "message": "Provider target country or language does not match the deployment.",
                            "path": base_path + ["provider_location_verification", "target_id"],
                            "remediation": "Choose a provider target that matches the deployment country and language.",
                        }
                    )
                local_models = {"local", "regional", "programmatic_local"}
                if deployment["seo_operating_model"] in local_models and target["target_type"] == "country":
                    errors.append(
                        {
                            "code": "ERROR_DOMAIN_PROVIDER_TARGET_SCOPE_MISMATCH",
                            "message": "A local or regional deployment cannot use a country-only provider target.",
                            "path": base_path + ["provider_location_verification", "target_type"],
                            "remediation": "Bind a verified region, city or postal-code target from the briefing scope.",
                        }
                    )
            if deployment["market_phase"] == "active" and verification.get("status") != "verified":
                errors.append(
                    {
                        "code": "ERROR_DOMAIN_PROVIDER_LOCATION_UNVERIFIED",
                        "message": "An active deployment requires a verified provider target before Step 0.",
                        "path": base_path + ["provider_location_verification", "status"],
                        "remediation": "Verify the exact provider target or keep the deployment planned until verification exists.",
                    }
                )
        if deployment["brand_id"] != brand_id:
            errors.append(
                {
                    "code": "ERROR_DOMAIN_REFERENCE_UNKNOWN",
                    "message": f"Unknown brand reference: {deployment['brand_id']}",
                    "path": base_path + ["brand_id"],
                    "remediation": "Reference the declared project brand_id.",
                }
            )
        for field, declared in (
            ("domain_ids", domains),
            ("physical_location_ids", set(locations)),
            ("service_area_ids", set(service_areas)),
        ):
            unknown = sorted(set(deployment[field]) - declared)
            if unknown:
                errors.append(
                    {
                        "code": "ERROR_DOMAIN_REFERENCE_UNKNOWN",
                        "message": f"Unknown references in {field}: {', '.join(unknown)}",
                        "path": base_path + [field],
                        "remediation": "Declare the referenced entities or remove the invalid references.",
                    }
                )
        if deployment["seo_operating_model"] in {"local", "regional", "programmatic_local"} and not (
            deployment["physical_location_ids"] or deployment["service_area_ids"]
        ):
            errors.append(
                {
                    "code": "ERROR_DOMAIN_LOCAL_SCOPE_MISSING",
                    "message": "Local, regional or programmatic-local deployment requires a physical location or service area reference.",
                    "path": base_path + ["seo_operating_model"],
                    "remediation": "Attach verified location or service-area evidence before local output is generated.",
                }
            )

    for index, profile in enumerate(entities["gbp_profiles"]):
        location = locations.get(profile["location_id"])
        if location is None or location["evidence_status"] != "verified":
            errors.append(
                {
                    "code": "ERROR_DOMAIN_LOCAL_PRESENCE_UNVERIFIED",
                    "message": f"GBP profile '{profile['gbp_id']}' has no verified physical location.",
                    "path": ["entity_domain_gbp", "gbp_profiles", index, "location_id"],
                    "remediation": "Verify the physical location evidence or remove the GBP profile from the project contract.",
                }
            )
    return errors


def validate_project(project: dict, root: Path | None = None) -> dict:
    root = root or _repo_root()
    validator, market_by_id, provider_by_target_id = _contracts(root)
    schema_errors = [_schema_error(error) for error in sorted(validator.iter_errors(project), key=lambda item: list(item.absolute_path))]
    semantic_errors = [] if schema_errors else _semantic_errors(project, market_by_id, provider_by_target_id)
    errors = schema_errors + semantic_errors
    return {
        "valid": not errors,
        "schema_version": project.get("schema_version"),
        "project_id": project.get("project_id"),
        "errors": errors,
    }


def assert_project_valid(project: dict, root: Path | None = None) -> dict:
    result = validate_project(project, root=root)
    if not result["valid"]:
        first = result["errors"][0]
        raise DomainContractError(
            first["code"],
            first["message"],
            path=first["path"],
            remediation=first["remediation"],
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Heartweb Foundation domain contract validator")
    parser.add_argument("--project", required=True, help="Path to a project v2 JSON sidecar")
    parser.add_argument("--json-out", action="store_true")
    args = parser.parse_args()
    try:
        project = _load_json(Path(args.project))
        result = validate_project(project)
    except DomainContractError as exc:
        result = {"valid": False, "errors": [exc.to_dict()]}
    if args.json_out:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["valid"]:
        print(f"[BESTANDEN] Foundation Domain Contract: {result['project_id']}")
    else:
        print(f"[NICHT BESTANDEN] {len(result['errors'])} Domainfehler", file=sys.stderr)
        for error in result["errors"]:
            print(f"  - {error['code']}: {error['message']}", file=sys.stderr)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
