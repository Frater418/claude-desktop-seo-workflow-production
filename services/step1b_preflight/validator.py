from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker
from services.preflight_common import validate_lineage


def _schema() -> dict:
    path = Path(__file__).resolve().parents[2] / "standards" / "outputs" / "step-1b-architecture.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _error(code: str, message: str, path: list[str | int]) -> dict:
    return {"code": code, "message": message, "path": path, "remediation": "Correct the canonical Step 1B architecture and rerun preflight."}


def _schema_errors(value: object) -> list[dict]:
    validator = Draft202012Validator(_schema(), format_checker=FormatChecker())
    return [_error("ERROR_STEP1B_ARCHITECTURE_INVALID", error.message, list(error.absolute_path)) for error in validator.iter_errors(value)]


def _decision_errors(architecture: dict, approved_content_ids: list[str]) -> list[dict]:
    errors: list[dict] = []
    decisions = architecture.get("content_decisions", [])
    identifiers = [item.get("content_id") for item in decisions if isinstance(item, dict)]
    approved = set(approved_content_ids)
    if len(identifiers) != len(set(identifiers)) or set(identifiers) != approved:
        errors.append(_error("ERROR_STEP1B_DECISION_COVERAGE_INVALID", "Every approved pillar and cluster must have exactly one architecture decision.", ["content_decisions"]))
    for index, item in enumerate(decisions):
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        canonical = item.get("canonical_url", "")
        parsed = urlparse(canonical)
        if not isinstance(url, str) or not isinstance(canonical, str) or parsed.path != url or not parsed.scheme or not parsed.netloc:
            errors.append(_error("ERROR_STEP1B_CANONICAL_INVALID", "Canonical URL must be absolute and match the decision URL.", ["content_decisions", index]))
    active = [item for item in decisions if isinstance(item, dict) and item.get("decision") != "backlog"]
    urls = [item.get("url") for item in active]
    canonicals = [item.get("canonical_url") for item in active]
    if len(urls) != len(set(urls)) or len(canonicals) != len(set(canonicals)):
        errors.append(_error("ERROR_STEP1B_URL_CONFLICT", "Active content decisions must not share a URL or canonical URL.", ["content_decisions"]))
    return errors


def _presentation_errors(architecture: dict, approved_content_ids: list[str]) -> list[dict]:
    errors: list[dict] = []
    approved = set(approved_content_ids)
    decisions = [item for item in architecture.get("content_decisions", []) if isinstance(item, dict)]
    decisions_by_id = {item.get("content_id"): item for item in decisions if isinstance(item.get("content_id"), str)}
    legend = [item for item in architecture.get("page_type_legend", []) if isinstance(item, dict)]
    legend_codes = [item.get("code") for item in legend]
    page_types = {item.get("page_type") for item in decisions if isinstance(item.get("page_type"), str)}
    if len(legend_codes) != len(set(legend_codes)) or set(legend_codes) != page_types:
        errors.append(_error("ERROR_STEP1B_PAGE_TYPE_LEGEND_INVALID", "Page type legend codes must be unique and cover exactly the page types used by decisions.", ["page_type_legend"]))
    for index, item in enumerate(decisions):
        content_id = item.get("content_id")
        parent_id = item.get("parent_content_id")
        if item.get("page_type") == "cluster_page" and (
            not isinstance(parent_id, str)
            or parent_id == content_id
            or parent_id not in decisions_by_id
            or decisions_by_id[parent_id].get("page_type") != "pillar_page"
        ):
            errors.append(_error("ERROR_STEP1B_HIERARCHY_INVALID", "Cluster pages must name a distinct approved pillar page parent.", ["content_decisions", index, "parent_content_id"]))
    confirmation_counts = {content_id: 0 for content_id, item in decisions_by_id.items() if item.get("presentation_status") == "open"}
    for index, confirmation in enumerate(architecture.get("open_confirmations", [])):
        if not isinstance(confirmation, dict):
            continue
        for content_id in confirmation.get("content_ids", []):
            if content_id not in approved or content_id not in confirmation_counts:
                errors.append(_error("ERROR_STEP1B_OPEN_CONFIRMATION_INVALID", "Open confirmations may reference only approved decisions with open presentation status.", ["open_confirmations", index, "content_ids"]))
                continue
            confirmation_counts[content_id] += 1
    if any(count != 1 for count in confirmation_counts.values()):
        errors.append(_error("ERROR_STEP1B_OPEN_CONFIRMATION_INVALID", "Every open presentation decision must have exactly one open confirmation.", ["open_confirmations"]))
    return errors


