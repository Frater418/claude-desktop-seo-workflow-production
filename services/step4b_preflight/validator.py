from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from services.preflight_common import validate_lineage
from services.domain_contract.validator import validate_project
from services.jsonld_validation import JsonLdValidatorAdapterError, validate_local_jsonld_text


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _errors(schema_name: str, value: object, code: str, root: Path) -> list[dict[str, object]]:
    schema = json.loads((root / "standards" / "outputs" / schema_name).read_text(encoding="utf-8"))
    return [{"code": code, "message": error.message, "path": list(error.absolute_path)} for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value)]


def page_content_sha256(page: dict[str, object]) -> str:
    payload = dict(page)
    payload.pop("content_sha256", None)
    canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_step4b_candidate(bundle: dict[str, object], root: Path | None = None) -> dict[str, object]:
    root = root or _root()
    page = bundle.get("page_spec")
    staging = bundle.get("staging_evidence")
    errors = _errors("step-4b-page-spec.schema.json", page, "ERROR_STEP4B_PAGE_INVALID", root)
    errors.extend(_errors("staging-evidence.schema.json", staging, "ERROR_STEP4B_STAGING_INVALID", root))
    if isinstance(page, dict) and isinstance(staging, dict):
        service_area = page.get("service_area", {})
        if service_area.get("mode") == "service_area" and service_area.get("address_claims"):
            errors.append({"code": "ERROR_STEP4B_SERVICE_AREA_UNSAFE", "message": "Service-area pages cannot claim a physical address.", "path": ["page_spec", "service_area", "address_claims"]})
        required_tools = {"crawl", "lighthouse", "axe", "visual"}
        observed_tools = {check.get("tool") for check in staging.get("checks", [])}
        if observed_tools != required_tools:
            errors.append({"code": "ERROR_STEP4B_STAGING_EVIDENCE_INCOMPLETE", "message": "Staging evidence requires crawl, Lighthouse, axe and visual references.", "path": ["staging_evidence", "checks"]})
        calculated_hash = page_content_sha256(page)
        if page.get("content_sha256") != calculated_hash or staging.get("content_sha256") != calculated_hash:
            errors.append({"code": "ERROR_STEP4B_CONTENT_HASH_MISMATCH", "message": "Page and staging evidence must bind the same content hash.", "path": ["content_sha256"]})
        markup = page.get("html")
        if isinstance(markup, str) and re.search(r"<\s*(script|iframe|object|embed)\b|\bon\w+\s*=|javascript:|data:", markup, re.I):
            errors.append({"code": "ERROR_STEP4B_MARKUP_UNSAFE", "message": "Page markup contains a prohibited executable or embedded resource.", "path": ["page_spec", "html"]})
        jsonld = page.get("jsonld")
        if isinstance(jsonld, dict) and isinstance(jsonld.get("graph"), dict):
            graph = json.dumps(jsonld["graph"], ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            if jsonld.get("graph_hash") != hashlib.sha256(graph.encode("utf-8")).hexdigest():
                errors.append({"code": "ERROR_STEP4B_JSONLD_HASH_MISMATCH", "message": "JSON-LD graph hash must bind canonical graph bytes.", "path": ["page_spec", "jsonld", "graph_hash"]})
            try:
                validation = validate_local_jsonld_text(f'<script type="application/ld+json">{graph}</script>', root=root)
            except JsonLdValidatorAdapterError as exc:
                errors.append({"code": exc.code, "message": str(exc), "path": ["page_spec", "jsonld", "graph"]})
            else:
                if not validation["valid"] or validation["blocks_found"] <= 0:
                    errors.append({"code": "ERROR_STEP4B_JSONLD_INVALID", "message": "JSON-LD graph must produce a valid local JSON-LD block.", "path": ["page_spec", "jsonld", "graph"]})
        project = bundle.get("project")
        if not isinstance(project, dict):
            errors.append({"code": "ERROR_STEP4B_PROJECT_MISSING", "message": "Page preflight requires the canonical Project V2 contract.", "path": ["project"]})
        elif not validate_project(project, root)["valid"]:
            errors.append({"code": "ERROR_STEP4B_PROJECT_INVALID", "message": "Page preflight requires a valid Project V2 contract.", "path": ["project"]})
        else:
            deployments = [item for item in project["market_deployments"] if item["deployment_id"] == page.get("deployment_id")]
            if len(deployments) != 1 or project.get("project_id") != page.get("project_id"):
                errors.append({"code": "ERROR_STEP4B_DEPLOYMENT_INVALID", "message": "Page must bind to exactly one Project V2 deployment.", "path": ["page_spec", "deployment_id"]})
            else:
                deployment = deployments[0]
                if page.get("language") != deployment["language"] or page.get("locale") != deployment["locale"]:
                    errors.append({"code": "ERROR_STEP4B_LOCALE_MISMATCH", "message": "Page language and locale must exactly match the deployment.", "path": ["page_spec", "locale"]})
                service_areas = {item["service_area_id"]: item for item in project["entity_domain_gbp"]["service_areas"]}
                locations = {item["location_id"]: item for item in project["entity_domain_gbp"]["physical_locations"]}
                references = set(page["service_area"]["areas"])
                allowed_areas = {identifier for identifier in deployment["service_area_ids"]}
                allowed_names = {service_areas[identifier]["name"] for identifier in allowed_areas if identifier in service_areas}
                if not references.issubset(allowed_areas | allowed_names):
                    errors.append({"code": "ERROR_STEP4B_SERVICE_AREA_UNSUPPORTED", "message": "Page service areas must be declared by the bound deployment.", "path": ["page_spec", "service_area", "areas"]})
                if page["service_area"]["mode"] == "physical_location":
                    physical = set(page["service_area"].get("physical_location_ids", []))
                    valid_locations = set(deployment["physical_location_ids"])
                    if not physical or not physical.issubset(valid_locations) or any(locations[item]["evidence_status"] != "verified" for item in physical if item in locations):
                        errors.append({"code": "ERROR_STEP4B_PHYSICAL_LOCATION_INVALID", "message": "Physical-location pages require verified deployment locations.", "path": ["page_spec", "service_area"]})
    return {"valid": not errors, "errors": errors}


def validate_step4b_preflight(bundle: dict[str, object], root: Path | None = None) -> dict[str, object]:
    root = root or _root()
    result = validate_step4b_candidate(bundle, root)
    result["errors"].extend(validate_lineage({**bundle, "candidate": bundle.get("page_spec")}, "4b", "4a", "GATE-4A", root, "step-4b-page-spec.schema.json"))
    result["valid"] = not result["errors"]
    return result
