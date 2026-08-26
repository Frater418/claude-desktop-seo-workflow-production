from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from pydantic import JsonValue


ROOT = Path(__file__).resolve().parents[2]
TENANT = "tenant-demo"
PROJECT = "project-demo"
CREATED_AT = "2026-08-22T10:15:30Z"
DELIVERABLES = (
    ("1", "strategy", "strategy/topic-inventory.md"),
    ("1b", "architecture", "architecture/page-map.md"),
    ("1c", "design", "design/design-system.md"),
    ("2", "keyword-research", "keyword-research/evidence.md"),
    ("3", "roadmap", "roadmap/plan.md"),
    ("4a", "copywriter-handoff", "copywriter-handoff/briefing.md"),
    ("4b", "developer-handoff", "developer-handoff/page-spec.md"),
)


def delivery_base() -> str:
    return f"/v1/tenants/{TENANT}/projects/{PROJECT}/delivery"


def write_projection(workspace: Path, relative: str, value: JsonValue) -> None:
    path = workspace / "v2" / "operator" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")


def workspace_snapshot(workspace: Path, *, include_delivery: bool = False) -> dict[str, bytes]:
    root = workspace / "v2" / "operator"
    return {
        path.relative_to(workspace).as_posix(): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file() and (include_delivery or not path.is_relative_to(root / "delivery"))
    }


def seed_workspace(workspace: Path, *, incomplete_final: bool = False) -> None:
    project_v2 = json.loads(
        (ROOT / "tests" / "fixtures" / "domain" / "real-customer-matrix" / "national-b2b.json").read_text(
            encoding="utf-8"
        )
    )
    project_v2["project_id"] = PROJECT
    project_v2["tenant"]["tenant_id"] = TENANT
    identity = {"tenant_id": TENANT, "project_id": PROJECT}
    write_projection(workspace, "project.json", {**identity, "name": "Neutral Delivery Project"})
    write_projection(workspace, "project-v2.json", project_v2)
    write_projection(workspace, "logical-session.json", {**identity, "logical_session_id": "session-delivery-0001"})
    write_projection(
        workspace,
        "workflow.json",
        {
            **identity,
            "initial_edges": [
                {"from_step_id": source, "to_step_id": target}
                for source, target in zip(("0", "1", "1b", "1c", "2", "3", "4a"), ("1", "1b", "1c", "2", "3", "4a", "4b"), strict=True)
            ],
            "sideflows": [{"step_id": "3b", "status": "not_due"}],
        },
    )
    write_projection(workspace, "steps.json", [{"step_id": step_id, "status": "completed"} for step_id in ("0", "1", "1b", "1c", "2", "3", "4a", "4b")])

    for step_id in ("0", "1", "1b", "1c", "2", "3", "4a", "4b"):
        write_projection(
            workspace,
            f"runs/run-step-{step_id}-0001.json",
            {
                **identity,
                "run_id": f"run-step-{step_id}-0001",
                "step_id": step_id,
                "gate_id": f"GATE-{step_id.upper()}",
                "revision": 1,
                "input_hash": hashlib.sha256(f"input-{step_id}".encode("ascii")).hexdigest(),
                "idempotency_key": f"idem-run-{step_id}-0001",
                "status": "completed",
                "attempt": 1,
                "created_at": CREATED_AT,
                "gate_context": {"local_workflow": True},
            },
        )

    artifacts: list[dict[str, JsonValue]] = []
    releases: list[dict[str, JsonValue]] = []
    gates: list[dict[str, JsonValue]] = []
    approvals: list[dict[str, JsonValue]] = []
    for index, (step_id, deliverable_id, _) in enumerate(DELIVERABLES, start=1):
        artifact_id = f"artifact-{deliverable_id}-0001"
        content = f"released {deliverable_id} artifact\n".encode("utf-8")
        content_sha256 = hashlib.sha256(content).hexdigest()
        (workspace / "v2" / "operator" / "artifact-content").mkdir(parents=True, exist_ok=True)
        (workspace / "v2" / "operator" / "artifact-content" / f"{artifact_id}.md").write_bytes(content)
        artifact = {
            **identity,
            "artifact_id": artifact_id,
            "run_id": f"run-step-{step_id}-0001",
            "step_id": step_id,
            "revision": 1,
            "input_hash": hashlib.sha256(f"input-{step_id}".encode("ascii")).hexdigest(),
            "content_sha256": content_sha256,
            "contract_version": "1.0.0",
            "producer_version": "delivery-api-test",
            "storage_key": f"tenants/{TENANT}/projects/{PROJECT}/runs/run-step-{step_id}-0001/artifacts/{artifact_id}/content.md",
            "created_at": CREATED_AT,
        }
        approval_id = f"approval-delivery-{index:04d}"
        release = {
            **identity,
            "release_id": f"release-artifact-{deliverable_id}-0001",
            "artifact_id": artifact_id,
            "artifact_sha256": content_sha256,
            "artifact_revision": 1,
            "run_id": f"run-step-{step_id}-0001",
            "step_id": step_id,
            "gate_id": f"GATE-{step_id.upper()}",
            "approval_id": approval_id,
            "policy_version": "1.0.0",
            "status": "released",
            "released_at": CREATED_AT,
        }
        artifacts.append(artifact)
        if not (incomplete_final and deliverable_id == "developer-handoff"):
            releases.append(release)
            write_projection(workspace, f"releases/{release['release_id']}.json", release)
        approvals.append({**identity, "approval_id": approval_id, "artifact_id": artifact_id, "status": "approved", "approved_at": CREATED_AT})
        gates.append(
            {
                "quality_gate_run_id": f"qgr-delivery-{index:04d}",
                "quality_gate_id": f"qg-{step_id}",
                "human_gate_id": f"GATE-{step_id.upper()}",
                "tenant_id": TENANT,
                "run_id": f"run-step-{step_id}-0001",
                "step_id": step_id,
                "artifact_id": artifact_id,
                "artifact_sha256": content_sha256,
                "artifact_revision": 1,
                "registry_version": "1.0.0",
                "policy_version": "1.0.0",
                "result": "passed",
                "evidence": {"check": "passed"},
                "checked_at": CREATED_AT,
                "checker_version": "delivery-api-test",
            }
        )
    write_projection(workspace, "artifacts.json", artifacts)
    write_projection(workspace, "gates.json", gates)
    write_projection(workspace, "approvals.json", approvals)
    write_projection(workspace, "releases.json", releases)
    write_projection(
        workspace,
        "tasks.json",
        [
            {
                **identity,
                "task_id": "task-delivery-0001",
                "run_id": "run-step-4a-0001",
                "step_id": "4a",
                "task_type": "missing_input",
                "title": "Publish approved briefing",
                "description": "Prepare the approved briefing for publication.",
                "owner_role": "operator",
                "priority": "high",
                "blocking_scope": "step",
                "artifact": {"artifact_id": "artifact-copywriter-handoff-0001", "content_sha256": artifacts[-2]["content_sha256"], "revision": 1},
                "evidence": [{"evidence_id": "evidence-delivery-0001", "content_sha256": hashlib.sha256(b"delivery evidence").hexdigest()}],
                "acceptance_criteria": ["The approved briefing is ready for the copywriter."],
                "resolution_method": "provide_input",
                "status": "open",
                "operator_action": {"action": "request_input", "requested_by": "operator-raphael", "requested_at": CREATED_AT, "instructions": "Prepare the publication handoff."},
            }
        ],
    )
    write_projection(workspace, "assignments.json", [{**identity, "assignment_id": "assignment-delivery-0001", "task_id": "task-delivery-0001", "assigned_role": "copywriter"}])
    write_projection(workspace, "reviews.json", [{**identity, "review_id": "review-delivery-0001", "artifact_id": "artifact-copywriter-handoff-0001", "status": "required"}])
    write_projection(workspace, "blockers.json", [{**identity, "blocker_id": "blocker-delivery-0001", "task_id": "task-delivery-0001", "artifact_id": "artifact-copywriter-handoff-0001", "status": "open"}])
    write_projection(workspace, "reports.json", [{**identity, "report_id": "report-delivery-0001", "status": "current"}])
    write_projection(workspace, "operator-records/operator-task/task-delivery-0001.json", {**identity, "task_id": "task-delivery-0001", "record_type": "operator-task", "status": "open"})


