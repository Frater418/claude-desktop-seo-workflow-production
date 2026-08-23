from __future__ import annotations


ROLES = frozenset({"hero", "direct_answer", "definition", "evidence", "comparison", "service_area", "faq", "conversion", "related_links"})


def _error(code: str, message: str, path: list[str]) -> dict[str, object]:
    return {"code": code, "message": message, "path": path}


def validate_sections(page: dict[str, object]) -> list[dict[str, object]]:
    sections = page.get("sections")
    if not isinstance(sections, list):
        return [_error("ERROR_STEP4B_SECTION_STRUCTURE_INVALID", "Page sections must be a typed list.", ["page_spec", "sections"])]
    roles = [section.get("role") for section in sections if isinstance(section, dict)]
    identifiers = [section.get("section_id") for section in sections if isinstance(section, dict)]
    if set(roles) != ROLES or len(roles) != len(ROLES) or len(set(roles)) != len(roles):
        return [_error("ERROR_STEP4B_SECTION_STRUCTURE_INVALID", "Page requires exactly one of every approved semantic section role.", ["page_spec", "sections"])]
    if len(identifiers) != len(set(identifiers)):
        return [_error("ERROR_STEP4B_SECTION_STRUCTURE_INVALID", "Page section IDs must be unique.", ["page_spec", "sections"])]
    return []


def validate_conversion(page: dict[str, object]) -> list[dict[str, object]]:
    ctas = page.get("ctas", [])
    forms = page.get("forms", [])
    links = page.get("sibling_links", [])
    if not all(isinstance(item, dict) for item in [*ctas, *forms, *links]):
        return [_error("ERROR_STEP4B_CONVERSION_STRUCTURE_INVALID", "Conversion authorities must be typed objects.", ["page_spec"])]
    cta_ids = [item.get("cta_id") for item in ctas]
    form_ids = [item.get("form_id") for item in forms]
    link_ids = [item.get("link_id") for item in links]
    if any(len(values) != len(set(values)) for values in [cta_ids, form_ids, link_ids]):
        return [_error("ERROR_STEP4B_CONVERSION_STRUCTURE_INVALID", "CTA, form and sibling-link authorities must be unique.", ["page_spec"])]
    conversion = page.get("conversion", {})
    sections = page.get("sections", [])
    conversion_section = next((item for item in sections if isinstance(item, dict) and item.get("role") == "conversion"), None)
    if not isinstance(conversion, dict) or not isinstance(conversion_section, dict):
        return [_error("ERROR_STEP4B_CONVERSION_STRUCTURE_INVALID", "Conversion authority and section are required.", ["page_spec", "conversion"])]
    content = conversion_section.get("content", {})
    references = [conversion.get("primary_cta_id"), *(option.get("cta_id") for option in conversion.get("contact_options", []) if isinstance(option, dict)), *(content.get("cta_ids", []) if isinstance(content, dict) else [])]
    form_references = content.get("form_ids", []) if isinstance(content, dict) else []
    related = next((item for item in sections if isinstance(item, dict) and item.get("role") == "related_links"), {})
    link_references = related.get("content", {}).get("sibling_link_ids", []) if isinstance(related, dict) and isinstance(related.get("content"), dict) else []
    hero = next((item for item in sections if isinstance(item, dict) and item.get("role") == "hero"), {})
    if isinstance(hero, dict) and isinstance(hero.get("content"), dict):
        references.append(hero["content"].get("primary_cta_id"))
    if conversion.get("final_cta_section_id") != conversion_section.get("section_id") or not all(reference in cta_ids for reference in references) or not all(reference in form_ids for reference in form_references) or not all(reference in link_ids for reference in link_references):
        return [_error("ERROR_STEP4B_CONVERSION_STRUCTURE_INVALID", "Every CTA, form and sibling-link reference must resolve exactly once.", ["page_spec", "conversion"])]
    if any(item.get("form_id") not in form_ids for item in ctas):
        return [_error("ERROR_STEP4B_CONVERSION_STRUCTURE_INVALID", "Each CTA must reference an authoritative form.", ["page_spec", "ctas"])]
    return []
