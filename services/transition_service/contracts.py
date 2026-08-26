"""Transition rules, workflow loading, evaluation helpers, and result records."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

STATE_RULES = {
    "start": ({"pending"}, "in_progress"), "submit_for_gate": ({"in_progress"}, "awaiting_gate"),
    "post_publication": ({"in_progress"}, "awaiting_gate"), "approve": ({"awaiting_gate"}, "approved"),
    "complete": ({"approved"}, "completed"), "publish": ({"approved"}, "completed"),
    "retry": ({"failed"}, "in_progress"), "revise": ({"awaiting_gate"}, "in_progress"),
    "supersede": ({"pending", "in_progress", "awaiting_gate", "approved", "failed"}, "superseded"),
}
RETRY_CLASS = {"ERR_TRANSITION_NOT_ALLOWED": "manual", "ERR_STALE_REVISION": "never", "ERR_APPROVAL_STALE": "manual", "ERR_ARTIFACT_REQUIRED": "manual", "ERR_GATE_REQUIRED": "manual", "ERR_TENANT_ISOLATION": "never", "ERR_IDEMPOTENCY_CONFLICT": "never", "ERR_RETRY_EXHAUSTED": "manual"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_workflow_graph(root: Path | None = None) -> dict:
    root = root or Path(__file__).resolve().parents[2]
    return load_json(root / "standards" / "workflow" / "workflow-graph.json")


def fingerprint(command: dict) -> str:
    return hashlib.sha256(json.dumps(command, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")).hexdigest()


def error(command: dict, run: dict, index: int, code: str, message: str) -> dict:
    suffix = command.get("command_id", "command-invalid").removeprefix("command-")
    return {"error_id": f"error-{suffix}-{index}", "tenant_id": run.get("tenant_id", command.get("tenant_id", "tenant-invalid")), "run_id": run.get("run_id", command.get("run_id", "run-invalid-0000")), "step_id": run.get("step_id", command.get("to_step_id", "0")), "code": code, "message": message, "retry_class": RETRY_CLASS[code], "occurred_at": command.get("requested_at", "1970-01-01T00:00:00Z")}


def predecessor_ok(command: dict, graph: dict, run: dict, predecessor: dict | None) -> bool:
    step_id = run["step_id"]
    if step_id == "0":
        return command["from_step_id"] == "0" and command["to_step_id"] == "0"
    edge_ok = True if step_id == "3b" and command["from_step_id"] == "4b" and command["to_step_id"] == "3b" else any(edge["from_step_id"] == command["from_step_id"] and edge["to_step_id"] == command["to_step_id"] == step_id for edge in graph["initial_edges"])
    return bool(edge_ok and predecessor and predecessor.get("step_id") == command["from_step_id"] and predecessor.get("status") == "released" and predecessor.get("artifact_id") and predecessor.get("artifact_sha256"))


def approval_errors(approval: dict | None, run: dict, artifact: dict, requested_at: str) -> list[str]:
    if not isinstance(approval, dict):
        return ["A current external approval record is required."]
    expected = {"tenant_id": run["tenant_id"], "run_id": run["run_id"], "gate_id": run["gate_id"], "artifact_id": artifact["artifact_id"], "artifact_sha256": artifact["content_sha256"], "artifact_revision": artifact["revision"], "decision": "approved"}
    errors = [f"Approval field '{key}' is stale or mismatched." for key, value in expected.items() if approval.get(key) != value]
    try:
        parse_time = lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not (parse_time(approval["decided_at"]) <= parse_time(requested_at) < parse_time(approval["expires_at"])):
            errors.append("Approval is not current at the requested transition time.")
    except (KeyError, TypeError, ValueError):
        errors.append("Approval timestamps are missing or invalid.")
    return errors


def human_quality_gate_run(command: dict, run: dict, artifact: dict, approval: dict, gate: dict, registry_version: str) -> dict:
    suffix = command["command_id"].removeprefix("command-")
    return {"quality_gate_run_id": f"qgr-{suffix}", "quality_gate_id": gate["gate_id"], "human_gate_id": run["gate_id"], "tenant_id": run["tenant_id"], "run_id": run["run_id"], "step_id": run["step_id"], "artifact_id": artifact["artifact_id"], "artifact_sha256": artifact["content_sha256"], "artifact_revision": artifact["revision"], "registry_version": registry_version, "policy_version": approval["policy_version"], "result": "passed", "evidence": {"artifact_id": artifact["artifact_id"], "artifact_sha256": artifact["content_sha256"], "approval_id": approval["approval_id"], "reviewer_id": approval["reviewer_id"], "decided_at": approval["decided_at"]}, "findings": [{"code": "QG_HUMAN_APPROVAL_VALID", "severity": "info", "message": "External revision-bound approval validated."}], "checked_at": command["requested_at"], "checker_version": "heartweb-transition-service-1.0.0"}


def release_record(command: dict, run: dict, artifact: dict, approval: dict) -> dict:
    suffix = command["command_id"].removeprefix("command-")
    return {"release_id": f"release-{suffix}", "tenant_id": run["tenant_id"], "project_id": run["project_id"], "run_id": run["run_id"], "step_id": run["step_id"], "gate_id": run["gate_id"], "artifact_id": artifact["artifact_id"], "artifact_sha256": artifact["content_sha256"], "artifact_revision": artifact["revision"], "approval_id": approval["approval_id"], "policy_version": approval["policy_version"], "status": "released", "released_at": command["requested_at"]}
