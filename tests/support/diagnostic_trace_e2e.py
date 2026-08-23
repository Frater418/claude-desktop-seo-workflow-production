from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Final, assert_never

from pydantic import TypeAdapter, ValidationError

from services.operator_api.diagnostic_trace_models import (
    DiagnosticTraceCloseRecord,
    DiagnosticTraceIndexEntry,
    DiagnosticTraceOperationRecord,
    DiagnosticTracePointer,
    DiagnosticTraceStartRecord,
)


_RECORD = TypeAdapter(DiagnosticTraceStartRecord | DiagnosticTraceOperationRecord | DiagnosticTraceCloseRecord)
_FORBIDDEN_TRACE_BYTES: Final = (
    b"/workspace/",
    b"/home/",
    b"c:\\users\\",
    b"file://",
    b"authorization",
    b"bearer ",
    b"token",
    b"header",
    b"request_body",
    b"page_text",
    b"customer",
    b"notion",
    b"n8n",
    b"agentseo",
    b"http://",
    b"https://",
)
_DELIVERY_ACTIONS: Final = (
    ("create_delivery_export", 201),
    ("download_delivery_export", 200),
    ("create_delivery_export", 200),
    ("browser_observation", 200),
)


@dataclass(frozen=True, slots=True)
class ClosedTraceEvidence:
    trace_id: str
    relative_run_path: str
    run_sha256: str
    run_bytes: bytes
    close_id: str
    closed_at: str
    last_successful_operation_id: str


def current_trace_id(root: Path) -> str:
    try:
        pointer = DiagnosticTracePointer.model_validate_json((root / "current.json").read_bytes())
    except (OSError, ValidationError) as error:
        raise AssertionError("M07 diagnostic current pointer is unreadable.") from error
    if pointer.status != "closed":
        raise AssertionError("M07 diagnostic trace must be closed before reconstruction.")
    return pointer.trace_id


def reject_active_trace(root: Path) -> None:
    current = root / "current.json"
    if not current.exists():
        return
    try:
        pointer = DiagnosticTracePointer.model_validate_json(current.read_bytes())
    except (OSError, ValidationError) as error:
        raise AssertionError("M07 diagnostic root has an unreadable current pointer.") from error
    if pointer.status == "active":
        raise AssertionError("M07 diagnostic root has an active trace and must not be mutated.")


def reconstruct_closed_trace(root: Path, trace_id: str, screenshot_reference: str) -> ClosedTraceEvidence:
    pointer_path = root / "current.json"
    index_path = root / "index.jsonl"
    try:
        pointer = DiagnosticTracePointer.model_validate_json(pointer_path.read_bytes())
        index_lines = tuple(line for line in index_path.read_bytes().splitlines() if line)
        index_entries = tuple(DiagnosticTraceIndexEntry.model_validate_json(line) for line in index_lines)
    except (OSError, ValidationError) as error:
        raise AssertionError("M07 closed diagnostic pointers are unreadable.") from error
    if pointer.status != "closed" or pointer.trace_id != trace_id:
        raise AssertionError("M07 current pointer does not identify the requested closed trace.")
    if not index_entries or any(entry.status != "closed" for entry in index_entries):
        raise AssertionError("M07 index must contain only closed traces.")
    matches = tuple(entry for entry in index_entries if entry.trace_id == trace_id)
    if len(matches) != 1:
        raise AssertionError("M07 index must contain exactly one matching closed trace.")
    index = matches[0]
    if index.relative_run_path != pointer.relative_run_path:
        raise AssertionError("M07 current pointer and index path disagree.")
    run_path = root / pointer.relative_run_path
    try:
        run_bytes = run_path.read_bytes()
        records = tuple(_RECORD.validate_json(line) for line in run_bytes.splitlines() if line)
    except (OSError, ValidationError) as error:
        raise AssertionError("M07 immutable diagnostic run is unreadable.") from error
    if not records or not isinstance(records[0], DiagnosticTraceStartRecord):
        raise AssertionError("M07 immutable diagnostic run must start with one trace_start record.")
    start = records[0].trace
    operations: list[DiagnosticTraceOperationRecord] = []
    terminals: list[DiagnosticTraceCloseRecord] = []
    for record in records[1:]:
        match record:
            case DiagnosticTraceOperationRecord():
                operations.append(record)
            case DiagnosticTraceCloseRecord():
                terminals.append(record)
            case DiagnosticTraceStartRecord():
                raise AssertionError("M07 immutable diagnostic run contains a duplicate trace_start record.")
            case unreachable:
                assert_never(unreachable)
    if len(terminals) != 1 or not isinstance(records[-1], DiagnosticTraceCloseRecord):
        raise AssertionError("M07 immutable diagnostic run must end with one terminal record.")
    terminal = terminals[0]
    if (start.trace_id, terminal.trace_id, index.trace_id) != (trace_id, trace_id, trace_id):
        raise AssertionError("M07 trace identities must match across all records.")
    if (start.tenant_id, start.project_id, start.run_id, start.source, start.scenario_id) != ("tenant-demo", "project-demo", "run-step-4b-0001", "automated", "m06-delivery"):
        raise AssertionError("M07 trace identity does not match the automated M06 delivery cell.")
    action_statuses = tuple((record.operation.action, record.operation.api_status) for record in operations)
    if action_statuses != _DELIVERY_ACTIONS:
        raise AssertionError("M07 trace does not contain the canonical Delivery create, download, replay, and browser operations.")
    observation = operations[-1].operation
    if observation.operation_id != "operation-0004-browser-observation" or observation.occurred_at != "2026-08-22T10:15:30Z":
        raise AssertionError("M07 browser observation must use canonical fixed-time identity.")
    if observation.route != "/v1/tenants/tenant-demo/projects/project-demo/delivery/exports" or observation.api_method != "POST" or observation.api_status != 200:
        raise AssertionError("M07 browser observation must describe the safe Delivery route success.")
    if observation.expected_actions != ("create_delivery_export", "download_delivery_export") or observation.rendered_actions != observation.expected_actions or observation.disabled_actions or observation.error_code is not None or observation.remediation is not None:
        raise AssertionError("M07 browser observation action projection is invalid.")
    if tuple((reference.kind, reference.relative_path) for reference in observation.evidence_references) != (("screenshot", screenshot_reference),):
        raise AssertionError("M07 browser observation must reference only the supplied relative screenshot.")
    if terminal.first_failing_operation_id is not None or index.first_failing_operation_id is not None:
        raise AssertionError("M07 closed trace must not contain a failing operation.")
    last_success = observation.operation_id
    if terminal.last_successful_operation_id != last_success or index.last_successful_operation_id != last_success:
        raise AssertionError("M07 closed trace last success does not match the browser observation.")
    trace_lower = run_bytes.lower()
    for forbidden in _FORBIDDEN_TRACE_BYTES:
        if forbidden in trace_lower:
            raise AssertionError("M07 immutable diagnostic trace contains forbidden sensitive or live-integration material.")
    return ClosedTraceEvidence(
        trace_id=trace_id,
        relative_run_path=pointer.relative_run_path,
        run_sha256=hashlib.sha256(run_bytes).hexdigest(),
        run_bytes=run_bytes,
        close_id=terminal.close_id,
        closed_at=terminal.closed_at,
        last_successful_operation_id=last_success,
    )
