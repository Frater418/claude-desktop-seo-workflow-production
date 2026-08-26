from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker

from services.deterministic_output_fields import STEP4B_PAGE_CONTRACT, bind_deterministic_output_fields
from services.jsonld_validation import JsonLdValidatorAdapterError, validate_local_jsonld_text
from services.step4b_preflight.geo_validation import validate_geo_markup, validate_section_jsonld_correspondence
from services.step4b_preflight.section_validation import validate_conversion, validate_sections


@dataclass(frozen=True, slots=True)
class LocalStagingReadinessError(RuntimeError):
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def local_staging_readiness(page_spec: Mapping[str, Any], root: Path) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    """Validate one typed page locally and return explicit simulation reports."""

    page = copy.deepcopy(dict(page_spec))
    accessibility = page.get("accessibility")
    responsive = page.get("responsive")
    if isinstance(accessibility, dict):
        accessibility["axe_evidence_id"] = "evidence-local-axe-placeholder"
    if isinstance(responsive, dict):
        responsive["visual_evidence_id"] = "evidence-local-visual-placeholder"
    page = bind_deterministic_output_fields(
        "4b",
        [{"contract_id": STEP4B_PAGE_CONTRACT, "content": page}],
    )[0]["content"]

    schema = json.loads((root / "standards/outputs/step-4b-page-spec.schema.json").read_text(encoding="utf-8"))
    schema_errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(page),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    semantic_errors = [
        *validate_sections(page),
        *validate_conversion(page),
        *validate_geo_markup(page),
        *validate_section_jsonld_correspondence(page),
    ]
    service_area = page.get("service_area")
    if isinstance(service_area, dict) and service_area.get("mode") == "service_area" and service_area.get("address_claims"):
        semantic_errors.append({"code": "ERROR_STEP4B_SERVICE_AREA_UNSAFE", "message": "Service-area pages cannot claim a physical address."})
    jsonld = page.get("jsonld")
    graph = jsonld.get("graph") if isinstance(jsonld, dict) else None
    if isinstance(graph, dict):
        graph_text = json.dumps(graph, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        try:
            validation = validate_local_jsonld_text(f'<script type="application/ld+json">{graph_text}</script>', root=root)
        except JsonLdValidatorAdapterError as error:
            raise LocalStagingReadinessError(error.code, str(error)) from error
        if not validation["valid"]:
            semantic_errors.extend(validation["errors"])
    if schema_errors or semantic_errors:
        first = schema_errors[0].message if schema_errors else str(semantic_errors[0].get("message", "Local staging readiness failed."))
        raise LocalStagingReadinessError("ERROR_LOCAL_STAGING_READINESS_FAILED", first)

    sections = page["sections"]
    reports = (
        {
            "tool": "crawl",
            "classification": "local_simulated",
            "source": "Heartweb typed-page structural crawl simulation; no external crawler was executed.",
            "findings": {"section_count": len(sections), "canonical_url": page["canonical_url"], "sibling_link_count": len(page["sibling_links"])},
        },
        {
            "tool": "lighthouse",
            "classification": "local_simulated",
            "source": "Heartweb static performance-readiness simulation; Lighthouse CLI was not executed.",
            "findings": {"external_dependencies_declared": False, "executable_tracking_declared": False, "standalone_renderer_required": True},
        },
        {
            "tool": "axe",
            "classification": "local_simulated",
            "source": "Heartweb typed accessibility-contract simulation; axe was not executed in a browser.",
            "findings": {"accessibility_contract_present": True, "form_count": len(page["forms"]), "consent_required": page["consent"]["required"]},
        },
        {
            "tool": "visual",
            "classification": "local_simulated",
            "source": "Heartweb responsive-contract simulation; screenshot and visual-diff tools were not executed.",
            "findings": {"responsive_contract_present": True, "section_roles": [section["role"] for section in sections]},
        },
    )
    return page, reports
