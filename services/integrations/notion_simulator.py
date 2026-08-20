from __future__ import annotations

import copy
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from services.integration_contracts.notion_graph import NotionGraphTarget, assert_notion_graph_valid


@dataclass(frozen=True, slots=True)
class NotionSimulationError(ValueError):
    code: str
    path: str
    message: str
    remediation: str

    def __str__(self) -> str:
        return f"{self.code}:{self.path}: {self.message} Remediation: {self.remediation}"


@dataclass(frozen=True, slots=True)
class NotionContracts:
    event_schema: Mapping[str, Any]
    event_catalog: Mapping[str, Any]
    proposal_schema: Mapping[str, Any]
    graph_schemas: Mapping[str, Mapping[str, Any]]


def materialize_events(events: Sequence[Mapping[str, Any]], contracts: NotionContracts) -> dict[str, Any]:
    _check_schema(contracts.event_schema, "event schema")
    _check_schema(contracts.proposal_schema, "proposal schema")
    for schema_name, schema in contracts.graph_schemas.items():
        _check_schema(schema, f"{schema_name} schema")
    event_types = tuple(contracts.event_schema["properties"]["event_type"]["enum"])
    if tuple(contracts.event_catalog.get("events", ())) != event_types:
        raise _error("NOTION_SIMULATION_CATALOG_MISMATCH", "/event_catalog/events", "event catalog must exactly match the V2 event schema", "Inject the approved V2 catalog and schema pair.")
    deduplicated: dict[str, Mapping[str, Any]] = {}
    event_validator = Draft202012Validator(contracts.event_schema, format_checker=FormatChecker())
    for index, source in enumerate(events):
        document = copy.deepcopy(dict(source))
        errors = sorted(event_validator.iter_errors(document), key=lambda item: (list(item.absolute_path), item.message))
        if errors or document.get("integration_mode") != "simulated" or "live_connection_id" in document:
            message = errors[0].message if errors else "only simulated events without live identifiers are accepted"
            raise _error("NOTION_SIMULATION_EVENT_INVALID", f"/events/{index}", message, "Submit a schema-valid simulated V2 event.")
        event_id = document["event_id"]
        previous = deduplicated.get(event_id)
        if previous is not None and _canonical(previous) != _canonical(document):
            raise _error("NOTION_SIMULATION_EVENT_CONFLICT", f"/events/{index}/event_id", "event ID has different content", "Use a new event ID for a changed immutable event.")
        deduplicated[event_id] = document
    ordered = sorted(deduplicated.values(), key=lambda item: (_instant(item["occurred_at"]), item["event_id"]))
    if not ordered:
        raise _error("NOTION_SIMULATION_EVENT_INVALID", "/events", "at least one event is required", "Supply the accepted event stream for one simulation.")
    identity = ordered[0]["identity"]
    simulation_id = ordered[0]["simulation_id"]
    for index, item in enumerate(ordered):
        if item["simulation_id"] != simulation_id or any(item["identity"][key] != identity[key] for key in ("tenant_id", "project_id")):
            raise _error("NOTION_SIMULATION_IDENTITY_CONFLICT", f"/events/{index}/identity", "events must belong to one tenant, project and simulation", "Split the projection stream by tenant, project and simulation.")
    records: dict[str, dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []
    highest_revision = 0
    for item in ordered:
        revision = item["identity"]["revision"]
        highest_revision = max(highest_revision, revision)
        _project_event(records, conflicts, item)
    latest = ordered[-1]
    snapshot = {
        "snapshot_id": f"notion-snapshot-{simulation_id.removeprefix('sim-')}", "schema_version": "2.0.0",
        "integration_mode": "simulated", "simulation_id": simulation_id, "materialized_at": latest["occurred_at"],
        "projection_revision": highest_revision, "source_event_watermark": latest["event_id"], "state_authority": "transition_service",
        "atomic_state_writer": False, "records": records, "conflicts": conflicts,
    }
    try:
        assert_notion_graph_valid(snapshot, NotionGraphTarget.SNAPSHOT, contracts.graph_schemas)
    except ValueError as exc:
        raise _error("NOTION_SIMULATION_PROJECTION_INVALID", "/records", str(exc), "Correct the event projection mapping before materialization.") from exc
    return snapshot


def materialize_projection(events: Sequence[Mapping[str, Any]], contracts: NotionContracts) -> dict[str, Any]:
    snapshot = materialize_events(events, contracts)
    latest = max(events, key=lambda item: (_instant(item["occurred_at"]), item["event_id"]))
    projection = {
        "projection_id": f"notion-projection-{snapshot['simulation_id'].removeprefix('sim-')}", "schema_version": "2.0.0",
        "integration_mode": "simulated", "simulation_id": snapshot["simulation_id"], "projected_at": snapshot["materialized_at"],
        "source_event_id": snapshot["source_event_watermark"], "source_revision": snapshot["projection_revision"], "identity": latest["identity"],
        "projection_role": "operative_projection", "state_authority": "transition_service", "atomic_state_writer": False, "records": snapshot["records"],
    }
    try:
        assert_notion_graph_valid(projection, NotionGraphTarget.PROJECTION, contracts.graph_schemas)
    except ValueError as exc:
        raise _error("NOTION_SIMULATION_PROJECTION_INVALID", "/records", str(exc), "Correct the event projection mapping before materialization.") from exc
    return projection


def translate_proposal(proposal: Mapping[str, Any], current_revision: int, proposal_schema: Mapping[str, Any]) -> dict[str, Any]:
    _check_schema(proposal_schema, "proposal schema")
    document = copy.deepcopy(dict(proposal))
    errors = sorted(Draft202012Validator(proposal_schema, format_checker=FormatChecker()).iter_errors(document), key=lambda item: (list(item.absolute_path), item.message))
    if errors:
        raise _error("NOTION_SIMULATION_PROPOSAL_INVALID", _path(errors[0].absolute_path), errors[0].message, "Submit a schema-valid simulated human proposal.")
    if document["expected_revision"] != current_revision:
        raise _error("NOTION_SIMULATION_STALE_PROPOSAL", "/expected_revision", "proposal revision does not match the current Core revision", "Refresh the Notion view and submit a new proposal.")
    return {
        "request_kind": "core_command_request", "command_id": f"core-{document['proposal_id'].removeprefix('notion-proposal-')}",
        "operation": document["intent"], "expected_revision": current_revision, "actor": document["actor"], "correlation_id": document["correlation_id"],
        "idempotency_key": document["idempotency_key"], "target": document["target"], "source_proposal_id": document["proposal_id"],
    }


def _project_event(records: dict[str, dict[str, Any]], conflicts: list[dict[str, Any]], event: Mapping[str, Any]) -> None:
    identity = event["identity"]
    project_id = identity["project_id"]
    customer_id = event["payload"].get("customer_id", f"customer-{project_id.removeprefix('project-')}")
    step_id = f"step-{identity['step_id']}-{project_id.removeprefix('project-')}"
    _put(records, conflicts, customer_id, "customer", "customer", [(_relation("project", project_id))], event)
    _put(records, conflicts, project_id, "project", "project", [(_relation("customer", customer_id))], event)
    _put(records, conflicts, step_id, "step", identity["step_id"], [(_relation("project", project_id))], event)
    _put(records, conflicts, identity["run_id"], "run", "active", [_relation("project", project_id), _relation("step", step_id)], event)
    event_type = event["event_type"]
    payload = event["payload"]
    base = [_relation("project", project_id), _relation("run", identity["run_id"]), _relation("step", step_id)]
    if event_type == "artifact.created":
        _put(records, conflicts, payload["artifact_id"], "artifact", "created", base, event)
    elif event_type in {"gate.ready", "gate.approved", "gate.rejected", "approval.recorded"}:
        gate_id = _gate_id(payload.get("gate_id", "gate"))
        _put(records, conflicts, gate_id, "gate", event_type.rsplit(".", 1)[-1], base, event)
        if event_type == "gate.ready":
            _put(records, conflicts, f"review-{event['event_id'].removeprefix('event-')}", "review", "requested", [*base, _relation("gate", gate_id)], event)
        if event_type == "approval.recorded":
            _put(records, conflicts, payload["approval_id"], "approval", payload["decision"], [*base, _relation("gate", gate_id)], event)
    elif event_type in {"task.created", "task.resolved", "assignment.created"}:
        task_id = payload.get("task_id", f"task-{event['event_id'].removeprefix('event-')}")
        if event_type == "assignment.created" and task_id not in records:
            _put(records, conflicts, task_id, "task", "unassigned", base, event)
        elif event_type != "assignment.created":
            status = "unassigned" if event_type == "task.created" else "resolved"
            _put(records, conflicts, task_id, "task", status, base, event)
        if event_type == "assignment.created":
            _put(records, conflicts, payload["assignment_id"], "assignment", payload["assigned_role"], [*base, _relation("task", task_id)], event)
    elif event_type == "step.blocked":
        _put(records, conflicts, payload["blocker_id"], "blocker", "blocked", base, event)
    elif event_type == "blocker.resolved":
        _put(records, conflicts, payload["blocker_id"], "blocker", "resolved", base, event)
    elif event_type == "defect.created":
        _put(records, conflicts, payload["defect_id"], "defect", payload["severity"], base, event)
    elif event_type == "escalation.created":
        _put(records, conflicts, payload["escalation_id"], "escalation", payload["decision_owner"], base, event)
    elif event_type == "performance.checkpoint_due":
        record_id = f"performance-checkpoint-{payload['checkpoint_id'].removeprefix('checkpoint-')}"
        _put(records, conflicts, record_id, "performance_checkpoint", str(payload["day_after_publication"]), base, event)
    elif event_type == "metric.recorded":
        _put(records, conflicts, payload["metric_id"], "metric", payload["unit"], base, event)
    elif event_type == "adjustment.proposed":
        _put(records, conflicts, payload["source_artifact_id"], "artifact", "referenced", base, event)
        checkpoint = f"performance-checkpoint-{payload['checkpoint_id'].removeprefix('checkpoint-')}"
        _put(records, conflicts, checkpoint, "performance_checkpoint", "referenced", base, event)
        record_id = f"adjustment-proposal-{payload['proposal_id'].removeprefix('adjustment-')}"
        _put(records, conflicts, record_id, "adjustment_proposal", "proposed", [*base, _relation("artifact", payload["source_artifact_id"]), _relation("performance_checkpoint", checkpoint)], event)
    elif event_type == "integration.delivery_failed":
        record_id = f"integration-status-{payload['delivery_id'].removeprefix('delivery-')}"
        _put(records, conflicts, record_id, "integration_status", payload["failure_code"], base, event)
    elif event_type == "integration.conflict_detected":
        record_id = f"integration-status-{payload['conflict_id'].removeprefix('conflict-')}"
        _put(records, conflicts, record_id, "integration_status", "conflict_detected", base, event)
        conflicts.append({"conflict_id": payload["conflict_id"], "record_id": record_id, "expected_revision": event["identity"]["revision"], "observed_revision": payload["conflicting_revision"]})


def _put(records: dict[str, dict[str, Any]], conflicts: list[dict[str, Any]], record_id: str, record_type: str, status: str, relations: list[dict[str, str]], event: Mapping[str, Any]) -> None:
    previous = records.get(record_id)
    if previous is not None:
        previous_revision = previous["source_revision"]
        revision = event["identity"]["revision"]
        conflicts.append({"conflict_id": f"conflict-{event['event_id'].removeprefix('event-')}-{record_id.removeprefix(record_type + '-')}", "record_id": record_id, "expected_revision": previous_revision, "observed_revision": revision})
        if revision < previous_revision:
            return
    records[record_id] = {"record_type": record_type, "subject_id": record_id, "title": record_id, "projected_status": status, "source_event_id": event["event_id"], "source_revision": event["identity"]["revision"], "relations": relations}


def _relation(relation_type: str, target_record_id: str) -> dict[str, str]:
    return {"relation_type": relation_type, "target_record_id": target_record_id}


def _gate_id(gate_id: str) -> str:
    return f"gate-{gate_id.lower().replace('_', '-')}"


def _check_schema(schema: Mapping[str, Any], name: str) -> None:
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise _error("NOTION_SIMULATION_SCHEMA_INVALID", "/", f"injected {name} is not a valid Draft 2020-12 schema", "Inject the approved schema without modification.") from exc


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _path(parts: Sequence[Any]) -> str:
    return "/" + "/".join(str(part) for part in parts)


def _error(code: str, path: str, message: str, remediation: str) -> NotionSimulationError:
    return NotionSimulationError(code, path, message, remediation)