def delivery_request(
    *,
    scope: str = "checkpoint",
    idempotency_key: str = "idem-delivery-00000001",
    created_at: str = CREATED_AT,
    export_id: str = "delivery-export-00000001",
    delivery_package_id: str = "delivery-package-00000001",
    delivery_export_result_id: str = "delivery-export-result-00000001",
    delivery_export_request_id: str = "delivery-export-request-00000001",
    package_revision: int = 7,
    roles: tuple[str, ...] = ("copywriter", "developer"),
) -> dict[str, JsonValue]:
    request: dict[str, JsonValue] = {
        "export_request": {
            "delivery_export_request_id": delivery_export_request_id,
            "schema_version": "1.0.0",
            "tenant_id": TENANT,
            "project_id": PROJECT,
            "scope": scope,
            "draft_inclusion_policy": "exclude_drafts",
            "idempotency_key": idempotency_key,
            "created_at": created_at,
            "source_snapshot_revision": 11,
            "requested_role_packages": list(roles),
        },
        "export_id": export_id,
        "delivery_package_id": delivery_package_id,
        "delivery_export_result_id": delivery_export_result_id,
        "package_revision": package_revision,
        "role_package_requests": [
            {"role": role, "role_handoff_manifest_id": f"role-handoff-{role}-00000001"}
            for role in roles
        ],
        "notion_import_request": {
            "notion_import_manifest_id": "notion-import-00000001",
            "customer_external_id": "customer-delivery-0001",
            "implementation_tasks": [
                {
                    "task_id": "task-implementation-0001",
                    "assignment_id": "assignment-implementation-0001",
                    "title": "Publish delivery package",
                    "status": "not_started",
                    "comments": "",
                    "source_assignee": "",
                    "priority": "high",
                    "deadline": "2026-09-01",
                    "role": "copywriter",
                    "dependencies": [],
                    "artifact_relations": [],
                }
            ],
            "publication_registry": {
                "publication_registry_record_id": "publication-registry-00000001",
                "urls": ["https://example.test/publish/delivery"],
            },
        },
    }
    return request


def changed_request(request: dict[str, JsonValue]) -> dict[str, JsonValue]:
    return copy.deepcopy(request)
