from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.operator_api.app import create_app
from services.operator_api.repository import (
    ProjectRepository,
    RepositoryError,
    WorkspaceRegistration,
    WorkspaceRegistry,
)
from services.operator_api.transition_recovery import TransitionRecovery


ROOT = Path(__file__).resolve().parents[1]
TENANT = "tenant-demo"
PROJECT = "project-demo"
RUN = "run-00000001"
OPERATOR_FIXTURE = ROOT / "tests/fixtures/operator/valid-operator-task.json"
RECORD_EVENT_TYPES = {
    "request-revision": "task.created", "request-input": "step.blocked", "create-defect": "defect.created",
    "escalate": "escalation.created", "request-waiver": "task.created", "reject": "gate.rejected", "resolve": "task.resolved",
}


def write(workspace: Path, name: str, value: object) -> None:
    path = workspace / "v2/operator" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def event() -> dict[str, object]:
    return {
        "event_id": "event-00000001", "event_type": "run.started", "schema_version": "2.0.0",
        "occurred_at": "2026-08-20T00:00:00Z", "correlation_id": "corr-00000001",
        "idempotency_key": "idem-00000001",
        "identity": {"tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": "0", "revision": 1},
        "integration_mode": "simulated", "simulation_id": "sim-00000001",
        "payload": {"attempt": 1, "input_hash": "0" * 64},
    }


def command() -> dict[str, object]:
    return {
        "command": "start", "command_id": "command-00000001", "correlation_id": "corr-00000001",
        "idempotency_key": "idem-00000001", "tenant_id": TENANT, "project_id": PROJECT,
        "run_id": RUN, "step_id": "0", "expected_revision": 1,
        "transition_command": {
            "command_id": "command-00000001", "tenant_id": TENANT, "project_id": PROJECT,
            "run_id": RUN, "expected_revision": 1, "idempotency_key": "idem-00000001",
            "operation": "start", "from_step_id": "0", "to_step_id": "0", "input_hash": "0" * 64,
            "requested_at": "2026-08-20T00:00:00Z",
        },
        "event": event(),
    }


def operator_record(task_id: str) -> dict[str, object]:
    record = json.loads(OPERATOR_FIXTURE.read_text(encoding="utf-8"))
    record.update({"task_id": task_id, "tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": "0"})
    return record


def record_command(verb: str, record: dict[str, object], suffix: str) -> dict[str, object]:
    record_event = event()
    record_event.update({"event_id": f"event-record-{suffix}", "event_type": RECORD_EVENT_TYPES[verb], "correlation_id": f"corr-record-{suffix}", "idempotency_key": f"idem-record-{suffix}"})
    if verb == "request-input":
        record_event["payload"] = {"blocker_id": "blocker-00000001", "reason": "input is required"}
    return {
        "command": verb, "command_id": f"command-record-{suffix}", "correlation_id": f"corr-record-{suffix}",
        "idempotency_key": f"idem-record-{suffix}", "tenant_id": TENANT, "project_id": PROJECT,
        "run_id": RUN, "step_id": "0", "expected_revision": 1, "record_type": "operator-task",
        "operator_record": record, "event": record_event,
    }


