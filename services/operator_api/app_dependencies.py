"""Validated dependencies loaded by the Operator API composition root."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from services.operator_routing import load_policy, validate_policy
from services.quality_gate_registry import load_registry
from services.transition_service.service import load_workflow_graph

from .event_store import EventStore
from .models import JsonValue
from .repository import WorkspaceRegistry


def load_dependencies(root: Path, registry: WorkspaceRegistry) -> dict[str, JsonValue]:
    """Load and validate the schema, workflow, policy, and event dependencies."""
    schemas: dict[str, JsonValue] = {}
    for folder in ("runtime", "operator", "integrations", "workflow"):
        for path in (root / "standards" / folder).glob("*.schema.json"):
            schema = _json(path)
            Draft202012Validator.check_schema(schema)
            schemas[path.stem] = schema
    graph = load_workflow_graph(root)
    graph_schema = _json(root / "standards/workflow/workflow-graph.schema.json")
    Draft202012Validator(graph_schema, format_checker=FormatChecker()).validate(graph)
    policy = load_policy(root)
    if not validate_policy(policy).valid:
        raise ValueError("routing policy is incomplete")
    catalog = _json(root / "standards/integrations/event-catalog-v2.json")
    event_schema = _json(root / "standards/integrations/workflow-event-v2.schema.json")
    if set(catalog["events"]) != set(event_schema["properties"]["event_type"]["enum"]):
        raise ValueError("event catalog is incomplete")
    for registration in registry._registrations:
        EventStore(registration.workspace, event_schema).validate_history()
    return {"policy": policy, "graph": graph, "gate_registry": load_registry(root), "event_schema": event_schema, "record_schemas": schemas}


def _json(path: Path) -> dict[str, JsonValue]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("schema is not an object")
    return value
