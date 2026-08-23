from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse


_GEO_ROLES = frozenset({"definition", "evidence", "comparison"})
_APPROVED_CLASSES = frozenset(
    {
        "definition-block",
        "evidence-container",
        "comparison-table-wrapper",
        "comparison-table",
        "speakable-section",
        "badge-datahub",
    }
)
_REQUIRED_CLASSES = {
    "definition": frozenset({"definition-block"}),
    "evidence": frozenset({"evidence-container"}),
    "comparison": frozenset({"comparison-table-wrapper"}),
}
_MICRODATA_FIELDS = {
    "definition": frozenset({"itemtype", "heading_itemprop", "body_itemprop"}),
    "evidence": frozenset({"itemtype", "heading_itemprop", "body_itemprop", "content_itemprop"}),
    "comparison": frozenset({"itemtype", "heading_itemprop", "table_itemprop"}),
}
_MICRODATA_ITEMPROPS = {
    "definition": {"heading_itemprop": "name", "body_itemprop": "description"},
    "evidence": {"heading_itemprop": "name", "body_itemprop": "description", "content_itemprop": ("additionalProperty", "citation")},
    "comparison": {"heading_itemprop": "name", "table_itemprop": "itemListElement"},
}


def _error(code: str, message: str, path: list[str | int]) -> dict[str, object]:
    return {"code": code, "message": message, "path": path}


def _http_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _valid_microdata(role: object, value: object) -> bool:
    if not isinstance(role, str) or not isinstance(value, dict):
        return False
    itemtype = value.get("itemtype")
    if set(value) != _MICRODATA_FIELDS[role] or not isinstance(itemtype, str) or not itemtype.startswith("https://schema.org/"):
        return False
    for name, allowed in _MICRODATA_ITEMPROPS[role].items():
        if isinstance(allowed, tuple):
            if value.get(name) not in allowed:
                return False
        elif value.get(name) != allowed:
            return False
    return True


def _schema_type(itemtype: object) -> str | None:
    if not isinstance(itemtype, str) or not itemtype.startswith("https://schema.org/"):
        return None
    return itemtype.rsplit("/", 1)[-1]


def validate_geo_markup(page: dict[str, object]) -> list[dict[str, object]]:
    sections = page.get("sections")
    if not isinstance(sections, list):
        return []
    errors: list[dict[str, object]] = []
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            continue
        role = section.get("role")
        classes = section.get("component_classes")
        if not isinstance(classes, list) or len(classes) != len(set(classes)) or any(item not in _APPROVED_CLASSES for item in classes):
            errors.append(_error("ERROR_STEP4B_GEO_MARKUP_INVALID", "Section component classes must be approved design-system selectors.", ["page_spec", "sections", index, "component_classes"]))
        if role not in _GEO_ROLES:
            continue
        if not isinstance(classes, list) or not _REQUIRED_CLASSES[role].issubset(classes):
            errors.append(_error("ERROR_STEP4B_GEO_MARKUP_INVALID", "GEO section is missing its required approved component class.", ["page_spec", "sections", index, "component_classes"]))
        microdata = section.get("microdata")
        if not _valid_microdata(role, microdata):
            errors.append(_error("ERROR_STEP4B_GEO_MARKUP_INVALID", "GEO section requires closed visible Microdata metadata.", ["page_spec", "sections", index, "microdata"]))
        if role == "comparison":
            content = section.get("content")
            table = content.get("table") if isinstance(content, dict) else None
            table_classes = table.get("component_classes") if isinstance(table, dict) else None
            if not isinstance(table_classes, list) or "comparison-table" not in table_classes:
                errors.append(_error("ERROR_STEP4B_GEO_MARKUP_INVALID", "Comparison table requires its own approved table class.", ["page_spec", "sections", index, "content", "table", "component_classes"]))
    return errors


def validate_section_jsonld_correspondence(page: dict[str, object]) -> list[dict[str, object]]:
    sections = page.get("sections")
    graph = page.get("jsonld")
    graph = graph.get("graph") if isinstance(graph, dict) else None
    nodes = graph.get("@graph") if isinstance(graph, dict) else None
    if not isinstance(sections, list) or not isinstance(nodes, list):
        return []
    section_ids = [section.get("schema_node_id") for section in sections if isinstance(section, dict)]
    node_ids = [node.get("@id") for node in nodes if isinstance(node, dict)]
    section_counts = Counter(section_ids)
    node_counts = Counter(node_ids)
    missing_or_duplicate = any(not _http_url(identifier) or count != 1 or node_counts[identifier] != 1 for identifier, count in section_counts.items())
    graph_has_unidentified_node = len(node_ids) != len(nodes) or any(not _http_url(identifier) for identifier in node_ids)
    extra_node_ids = set(node_ids) - set(section_ids)
    if missing_or_duplicate or graph_has_unidentified_node or len(extra_node_ids) != 1:
        return [_error("ERROR_STEP4B_SECTION_JSONLD_MISMATCH", "Each visible section must bind exactly once to a JSON-LD graph node, with only one page or entity root node allowed.", ["page_spec", "sections"])]
    nodes_by_id = {node["@id"]: node for node in nodes if isinstance(node, dict)}
    for section in sections:
        if not isinstance(section, dict) or section.get("role") not in _GEO_ROLES:
            continue
        node = nodes_by_id[section["schema_node_id"]]
        microdata = section.get("microdata")
        if not _valid_microdata(section["role"], microdata):
            continue
        itemtype = microdata.get("itemtype") if isinstance(microdata, dict) else None
        if _schema_type(itemtype) != node.get("@type"):
            return [_error("ERROR_STEP4B_SECTION_JSONLD_MISMATCH", "Typed visible Microdata must use the exact Schema.org type of its same-ID JSON-LD graph node.", ["page_spec", "sections"])]
    return []