class OperatorApiTests(unittest.TestCase):
    def client(self, workspace: Path) -> TestClient:
        registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
        return TestClient(create_app(registry=registry, repository_root=ROOT))

    def seed(self, workspace: Path) -> None:
        write(workspace, "project.json", {"tenant_id": TENANT, "project_id": PROJECT, "name": "Neutral Project"})
        write(workspace, "logical-session.json", {"tenant_id": TENANT, "project_id": PROJECT, "logical_session_id": "session-00000001"})
        write(workspace, "workflow.json", {"tenant_id": TENANT, "project_id": PROJECT, "initial_edges": [{"from_step_id": "0", "to_step_id": "1"}], "sideflows": [{"step_id": "3b", "status": "not_due"}]})
        write(workspace, f"runs/{RUN}.json", {"tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": "0", "gate_id": "GATE-0", "revision": 1, "input_hash": "0" * 64, "status": "pending", "attempt": 1})
        write(workspace, "steps.json", [{"step_id": "0", "status": "pending"}])
        for collection in ("artifacts", "gates", "tasks", "tickets", "assignments", "context-packages", "llm-runs", "performance-checkpoints", "metrics", "adjustment-proposals", "integrations-status"):
            write(workspace, f"{collection}.json", [])
        supporting = {"artifact_id": "artifact-contract-0001", "tenant_id": TENANT, "project_id": PROJECT, "run_id": "run-contract-0001", "step_id": "0", "revision": 1, "content_sha256": "c" * 64}
        write(workspace, "artifacts.json", [supporting])
        write(workspace, "gates.json", [{"quality_gate_run_id": "qgr-contract-0001", "quality_gate_id": "qg-domain-contract", "human_gate_id": "GATE-0", "tenant_id": TENANT, "run_id": "run-contract-0001", "step_id": "0", "artifact_id": supporting["artifact_id"], "artifact_sha256": supporting["content_sha256"], "artifact_revision": 1, "registry_version": "1.1.0", "policy_version": "1.1.0", "result": "passed", "evidence": {"schema_id": "runtime", "schema_version": "1.0.0", "artifact_sha256": supporting["content_sha256"], "validator_result": "passed"}, "checked_at": "2026-08-20T00:00:00Z", "checker_version": "test-1.0.0"}])

    def test_read_families_expose_projections_and_3b_sideflow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.seed(workspace)
            client = self.client(workspace)
            base = f"/v1/tenants/{TENANT}/projects/{PROJECT}"
            routes = ("", "/logical-session", "/workflow", "/steps", "/steps/0", "/artifacts", "/gates", "/tasks", "/tickets", "/assignments", "/context-packages", f"/runs/{RUN}", f"/runs/{RUN}/history", "/performance-checkpoints", "/metrics", "/adjustment-proposals", "/integrations/status")

            for route in routes:
                with self.subTest(route=route):
                    response = client.get(f"{base}{route}")
                    self.assertEqual(200, response.status_code)
                    self.assertIn("data", response.json())
            workflow = client.get(f"{base}/workflow").json()["data"]
            self.assertEqual("3b", workflow["sideflows"][0]["step_id"])
            self.assertEqual("not_due", workflow["sideflows"][0]["status"])

    def test_health_and_readiness_routes_reflect_a_healthy_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.seed(workspace)
            client = self.client(workspace)

            self.assertEqual({"data": {"status": "alive"}}, client.get("/healthz").json())
            self.assertEqual({"data": {"status": "ready"}}, client.get("/readyz").json())

    def test_rejects_unknown_cross_tenant_and_traversal_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.seed(workspace)
            client = self.client(workspace)

            self.assertEqual(404, client.get(f"/v1/tenants/{TENANT}/projects/project-unknown").status_code)
            self.assertEqual(404, client.get(f"/v1/tenants/tenant-other/projects/{PROJECT}").status_code)
            self.assertIn(client.get(f"/v1/tenants/{TENANT}/projects/..%2Fsecret").status_code, {404, 422})

    def test_start_delegates_then_appends_before_projection_and_replays(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.seed(workspace)
            client = self.client(workspace)
            route = f"/v1/tenants/{TENANT}/projects/{PROJECT}/commands/start"

            invalid = command()
            invalid["tenant_id"] = "tenant-other"
            self.assertEqual(409, client.post(route, json=invalid).status_code)
            first = client.post(route, json=command())
            replay = client.post(route, json=command())
            self.assertEqual(200, first.status_code)
            self.assertFalse(first.json()["replay"])
            self.assertEqual(200, replay.status_code)
            self.assertTrue(replay.json()["replay"])
            self.assertEqual("in_progress", json.loads((workspace / f"v2/operator/runs/{RUN}.json").read_text(encoding="utf-8"))["status"])

    def test_transition_projection_recovery_repairs_the_exact_appended_event(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.seed(workspace)
            client = self.client(workspace)
            route = f"/v1/tenants/{TENANT}/projects/{PROJECT}/commands/start"

            with patch.object(
                TransitionRecovery,
                "finalize",
                side_effect=RepositoryError("ERROR_CONTEXT_SOURCE_INVALID", "Projection is unavailable."),
            ):
                self.assertEqual(503, client.post(route, json=command()).status_code)

            sidecar = workspace / "v2/operator/transition-recovery/command-00000001.json"
            self.assertTrue(sidecar.exists())
            self.assertEqual("pending", json.loads((workspace / f"v2/operator/runs/{RUN}.json").read_text(encoding="utf-8"))["status"])
            self.assertEqual(1, len((workspace / "v2/operator/events/events.jsonl").read_text(encoding="utf-8").splitlines()))
            self.assertEqual(503, client.get("/readyz").status_code)

            replay = client.post(route, json=command())

            self.assertEqual(200, replay.status_code)
            self.assertTrue(replay.json()["replay"])
            self.assertFalse(sidecar.exists())
            self.assertEqual("in_progress", json.loads((workspace / f"v2/operator/runs/{RUN}.json").read_text(encoding="utf-8"))["status"])
            self.assertEqual(1, len((workspace / "v2/operator/events/events.jsonl").read_text(encoding="utf-8").splitlines()))

    def test_transition_nested_identity_mismatch_matrix_rejects_before_mutation(self) -> None:
        cases = (
            ("command_id", "command-00000002", 409), ("tenant_id", "tenant-other", 409),
            ("project_id", "project-other", 409), ("run_id", "run-00000002", 409),
            ("expected_revision", 2, 409), ("idempotency_key", "idem-00000002", 409),
            ("step_id", "1", 422), ("operation", "retry", 409),
        )
        for field, value, status in cases:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temporary:
                    workspace = Path(temporary)
                    self.seed(workspace)
                    payload = command()
                    payload["transition_command"][field] = value
                    response = self.client(workspace).post(f"/v1/tenants/{TENANT}/projects/{PROJECT}/commands/start", json=payload)
                    self.assertEqual(status, response.status_code)
                    self.assertFalse((workspace / "v2/operator/events/events.jsonl").exists())
                    self.assertEqual("pending", json.loads((workspace / f"v2/operator/runs/{RUN}.json").read_text(encoding="utf-8"))["status"])

    def test_reordered_operator_records_use_distinct_canonical_identities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.seed(workspace)
            first = operator_record("task-00000001")
            reordered = {"tenant_id": first.pop("tenant_id"), **first}
            second = operator_record("task-00000002")
            client = self.client(workspace)
            route = f"/v1/tenants/{TENANT}/projects/{PROJECT}/commands/request-input"
            self.assertEqual(200, client.post(route, json=record_command("request-input", reordered, "one")).status_code)
            self.assertEqual(200, client.post(route, json=record_command("request-input", second, "two")).status_code)
            records = workspace / "v2/operator/operator-records/operator-task"
            self.assertEqual("task-00000001", json.loads((records / "task-00000001.json").read_text(encoding="utf-8"))["task_id"])
            self.assertEqual("task-00000002", json.loads((records / "task-00000002.json").read_text(encoding="utf-8"))["task_id"])

    def test_projection_recovery_replays_without_second_event_after_containment_repair(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.seed(workspace)
            payload = record_command("request-input", operator_record("task-00000001"), "recovery")
            client = self.client(workspace)
            route = f"/v1/tenants/{TENANT}/projects/{PROJECT}/commands/request-input"
            with patch.object(
                ProjectRepository,
                "finalize_operator_recovery",
                side_effect=RepositoryError("ERR_TENANT_ISOLATION", "Projection is unavailable."),
            ):
                self.assertEqual(503, client.post(route, json=payload).status_code)
            sidecar = workspace / "v2/operator/projection-recovery/operator-task--task-00000001.json"
            self.assertTrue(sidecar.exists())
            self.assertEqual(503, client.get("/readyz").status_code)
            self.assertEqual(1, len((workspace / "v2/operator/events/events.jsonl").read_text(encoding="utf-8").splitlines()))
            replay = client.post(route, json=payload)
            self.assertEqual(200, replay.status_code)
            self.assertTrue(replay.json()["replay"])
            self.assertFalse(sidecar.exists())
            self.assertTrue((workspace / "v2/operator/operator-records/operator-task/task-00000001.json").exists())
            self.assertEqual(200, client.get("/readyz").status_code)
            self.assertEqual(1, len((workspace / "v2/operator/events/events.jsonl").read_text(encoding="utf-8").splitlines()))

    def test_pending_recovery_is_unready_and_conflict_cannot_consume_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.seed(workspace)
            payload = record_command("request-input", operator_record("task-00000001"), "pending")
            route = f"/v1/tenants/{TENANT}/projects/{PROJECT}/commands/request-input"
            client = self.client(workspace)
            with patch.object(
                ProjectRepository,
                "finalize_operator_recovery",
                side_effect=RepositoryError("ERR_TENANT_ISOLATION", "Projection is unavailable."),
            ):
                self.assertEqual(503, client.post(route, json=payload).status_code)
            restarted = self.client(workspace)
            self.assertEqual(503, restarted.get("/readyz").status_code)
            conflicting = json.loads(json.dumps(payload))
            conflicting["event"]["event_id"] = "event-record-conflict"
            self.assertEqual(409, restarted.post(route, json=conflicting).status_code)
            self.assertTrue((workspace / "v2/operator/projection-recovery/operator-task--task-00000001.json").exists())

    def test_pending_recovery_blocks_unrelated_workspace_command(self) -> None:
        with tempfile.TemporaryDirectory() as first_temporary, tempfile.TemporaryDirectory() as second_temporary:
            first_workspace = Path(first_temporary)
            second_workspace = Path(second_temporary)
            self.seed(first_workspace)
            self.seed(second_workspace)
            second_tenant = "tenant-other"
            second_project = "project-other"
            registry = WorkspaceRegistry(
                (
                    WorkspaceRegistration(TENANT, PROJECT, first_workspace),
                    WorkspaceRegistration(second_tenant, second_project, second_workspace),
                )
            )
            client = TestClient(create_app(registry=registry, repository_root=ROOT))
            first_payload = record_command("request-input", operator_record("task-00000001"), "first-pending")
            first_route = f"/v1/tenants/{TENANT}/projects/{PROJECT}/commands/request-input"
            with patch.object(
                ProjectRepository,
                "finalize_operator_recovery",
                side_effect=RepositoryError("ERR_TENANT_ISOLATION", "Projection is unavailable."),
            ):
                self.assertEqual(503, client.post(first_route, json=first_payload).status_code)
            self.assertEqual(503, client.get("/readyz").status_code)

            second_record = operator_record("task-00000002")
            second_record.update(tenant_id=second_tenant, project_id=second_project)
            second_payload = record_command("request-input", second_record, "second-success")
            second_payload.update(tenant_id=second_tenant, project_id=second_project)
            second_payload["event"]["identity"].update(tenant_id=second_tenant, project_id=second_project)
            second_route = f"/v1/tenants/{second_tenant}/projects/{second_project}/commands/request-input"
            self.assertEqual(503, client.post(second_route, json=second_payload).status_code)
            self.assertEqual(503, client.get("/readyz").status_code)
            self.assertTrue(
                (first_workspace / "v2/operator/projection-recovery/operator-task--task-00000001.json").exists()
            )

    def test_event_append_failure_cleans_sidecar_and_all_operator_verb_allowlists_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.seed(workspace)
            client = self.client(workspace)
            route = f"/v1/tenants/{TENANT}/projects/{PROJECT}/commands/request-input"
            invalid_event = record_command("request-input", operator_record("task-00000001"), "invalid")
            invalid_event["event"]["payload"] = {"blocker_id": "blocker-00000001"}
            self.assertEqual(422, client.post(route, json=invalid_event).status_code)
            recovery_root = workspace / "v2/operator/projection-recovery"
            self.assertFalse(recovery_root.exists() and any(recovery_root.iterdir()))
            self.assertFalse((workspace / "v2/operator/operator-records/operator-task/task-00000001.json").exists())
            for verb in RECORD_EVENT_TYPES:
                with self.subTest(verb=verb):
                    denied = record_command(verb, operator_record("task-00000003"), f"denied-{verb}")
                    denied["record_type"] = "blocker-record" if verb == "request-input" else "operator-task"
                    self.assertEqual(422, client.post(f"/v1/tenants/{TENANT}/projects/{PROJECT}/commands/{verb}", json=denied).status_code)


    def test_current_run_returns_the_initial_run_and_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.seed(workspace)
            client = self.client(workspace)
            route = f"/v1/tenants/{TENANT}/projects/{PROJECT}/runs/current"
            before = {
                path.relative_to(workspace): path.read_bytes()
                for path in workspace.rglob("*")
                if path.is_file()
            }

            response = client.get(route)

            self.assertEqual(200, response.status_code)
            self.assertEqual(
                {
                    "tenant_id": TENANT,
                    "project_id": PROJECT,
                    "run_id": RUN,
                    "step_id": "0",
                    "expected_revision": 1,
                },
                response.json(),
            )
            after = {
                path.relative_to(workspace): path.read_bytes()
                for path in workspace.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before, after)

    def test_current_run_selects_pending_successor_and_latest_completed_frontier(self) -> None:
        cases = (
            ("pending-successor", "completed", "pending", "run-00000002"),
            ("completed-frontier", "completed", None, RUN),
        )
        for name, initial_status, successor_status, expected_run_id in cases:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as temporary:
                    workspace = Path(temporary)
                    self.seed(workspace)
                    initial = json.loads((workspace / f"v2/operator/runs/{RUN}.json").read_text(encoding="utf-8"))
                    initial["status"] = initial_status
                    write(workspace, f"runs/{RUN}.json", initial)
                    if successor_status is not None:
                        write(workspace, "runs/run-00000002.json", {
                            "tenant_id": TENANT, "project_id": PROJECT, "run_id": "run-00000002",
                            "step_id": "1", "gate_id": "GATE-1", "revision": 2,
                            "input_hash": "1" * 64, "status": successor_status, "attempt": 1,
                        })

                    response = self.client(workspace).get(
                        f"/v1/tenants/{TENANT}/projects/{PROJECT}/runs/current"
                    )

                    self.assertEqual(200, response.status_code)
                    self.assertEqual(expected_run_id, response.json()["run_id"])

    def test_current_run_excludes_step_3b(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.seed(workspace)
            self._copy_run(workspace, "run-00000002", status="superseded")
            write(workspace, "runs/run-0000003b.json", {
                "tenant_id": TENANT, "project_id": PROJECT, "run_id": "run-0000003b",
                "step_id": "3b", "gate_id": "GATE-3B", "revision": 3,
                "input_hash": "3" * 64, "status": "pending", "attempt": 1,
            })

            response = self.client(workspace).get(
                f"/v1/tenants/{TENANT}/projects/{PROJECT}/runs/current"
            )

            self.assertEqual(200, response.status_code)
            self.assertEqual(RUN, response.json()["run_id"])

    def test_current_run_fails_closed_for_invalid_state(self) -> None:
        cases = (
            ("missing", lambda workspace: (workspace / f"v2/operator/runs/{RUN}.json").unlink()),
            ("malformed-revision", lambda workspace: self._replace_run(workspace, revision="1")),
            ("unknown-step", lambda workspace: self._replace_run(workspace, step_id="unknown")),
            ("unknown-status", lambda workspace: self._replace_run(workspace, status="unknown")),
            ("duplicate-step", lambda workspace: self._copy_run(workspace, "run-00000002", step_id="0")),
            ("discontinuous-route", lambda workspace: self._copy_run(workspace, "run-00000002", step_id="1b")),
        )
        for name, mutate in cases:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as temporary:
                    workspace = Path(temporary)
                    self.seed(workspace)
                    mutate(workspace)

                    response = self.client(workspace).get(
                        f"/v1/tenants/{TENANT}/projects/{PROJECT}/runs/current"
                    )

                    self.assertEqual(503, response.status_code)
                    self.assertEqual("ERROR_CONTEXT_SOURCE_INVALID", response.json()["code"])

    def test_current_run_fails_closed_for_symlinked_run_record_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.seed(workspace)
            runs = workspace / "v2/operator/runs"
            link = runs / "run-00000002.json"
            try:
                link.symlink_to(runs / f"{RUN}.json")
            except OSError as error:
                self.skipTest(f"Platform cannot create symlinks: {error}")
            client = self.client(workspace)
            before = self._workspace_snapshot(workspace)

            response = client.get(
                f"/v1/tenants/{TENANT}/projects/{PROJECT}/runs/current"
            )

            self.assertEqual(503, response.status_code)
            self.assertEqual("ERROR_CONTEXT_SOURCE_INVALID", response.json()["code"])
            self.assertEqual(before, self._workspace_snapshot(workspace))

    def test_current_run_fails_closed_for_non_regular_json_run_record_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.seed(workspace)
            (workspace / "v2/operator/runs/non-regular.json").mkdir()
            client = self.client(workspace)
            before = self._workspace_snapshot(workspace)

            response = client.get(
                f"/v1/tenants/{TENANT}/projects/{PROJECT}/runs/current"
            )

            self.assertEqual(503, response.status_code)
            self.assertEqual("ERROR_CONTEXT_SOURCE_INVALID", response.json()["code"])
            self.assertEqual(before, self._workspace_snapshot(workspace))

    def test_current_run_preserves_tenant_isolation_for_record_identity_mismatch(self) -> None:
        for field, value in (("tenant_id", "tenant-other"), ("project_id", "project-other")):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temporary:
                    workspace = Path(temporary)
                    self.seed(workspace)
                    self._replace_run(workspace, **{field: value})

                    response = self.client(workspace).get(
                        f"/v1/tenants/{TENANT}/projects/{PROJECT}/runs/current"
                    )

                    self.assertEqual(404, response.status_code)
                    self.assertEqual("ERR_TENANT_ISOLATION", response.json()["code"])

    @staticmethod
    def _replace_run(workspace: Path, **changes: object) -> None:
        run_path = workspace / f"v2/operator/runs/{RUN}.json"
        run = json.loads(run_path.read_text(encoding="utf-8"))
        run.update(changes)
        write(workspace, f"runs/{RUN}.json", run)

    @staticmethod
    def _copy_run(workspace: Path, run_id: str, **changes: object) -> None:
        run = json.loads((workspace / f"v2/operator/runs/{RUN}.json").read_text(encoding="utf-8"))
        run.update({"run_id": run_id, "revision": 2, **changes})
        write(workspace, f"runs/{run_id}.json", run)

    @staticmethod
    def _workspace_snapshot(workspace: Path) -> tuple[tuple[str, str, bytes | str | None], ...]:
        entries: list[tuple[str, str, bytes | str | None]] = []
        for path in workspace.rglob("*"):
            if path.is_symlink():
                entries.append((str(path.relative_to(workspace)), "symlink", str(path.readlink())))
            elif path.is_file():
                entries.append((str(path.relative_to(workspace)), "file", path.read_bytes()))
            elif path.is_dir():
                entries.append((str(path.relative_to(workspace)), "directory", None))
            else:
                entries.append((str(path.relative_to(workspace)), "other", None))
        return tuple(sorted(entries))


if __name__ == "__main__":
    unittest.main()