def _link_errors(architecture: dict, approved_content_ids: list[str]) -> list[dict]:
    errors: list[dict] = []
    approved = set(approved_content_ids)
    links = architecture.get("link_graph", [])
    decisions_by_id = {
        item.get("content_id"): item
        for item in architecture.get("content_decisions", [])
        if isinstance(item, dict) and isinstance(item.get("content_id"), str)
    }
    for index, link in enumerate(links):
        if not isinstance(link, dict) or {link.get("from_content_id"), link.get("to_content_id")} - approved:
            errors.append(_error("ERROR_STEP1B_LINK_GRAPH_INVALID", "Link graph may only connect approved content.", ["link_graph", index]))
            continue
        source = link["from_content_id"]
        target = link["to_content_id"]
        relationship = link["relationship"]
        source_type = decisions_by_id.get(source, {}).get("page_type")
        target_type = decisions_by_id.get(target, {}).get("page_type")
        if relationship == "vertical" and not (source_type == "pillar_page" and target_type == "cluster_page" and decisions_by_id[target].get("parent_content_id") == source):
            errors.append(_error("ERROR_STEP1B_LINK_GRAPH_INVALID", "Vertical links must lead from a pillar to its cluster.", ["link_graph", index]))
        if relationship == "horizontal" and not (source_type == "pillar_page" and target_type == "pillar_page" and source != target):
            errors.append(_error("ERROR_STEP1B_LINK_GRAPH_INVALID", "Horizontal links must connect distinct pillars.", ["link_graph", index]))
    clusters = {identifier for identifier, item in decisions_by_id.items() if identifier in approved and item.get("page_type") == "cluster_page"}
    linked_clusters = {link.get("to_content_id") for link in links if isinstance(link, dict) and link.get("relationship") == "vertical"}
    if not clusters.issubset(linked_clusters):
        errors.append(_error("ERROR_STEP1B_LINK_GRAPH_INVALID", "Every approved cluster needs an inbound vertical link.", ["link_graph"]))
    pillars = {identifier for identifier, item in decisions_by_id.items() if identifier in approved and item.get("page_type") == "pillar_page"}
    horizontal_pillars = {
        identifier
        for link in links
        if isinstance(link, dict) and link.get("relationship") == "horizontal"
        for identifier in (link.get("from_content_id"), link.get("to_content_id"))
        if identifier in pillars
    }
    if len(pillars) > 1 and horizontal_pillars != pillars:
        errors.append(_error("ERROR_STEP1B_LINK_GRAPH_INVALID", "Every approved pillar needs a horizontal link when multiple pillars exist.", ["link_graph"]))
    return errors


def validate_step1b_candidate(architecture: object, approved_content_ids: list[str]) -> dict:
    errors = _schema_errors(architecture)
    if not isinstance(architecture, dict) or not isinstance(approved_content_ids, list):
        return {"valid": False, "errors": errors or [_error("ERROR_STEP1B_INPUT_INVALID", "Architecture and approved content IDs are required.", [])]}
    errors.extend(_decision_errors(architecture, approved_content_ids))
    errors.extend(_presentation_errors(architecture, approved_content_ids))
    errors.extend(_link_errors(architecture, approved_content_ids))
    unique = {(item["code"], tuple(str(part) for part in item["path"]), item["message"]): item for item in errors}
    return {"valid": not unique, "errors": [unique[key] for key in sorted(unique)]}


def validate_step1b_preflight(bundle: object, approved_content_ids: list[str] | None = None) -> dict:
    candidate = bundle.get("candidate", bundle) if isinstance(bundle, dict) else bundle
    approved = bundle.get("approved_content_ids", approved_content_ids) if isinstance(bundle, dict) else approved_content_ids
    result = validate_step1b_candidate(candidate, approved if isinstance(approved, list) else [])
    lineage_bundle = dict(bundle) if isinstance(bundle, dict) else {"candidate": candidate}
    result["errors"].extend(validate_lineage(lineage_bundle, "1b", "1", "GATE-1", candidate_schema_name="step-1b-architecture.schema.json"))
    result["valid"] = not result["errors"]
    return result
