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


def _design_binding_errors(design: object) -> list[dict]:
    if not isinstance(design, dict):
        return []
    brand_consistency = design.get("brand_consistency")
    if not isinstance(brand_consistency, dict):
        return []
    declared_evidence = set(design.get("evidence_ids", []))
    brand_evidence = set(brand_consistency.get("evidence_ids", []))
    if brand_evidence <= declared_evidence:
        return []
    return [_error("ERROR_STEP1C_DESIGN_BRAND_EVIDENCE_INVALID", "Brand consistency evidence must be declared by the design artifact.", ["design", "brand_consistency", "evidence_ids"])]


def _content_evidence_errors(template: dict, index: int) -> list[dict]:
    content = template["content"]
    declared_evidence = set(template["evidence_ids"])
    evidence_sources = [
        (["hero", "primary_cta"], content["hero"]["primary_cta"]),
        (["editorial"], content["editorial"]),
        (["heartpiece"], content["heartpiece"]),
        (["final_cta", "primary_cta"], content["final_cta"]["primary_cta"]),
    ]
    evidence_sources.extend((["quick_facts", "facts", fact_index], fact) for fact_index, fact in enumerate(content["quick_facts"]["facts"]))
    evidence_sources.extend((["process", "steps", step_index], step) for step_index, step in enumerate(content["process"]["steps"]))
    evidence_sources.extend((["social_proof", "entries", entry_index], entry) for entry_index, entry in enumerate(content["social_proof"]["entries"]))
    evidence_sources.extend((["faq", "items", item_index], item) for item_index, item in enumerate(content["faq"]["items"]))
    return [
        _error("ERROR_STEP1C_TEMPLATE_CONTENT_EVIDENCE_INVALID", "Content evidence must be declared by the template artifact.", ["templates", index, "content", *path, "evidence_ids"])
        for path, source in evidence_sources
        if not set(source["evidence_ids"]) <= declared_evidence
    ]


def _root_link_errors(template: dict, index: int) -> list[dict]:
    links = template["links"]
    pairs = [(link["target_content_id"], link["relationship"]) for link in links]
    hrefs = [link["href"] for link in links]
    if len(pairs) == len(set(pairs)) and len(hrefs) == len(set(hrefs)):
        return []
    return [_error("ERROR_STEP1C_TEMPLATE_LINK_REGISTRY_INVALID", "Root links must use unique target relationships and canonical routes.", ["templates", index, "links"])]


def _content_link_errors(template: dict, index: int) -> list[dict]:
    content = template["content"]
    declared_links = {(link["target_content_id"], link["relationship"]) for link in template["links"]}
    link_sources = [
        (["hero", "primary_cta"], content["hero"]["primary_cta"]["target_content_id"], "vertical"),
        (["final_cta", "primary_cta"], content["final_cta"]["primary_cta"]["target_content_id"], "vertical"),
    ]
    link_sources.extend((["grouped_cluster_links", "groups", group_index, "links", link_index], link["target_content_id"], link["relationship"]) for group_index, group in enumerate(content["grouped_cluster_links"]["groups"]) for link_index, link in enumerate(group["links"]))
    link_sources.extend((["cross_pillar_links", "links", link_index], link["target_content_id"], link["relationship"]) for link_index, link in enumerate(content["cross_pillar_links"]["links"]))
    errors = [
        _error("ERROR_STEP1C_TEMPLATE_LINK_REFERENCE_INVALID", "Content links must bind to a declared canonical target and relationship.", ["templates", index, "content", *path, "target_content_id"])
        for path, target_content_id, relationship in link_sources
        if (target_content_id, relationship) not in declared_links
    ]
    if not content["cross_pillar_links"]["links"] and any(link["relationship"] == "horizontal" for link in template["links"]):
        errors.append(_error("ERROR_STEP1C_TEMPLATE_LINK_REFERENCE_INVALID", "Cross-pillar links are required when horizontal targets are declared.", ["templates", index, "content", "cross_pillar_links", "links"]))
    return errors


def _faq_binding_errors(template: dict, index: int) -> list[dict]:
    faq_reference_ids = {reference["reference_id"] for reference in template["jsonld_references"] if reference["type"] == "FAQPage"}
    return [
        _error("ERROR_STEP1C_TEMPLATE_JSONLD_BINDING_INVALID", "FAQ items must bind to a declared FAQPage JSON-LD reference.", ["templates", index, "content", "faq", "items", item_index, "jsonld_reference_id"])
        for item_index, item in enumerate(template["content"]["faq"]["items"])
        if item["jsonld_reference_id"] not in faq_reference_ids
    ]


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
    if errors:
        return errors
    errors.extend(_root_link_errors(template, index))
    errors.extend(_content_evidence_errors(template, index))
    errors.extend(_content_link_errors(template, index))
    errors.extend(_faq_binding_errors(template, index))
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
    if not errors:
        errors.extend(_design_binding_errors(design))
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
