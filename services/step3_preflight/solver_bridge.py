"""Deterministic conversion from released Step 2 evidence to Step 3 fields."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Mapping, TypeAlias

import mcp as mcp_sdk

_LOCAL_MCP_PATH = str(Path(__file__).resolve().parents[2] / "mcp")
if _LOCAL_MCP_PATH not in mcp_sdk.__path__:
    mcp_sdk.__path__.append(_LOCAL_MCP_PATH)

from mcp.tools.capacity_matrix_solver import CapacityValidationError, solve_capacity_plan  # noqa: E402
from services.step2_preflight.validator import validate_step2_candidate


JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
_MACHINE_FIELD_NAMES = (
    "weeks",
    "mandatory_item_ids",
    "backlog_item_ids",
    "vertical_links",
    "horizontal_links",
)


class SolverBridgeError(ValueError):
    """Raised when released Step 2 evidence cannot produce a closed plan."""


def _canonical(value: Mapping[str, JsonValue]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _candidate_rows(candidate: Mapping[str, JsonValue]) -> list[tuple[str, Mapping[str, JsonValue]]]:
    pillars = candidate.get("pillars")
    if not isinstance(pillars, list):
        return []
    return [
        (pillar["pillar_id"], row)
        for pillar in pillars
        if isinstance(pillar, dict) and isinstance(pillar.get("pillar_id"), str)
        for row in pillar.get("rows", [])
        if isinstance(row, dict)
    ]


def step2_solver_projection(step2_candidate: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """Return the complete canonical solver input from verified Step 2 evidence."""
    items = [
        {
            "item_id": row["evidence_id"],
            "pillar": pillar_id,
            "title": row["title"],
            "keyword": row["keyword"],
            "search_volume": row["search_volume"],
            "difficulty": row["difficulty"],
            "category": row["category"],
            "content_type": row["content_type"],
            "geo_type": row["geo_type"],
            "engine_target": row["engine_target"],
            "information_gain": row["information_gain"],
            "entity_density": row["entity_density"],
            "business_relevance": row["business_relevance"],
            "is_mandatory": row["mandatory_location_policy"]["state"] == "required",
            "provider": row["provider"],
            "raw_response_sha256": row["raw_response_sha256"],
        }
        for pillar_id, row in _candidate_rows(step2_candidate)
    ]
    return {"items": sorted(items, key=lambda item: (item["pillar"], item["keyword"], item["item_id"]))}


def _links(items: list[dict[str, JsonValue]]) -> tuple[list[dict[str, JsonValue]], list[dict[str, JsonValue]]]:
    vertical = sorted(
        (
            {"source_item_id": item["item_id"], "target_pillar_id": item["pillar"]}
            for item in items
        ),
        key=lambda link: (link["source_item_id"], link["target_pillar_id"]),
    )
    by_pillar: defaultdict[str, list[str]] = defaultdict(list)
    for item in items:
        by_pillar[item["pillar"]].append(item["item_id"])
    horizontal = [
        {"source_item_id": item_id, "target_item_id": sorted(sibling_ids)[(index + 1) % len(sibling_ids)]}
        for sibling_ids in by_pillar.values()
        if len(sibling_ids) >= 2
        for index, item_id in enumerate(sorted(sibling_ids))
    ]
    return vertical, sorted(horizontal, key=lambda link: (link["source_item_id"], link["target_item_id"]))


def _require_partition(input_ids: list[str], weeks: list[dict[str, JsonValue]], backlog_ids: list[str]) -> None:
    scheduled_ids = [item_id for week in weeks for item_id in week["item_ids"]]
    if len(input_ids) != len(scheduled_ids) + len(backlog_ids) or set(input_ids) != set(scheduled_ids) | set(backlog_ids):
        raise SolverBridgeError("ERROR_STEP3_SOLVER_PARTITION_INVALID")
    if len(scheduled_ids) != len(set(scheduled_ids)) or len(backlog_ids) != len(set(backlog_ids)) or set(scheduled_ids) & set(backlog_ids):
        raise SolverBridgeError("ERROR_STEP3_SOLVER_PARTITION_INVALID")


def derive_step3_plan_fields(step2_candidate: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """Validate released evidence, run the public solver, and bind its machine fields."""
    if not validate_step2_candidate(step2_candidate)["valid"]:
        raise SolverBridgeError("ERROR_STEP3_SOURCE_STEP2_INVALID")

    projection = step2_solver_projection(step2_candidate)
    items = projection["items"]
    if not isinstance(items, list):
        raise SolverBridgeError("ERROR_STEP3_SOLVER_INPUT_INVALID")
    try:
        solver_result = solve_capacity_plan(items, hours_max=15, total_weeks=17)
    except CapacityValidationError as error:
        raise SolverBridgeError("ERROR_STEP3_SOLVER_INPUT_INVALID") from error
    weeks = [
        {"week": week["week"], "capacity_hours": week["hours"], "item_ids": [item["item_id"] for item in week["items"]]}
        for week in solver_result["weeks"]
    ]
    input_ids = [item["item_id"] for item in items]
    backlog_ids = [item["item_id"] for item in solver_result["unplaced"]]
    _require_partition(input_ids, weeks, backlog_ids)
    mandatory_ids = sorted(item["item_id"] for item in items if item["is_mandatory"])
    scheduled_weeks = {item_id: week["week"] for week in weeks for item_id in week["item_ids"]}
    if any(item_id not in scheduled_weeks or scheduled_weeks[item_id] > 8 for item_id in mandatory_ids):
        raise SolverBridgeError("ERROR_STEP3_MANDATORY_ALLOCATION_INVALID")
    vertical, horizontal = _links(items)
    machine_fields = {
        "weeks": weeks,
        "mandatory_item_ids": mandatory_ids,
        "backlog_item_ids": backlog_ids,
        "vertical_links": vertical,
        "horizontal_links": horizontal,
    }
    solver_input = _canonical(projection)
    solver_output = _canonical(machine_fields)
    return {
        "solver_version": "1.3.0",
        "solver_input": solver_input,
        "solver_output": solver_output,
        "solver_input_sha256": hashlib.sha256(solver_input.encode("utf-8")).hexdigest(),
        "solver_output_sha256": hashlib.sha256(solver_output.encode("utf-8")).hexdigest(),
        **machine_fields,
    }
