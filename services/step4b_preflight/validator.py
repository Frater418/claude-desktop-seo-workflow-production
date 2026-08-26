from __future__ import annotations

import json
import hashlib
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from services.canonical_json import canonical_json_bytes
from services.preflight_common import validate_lineage
from services.domain_contract.validator import validate_project
from services.jsonld_validation import JsonLdValidatorAdapterError, validate_local_jsonld_text
from services.step4b_preflight.geo_validation import validate_geo_markup, validate_section_jsonld_correspondence
from services.step4b_preflight.section_validation import validate_conversion, validate_sections


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


def staging_evidence_sha256(value: dict[str, object]) -> str:
    payload = dict(value)
    payload.pop("staging_sha256", None)
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _validate_staging_evidence(page: dict[str, object], staging: dict[str, object]) -> list[dict[str, object]]:
    errors: list[dict[str, object]] = []
    checks = staging.get("checks")
    if not isinstance(checks, list) or not all(isinstance(check, dict) for check in checks):
        return errors
    required_tools = {"crawl", "lighthouse", "axe", "visual"}
    tools = [check.get("tool") for check in checks]
    if len(checks) != 4 or any(tools.count(tool) != 1 for tool in required_tools):
        errors.append({"code": "ERROR_STEP4B_STAGING_TOOL_COVERAGE", "message": "Staging evidence requires each of crawl, lighthouse, axe and visual exactly once.", "path": ["staging_evidence", "checks"]})
    else:
        checks_by_tool = {check["tool"]: check for check in checks}
        accessibility = page.get("accessibility")
        responsive = page.get("responsive")
        if (
            not isinstance(accessibility, dict)
            or not isinstance(responsive, dict)
            or accessibility.get("axe_evidence_id") != checks_by_tool["axe"].get("evidence_id")
            or responsive.get("visual_evidence_id") != checks_by_tool["visual"].get("evidence_id")
        ):
            errors.append({"code": "ERROR_STEP4B_STAGING_PAGE_EVIDENCE_MISMATCH", "message": "Page accessibility and visual evidence IDs must bind the corresponding staging checks.", "path": ["page_spec", "accessibility"]})
    check_evidence_ids = [check.get("evidence_id") for check in checks]
    evidence_ids = staging.get("evidence_ids")
    if not isinstance(evidence_ids, list) or len(evidence_ids) != 4 or any(evidence_ids.count(evidence_id) != 1 for evidence_id in evidence_ids) or any(check_evidence_ids.count(evidence_id) != 1 for evidence_id in check_evidence_ids) or any(evidence_id not in check_evidence_ids for evidence_id in evidence_ids) or any(evidence_id not in evidence_ids for evidence_id in check_evidence_ids):
        errors.append({"code": "ERROR_STEP4B_STAGING_EVIDENCE_COVERAGE", "message": "Staging evidence IDs must exactly cover the four check evidence IDs.", "path": ["staging_evidence", "evidence_ids"]})
    page_hash = page.get("content_sha256")
    staging_hash = staging.get("content_sha256")
    if any(check.get("content_sha256") != page_hash or check.get("content_sha256") != staging_hash for check in checks):
        errors.append({"code": "ERROR_STEP4B_STAGING_CONTENT_BINDING", "message": "Every staging check must bind the page and staging content hash.", "path": ["staging_evidence", "checks"]})
    for index, check in enumerate(checks):
        provenance = check.get("provenance")
        if not isinstance(provenance, dict) or provenance.get("classification") not in {"local_simulated", "external_report"} or not isinstance(provenance.get("source"), str) or not provenance["source"].strip():
            errors.append({"code": "ERROR_STEP4B_STAGING_PROVENANCE_INVALID", "message": "Every staging check requires honest provenance.", "path": ["staging_evidence", "checks", index, "provenance"]})
    if staging.get("staging_sha256") != staging_evidence_sha256(staging):
        errors.append({"code": "ERROR_STEP4B_STAGING_HASH_MISMATCH", "message": "Staging evidence hash must bind canonical staging evidence bytes.", "path": ["staging_evidence", "staging_sha256"]})
    return errors


def validate_step4b_candidate(bundle: dict[str, object], root: Path | None = None) -> dict[str, object]:
    root = root or _root()
    page = bundle.get("page_spec")
    staging = bundle.get("staging_evidence")
    errors = _errors("step-4b-page-spec.schema.json", page, "ERROR_STEP4B_PAGE_INVALID", root)
    errors.extend(_errors("staging-evidence.schema.json", staging, "ERROR_STEP4B_STAGING_INVALID", root))
    if isinstance(page, dict) and isinstance(staging, dict):
        errors.extend(validate_sections(page))
        errors.extend(validate_conversion(page))
        errors.extend(validate_geo_markup(page))
        errors.extend(validate_section_jsonld_correspondence(page))
        service_area = page.get("service_area", {})
        if isinstance(service_area, dict) and service_area.get("mode") == "service_area" and service_area.get("address_claims"):
            errors.append({"code": "ERROR_STEP4B_SERVICE_AREA_UNSAFE", "message": "Service-area pages cannot claim a physical address.", "path": ["page_spec", "service_area", "address_claims"]})
        errors.extend(_validate_staging_evidence(page, staging))
        calculated_hash = page_content_sha256(page)
        if page.get("content_sha256") != calculated_hash or staging.get("content_sha256") != calculated_hash:
            errors.append({"code": "ERROR_STEP4B_CONTENT_HASH_MISMATCH", "message": "Page and staging evidence must bind the same content hash.", "path": ["content_sha256"]})
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
                references = set(service_area.get("service_area_ids", []))
                allowed_areas = set(deployment["service_area_ids"])
                if not references.issubset(allowed_areas):
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
