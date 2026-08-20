from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from services.preflight_common import validate_lineage


def _schema(name: str) -> dict:
    path = Path(__file__).resolve().parents[2] / "standards" / "outputs" / name
    return json.loads(path.read_text(encoding="utf-8"))


def _error(code: str, message: str, path: list[str | int]) -> dict:
    return {"code": code, "message": message, "path": path, "remediation": "Correct the canonical Step 1C design or template artifact and rerun preflight."}


def _schema_errors(value: object, name: str, code: str, prefix: list[str | int]) -> list[dict]:
    validator = Draft202012Validator(_schema(name), format_checker=FormatChecker())
    return [_error(code, error.message, prefix + list(error.absolute_path)) for error in validator.iter_errors(value)]


def _design_errors(design: object) -> list[dict]:
    return _schema_errors(design, "step-1c-design-system.schema.json", "ERROR_STEP1C_DESIGN_INVALID", ["design"])


def _template_errors(template: object, index: int) -> list[dict]:
    errors = _schema_errors(template, "step-1c-template.schema.json", "ERROR_STEP1C_TEMPLATE_INVALID", ["templates", index])
    if not isinstance(template, dict):
        return errors
    location = template.get("location_context")
    if isinstance(location, dict):
        physical_claim_fields = {"physical_address", "nap", "gbp_claim"}
        if location.get("claim_type") == "service_area" and physical_claim_fields.intersection(location):
            errors.append(_error("ERROR_STEP1C_LOCATION_CLAIM_INVALID", "Service-area evidence cannot support physical address, NAP, or GBP claims.", ["templates", index, "location_context"]))
        if location.get("claim_type") == "physical_location" and not location.get("physical_location_evidence_ids"):
            errors.append(_error("ERROR_STEP1C_LOCATION_CLAIM_INVALID", "Physical-location claims require physical-location evidence.", ["templates", index, "location_context"]))
    accessibility = template.get("accessibility")
    if not isinstance(accessibility, dict) or not accessibility.get("landmarks") or not accessibility.get("skip_link"):
        errors.append(_error("ERROR_STEP1C_ACCESSIBILITY_INVALID", "Templates require landmarks and a skip link.", ["templates", index, "accessibility"]))
    if not template.get("jsonld_references"):
        errors.append(_error("ERROR_STEP1C_JSONLD_REFERENCE_INVALID", "Templates require evidence-bound JSON-LD references.", ["templates", index, "jsonld_references"]))
    return errors


def _lineage_errors(design: object, templates: list[object]) -> list[dict]:
    if not isinstance(design, dict):
        return []
    artifact_id = design.get("artifact_id")
    errors: list[dict] = []
    for index, template in enumerate(templates):
        if not isinstance(template, dict):
            continue
        if template.get("project_id") != design.get("project_id") or template.get("deployment_id") != design.get("deployment_id"):
            errors.append(_error("ERROR_STEP1C_LINEAGE_INVALID", "Design and templates must bind the same project and deployment.", ["templates", index]))
        if artifact_id not in template.get("source_artifact_ids", []):
            errors.append(_error("ERROR_STEP1C_LINEAGE_INVALID", "Every template must reference the design-system artifact.", ["templates", index, "source_artifact_ids"]))
    return errors


def validate_step1c_candidate(design: object, templates: object) -> dict:
    template_values = templates if isinstance(templates, list) else []
    errors = _design_errors(design)
    if not isinstance(templates, list) or not templates:
        errors.append(_error("ERROR_STEP1C_INPUT_INVALID", "At least one template is required.", ["templates"]))
    for index, template in enumerate(template_values):
        errors.extend(_template_errors(template, index))
    errors.extend(_lineage_errors(design, template_values))
    unique = {(item["code"], tuple(str(part) for part in item["path"]), item["message"]): item for item in errors}
    return {"valid": not unique, "errors": [unique[key] for key in sorted(unique)]}


def validate_step1c_preflight(bundle: object, templates: object | None = None) -> dict:
    if isinstance(bundle, dict) and "design" in bundle:
        design = bundle["design"]
        template_values = bundle.get("templates")
        lineage_bundle = {**bundle, "candidate": design}
    else:
        design = bundle
        template_values = templates
        lineage_bundle = {"candidate": design}
    result = validate_step1c_candidate(design, template_values)
    result["errors"].extend(validate_lineage(lineage_bundle, "1c", "1b", "GATE-1B", candidate_schema_name="step-1c-design-system.schema.json"))
    result["valid"] = not result["errors"]
    return result
