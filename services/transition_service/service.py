"""Central fail-fast workflow transition service.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from services.quality_gate_registry import evaluate_gate_runs, load_registry


STATE_RULES = {
    "start": ({"pending"}, "in_progress"),
    "submit_for_gate": ({"in_progress"}, "awaiting_gate"),
    "post_publication": ({"in_progress"}, "awaiting_gate"),
    "approve": ({"awaiting_gate"}, "approved"),
    "complete": ({"approved"}, "completed"),
    "publish": ({"approved"}, "completed"),
    "retry": ({"failed"}, "in_progress"),
    "supersede": ({"pending", "in_progress", "awaiting_gate", "approved", "failed"}, "superseded"),
}

RETRY_CLASS = {
    "ERR_TRANSITION_NOT_ALLOWED": "manual",
    "ERR_STALE_REVISION": "never",
    "ERR_APPROVAL_STALE": "manual",
    "ERR_ARTIFACT_REQUIRED": "manual",
    "ERR_GATE_REQUIRED": "manual",
    "ERR_TENANT_ISOLATION": "never",
    "ERR_IDEMPOTENCY_CONFLICT": "never",
    "ERR_RETRY_EXHAUSTED": "manual",
}


class LedgerLockContentionError(RuntimeError):
    """Raised when another local transition process owns the ledger lock."""

    def __init__(self, ledger_path: Path) -> None:
        self.ledger_path = ledger_path
        super().__init__(f"ERROR_TRANSITION_LEDGER_LOCKED: Durable ledger lock is active: {ledger_path}")


@contextmanager
def durable_ledger_lock(ledger_path: Path) -> Iterator[None]:
    """Acquire the durable-local ledger lock or fail immediately on contention."""
    lock_path = ledger_path.with_suffix(ledger_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_path.touch(exist_ok=False)
    except FileExistsError as exc:
        raise LedgerLockContentionError(ledger_path) from exc
    try:
        yield
    finally:
        lock_path.unlink()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_workflow_graph(root: Path | None = None) -> dict:
    root = root or Path(__file__).resolve().parents[2]
    return _load_json(root / "standards" / "workflow" / "workflow-graph.json")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _fingerprint(command: dict) -> str:
    source = json.dumps(command, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")
    return hashlib.sha256(source).hexdigest()


def _error(command: dict, run: dict, index: int, code: str, message: str) -> dict:
    suffix = command.get("command_id", "command-invalid").removeprefix("command-")
    return {
        "error_id": f"error-{suffix}-{index}",
        "tenant_id": run.get("tenant_id", command.get("tenant_id", "tenant-invalid")),
        "run_id": run.get("run_id", command.get("run_id", "run-invalid-0000")),
        "step_id": run.get("step_id", command.get("to_step_id", "0")),
        "code": code,
        "message": message,
        "retry_class": RETRY_CLASS[code],
        "occurred_at": command.get("requested_at", "1970-01-01T00:00:00Z"),
    }


def _predecessor_ok(command: dict, graph: dict, run: dict, predecessor: dict | None) -> bool:
    step_id = run["step_id"]
    if step_id == "0":
        return command["from_step_id"] == "0" and command["to_step_id"] == "0"
    if step_id == "3b" and command["from_step_id"] == "4b" and command["to_step_id"] == "3b":
        edge_ok = True
    else:
        edge_ok = any(
            edge["from_step_id"] == command["from_step_id"]
            and edge["to_step_id"] == command["to_step_id"] == step_id
            for edge in graph["initial_edges"]
        )
    return bool(
        edge_ok
        and predecessor
        and predecessor.get("step_id") == command["from_step_id"]
        and predecessor.get("status") == "released"
        and predecessor.get("artifact_id")
        and predecessor.get("artifact_sha256")
    )


def _approval_errors(approval: dict | None, run: dict, artifact: dict, requested_at: str) -> list[str]:
    if not isinstance(approval, dict):
        return ["A current external approval record is required."]
    expected = {
        "tenant_id": run["tenant_id"],
        "run_id": run["run_id"],
        "gate_id": run["gate_id"],
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": artifact["content_sha256"],
        "artifact_revision": artifact["revision"],
        "decision": "approved",
    }
    errors = [f"Approval field '{key}' is stale or mismatched." for key, value in expected.items() if approval.get(key) != value]
    try:
        if not (_parse_time(approval["decided_at"]) <= _parse_time(requested_at) < _parse_time(approval["expires_at"])):
            errors.append("Approval is not current at the requested transition time.")
    except (KeyError, TypeError, ValueError):
        errors.append("Approval timestamps are missing or invalid.")
    return errors


def _human_qgr(command: dict, run: dict, artifact: dict, approval: dict, gate: dict) -> dict:
    suffix = command["command_id"].removeprefix("command-")
    return {
        "quality_gate_run_id": f"qgr-{suffix}",
        "quality_gate_id": gate["gate_id"],
        "human_gate_id": run["gate_id"],
        "tenant_id": run["tenant_id"],
        "run_id": run["run_id"],
        "step_id": run["step_id"],
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": artifact["content_sha256"],
        "policy_version": approval["policy_version"],
        "result": "passed",
        "findings": [{"code": "QG_HUMAN_APPROVAL_VALID", "severity": "info", "message": "External revision-bound approval validated."}],
        "checked_at": command["requested_at"],
        "checker_version": "heartweb-transition-service-1.0.0",
    }


def _release(command: dict, run: dict, artifact: dict, approval: dict) -> dict:
    suffix = command["command_id"].removeprefix("command-")
    return {
        "release_id": f"release-{suffix}",
        "tenant_id": run["tenant_id"],
        "project_id": run["project_id"],
        "run_id": run["run_id"],
        "step_id": run["step_id"],
        "gate_id": run["gate_id"],
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": artifact["content_sha256"],
        "artifact_revision": artifact["revision"],
        "approval_id": approval["approval_id"],
        "policy_version": approval["policy_version"],
        "status": "released",
        "released_at": command["requested_at"],
    }


def process_transition(
    command: dict,
    run: dict,
    current_artifact: dict | None,
    supporting_artifacts: list[dict] | None = None,
    quality_gate_runs: list[dict] | None = None,
    approval: dict | None = None,
    predecessor_release: dict | None = None,
    context: dict | None = None,
    idempotency_ledger: dict[str, str] | None = None,
    max_attempts: int = 3,
    registry: dict | None = None,
    graph: dict | None = None,
) -> dict:
    """Evaluate one transition without partial state mutation."""
    supporting_artifacts = supporting_artifacts or []
    quality_gate_runs = quality_gate_runs or []
    context = context or {}
    idempotency_ledger = idempotency_ledger or {}
    registry = registry or load_registry()
    graph = graph or load_workflow_graph()
    errors: list[tuple[str, str]] = []
    fingerprint = _fingerprint(command)

    previous_fingerprint = idempotency_ledger.get(command.get("idempotency_key"))
    if previous_fingerprint and previous_fingerprint != fingerprint:
        errors.append(("ERR_IDEMPOTENCY_CONFLICT", "Idempotency key was already used for a different command."))
    elif previous_fingerprint == fingerprint:
        return {
            "ok": True,
            "replay": True,
            "command_fingerprint": fingerprint,
            "run": copy.deepcopy(run),
            "human_quality_gate_run": None,
            "release_record": None,
            "errors": [],
        }

    identity = {
        "tenant_id": run.get("tenant_id"),
        "project_id": run.get("project_id"),
        "run_id": run.get("run_id"),
    }
    if any(command.get(key) != value for key, value in identity.items()):
        errors.append(("ERR_TENANT_ISOLATION", "Command tenant, project or run identity does not match the current run."))
    if command.get("expected_revision") != run.get("revision"):
        errors.append(("ERR_STALE_REVISION", "Command expected revision does not match the current run revision."))
    if command.get("input_hash") != run.get("input_hash"):
        errors.append(("ERR_STALE_REVISION", "Command input hash does not match the current run input hash."))
    operation = command.get("operation")
    if operation not in STATE_RULES:
        errors.append(("ERR_TRANSITION_NOT_ALLOWED", f"Unsupported operation: {operation}."))
    else:
        allowed_states, _ = STATE_RULES[operation]
        if run.get("status") not in allowed_states:
            errors.append(("ERR_TRANSITION_NOT_ALLOWED", f"Operation {operation} is not allowed from status {run.get('status')}."))

    if command.get("to_step_id") != run.get("step_id"):
        errors.append(("ERR_TRANSITION_NOT_ALLOWED", "Command target step does not match the current run step."))
    if operation in {"approve", "complete", "publish", "retry", "supersede"} and command.get("from_step_id") != run.get("step_id"):
        errors.append(("ERR_TRANSITION_NOT_ALLOWED", "Same-step operation must use the current step as source and target."))
    if operation in {"start", "submit_for_gate", "post_publication"} and not _predecessor_ok(command, graph, run, predecessor_release):
        errors.append(("ERR_TRANSITION_NOT_ALLOWED", "A matching released predecessor and workflow edge are required."))

    artifact_required = operation in {"submit_for_gate", "post_publication", "approve", "complete", "publish"}
    if artifact_required and not isinstance(current_artifact, dict):
        errors.append(("ERR_ARTIFACT_REQUIRED", "Current artifact is required for this transition."))
    elif isinstance(current_artifact, dict):
        expected_artifact = {
            "tenant_id": run.get("tenant_id"),
            "project_id": run.get("project_id"),
            "run_id": run.get("run_id"),
            "step_id": run.get("step_id"),
        }
        if any(current_artifact.get(key) != value for key, value in expected_artifact.items()):
            errors.append(("ERR_ARTIFACT_REQUIRED", "Current artifact identity does not match the run."))
        if command.get("output_hash") and command.get("output_hash") != current_artifact.get("content_sha256"):
            errors.append(("ERR_ARTIFACT_REQUIRED", "Command output hash does not match the current artifact."))

    if operation == "retry" and int(run.get("attempt", 1)) >= max_attempts:
        errors.append(("ERR_RETRY_EXHAUSTED", "Retry attempt limit is exhausted."))

    gate_result = None
    if not errors and artifact_required:
        gate_operation = "submit_for_gate" if operation in {"submit_for_gate", "approve", "complete"} else operation
        gate_result = evaluate_gate_runs(
            registry,
            run["step_id"],
            gate_operation,
            context,
            run["tenant_id"],
            run["run_id"],
            run["gate_id"],
            current_artifact,
            supporting_artifacts,
            quality_gate_runs,
        )
        for gate_error in gate_result["errors"]:
            errors.append(("ERR_GATE_REQUIRED", f"{gate_error['gate_id']}: {gate_error['message']}"))

    human_gate_defs: list[dict] = []
    if not errors and operation in {"approve", "complete", "publish"}:
        human_result = evaluate_gate_runs(
            registry,
            run["step_id"],
            "approve" if operation != "publish" else "publish",
            context,
            run["tenant_id"],
            run["run_id"],
            run["gate_id"],
            current_artifact,
            supporting_artifacts,
            quality_gate_runs,
        )
        human_gate_defs = human_result["human_gate_definitions"]
        for gate_error in human_result["errors"]:
            errors.append(("ERR_GATE_REQUIRED", f"{gate_error['gate_id']}: {gate_error['message']}"))
        for approval_error in _approval_errors(approval, run, current_artifact, command["requested_at"]):
            errors.append(("ERR_APPROVAL_STALE", approval_error))
        if len(human_gate_defs) != 1:
            errors.append(("ERR_GATE_REQUIRED", "Exactly one applicable human gate definition is required."))

    if not errors and operation in {"complete", "publish"}:
        human_gate_id = human_gate_defs[0]["gate_id"]
        current_human_run = any(
            record.get("quality_gate_id") == human_gate_id
            and record.get("tenant_id") == run["tenant_id"]
            and record.get("run_id") == run["run_id"]
            and record.get("artifact_id") == current_artifact["artifact_id"]
            and record.get("artifact_sha256") == current_artifact["content_sha256"]
            and record.get("result") == "passed"
            for record in quality_gate_runs
        )
        if not current_human_run:
            errors.append(("ERR_GATE_REQUIRED", "A current passed human quality-gate run is required before completion."))

    if errors:
        envelopes = [_error(command, run, index + 1, code, message) for index, (code, message) in enumerate(errors)]
        return {
            "ok": False,
            "replay": False,
            "command_fingerprint": fingerprint,
            "run": copy.deepcopy(run),
            "human_quality_gate_run": None,
            "release_record": None,
            "errors": envelopes,
        }

    _, target_status = STATE_RULES[operation]
    next_run = copy.deepcopy(run)
    next_run["status"] = target_status
    if operation in {"submit_for_gate", "post_publication", "approve", "complete", "publish"}:
        next_run["output_hash"] = current_artifact["content_sha256"]
    if operation == "retry":
        next_run["attempt"] = int(run["attempt"]) + 1
    human_qgr = _human_qgr(command, run, current_artifact, approval, human_gate_defs[0]) if operation == "approve" else None
    release_record = _release(command, run, current_artifact, approval) if operation in {"complete", "publish"} else None
    return {
        "ok": True,
        "replay": False,
        "command_fingerprint": fingerprint,
        "run": next_run,
        "human_quality_gate_run": human_qgr,
        "release_record": release_record,
        "errors": [],
    }


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _load_ledger(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = _load_json(path)
    fingerprints = payload.get("fingerprints")
    if not isinstance(fingerprints, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in fingerprints.items()):
        raise RuntimeError("Transition ledger has an invalid durable-local format.")
    return fingerprints


def main() -> int:
    parser = argparse.ArgumentParser(description="Heartweb central transition service")
    parser.add_argument("--request", required=True, help="JSON request containing command, run, artifacts, gates and context")
    parser.add_argument("--output", required=True, help="Atomic transition-result output path")
    parser.add_argument("--ledger", required=True, help="Durable local idempotency ledger path")
    args = parser.parse_args()
    request = _load_json(Path(args.request))
    ledger_path = Path(args.ledger)
    try:
        with durable_ledger_lock(ledger_path):
            ledger = _load_ledger(ledger_path)
            result = process_transition(
                command=request["command"],
                run=request["run"],
                current_artifact=request.get("current_artifact"),
                supporting_artifacts=request.get("supporting_artifacts"),
                quality_gate_runs=request.get("quality_gate_runs"),
                approval=request.get("approval"),
                predecessor_release=request.get("predecessor_release"),
                context=request.get("context"),
                idempotency_ledger=ledger,
                max_attempts=int(request.get("max_attempts", 3)),
            )
            if result["ok"] and not result["replay"]:
                ledger[request["command"]["idempotency_key"]] = result["command_fingerprint"]
                _atomic_write(ledger_path, {"fingerprints": ledger})
            _atomic_write(Path(args.output), result)
    except LedgerLockContentionError as exc:
        print(exc, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
