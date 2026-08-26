from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry
from tests.test_step0_cross_binding import accepted_intake, neutral_manifest, project


ROOT = Path(__file__).resolve().parents[1]
TENANT = "tenant-neutral"
PROJECT = "project-neutral"
RUN = "run-neutral-0001"
ACTOR = "operator-heartweb-admin"
VERBS = (
    "start", "submit-for-gate", "approve", "reject", "request-revision",
    "request-input", "escalate", "request-waiver", "complete",
)


def write(workspace: Path, name: str, value: object) -> None:
    path = workspace / "v2/operator" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def seed(workspace: Path) -> None:
    project_v2 = project()
    write(workspace, "project.json", {"tenant_id": TENANT, "project_id": PROJECT})
    write(workspace, "project-v2.json", project_v2)
    write(workspace, "intake.json", {"tenant_id": TENANT, "project_id": PROJECT, **accepted_intake()})
    write(workspace, "logical-session.json", {"tenant_id": TENANT, "project_id": PROJECT})
    write(workspace, "workflow.json", {"tenant_id": TENANT, "project_id": PROJECT})
    write(workspace, f"runs/{RUN}.json", {"tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": "0", "gate_id": "GATE-0", "revision": 1, "input_hash": "0" * 64, "status": "pending", "attempt": 1, "created_at": "2026-08-20T00:00:00Z"})
    for collection in ("artifacts", "gates", "tasks", "tickets", "assignments", "context-packages", "llm-runs", "performance-checkpoints", "metrics", "adjustment-proposals", "integrations-status", "approvals"):
        write(workspace, f"{collection}.json", [])


def save_candidate(client: TestClient, base: str, workspace: Path, *, key: str = "idem-artifact-save-0001") -> None:
    run = json.loads((workspace / f"v2/operator/runs/{RUN}.json").read_text(encoding="utf-8"))
    if run["status"] == "pending":
        run["status"] = "in_progress"
        write(workspace, f"runs/{RUN}.json", run)
    response = client.post(f"{base}/artifacts", json={
        "run_id": RUN, "expected_parent_revision": 1, "idempotency_key": key,
        "primary_document": neutral_manifest(), "supporting_documents": (), "bundle": {},
        "gate_context": {"evidence_by_gate": {}},
    })
    assert response.status_code == 200, response.text


def intent(verb: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "action": verb,
        "tenant_id": TENANT,
        "project_id": PROJECT,
        "run_id": RUN,
        "step_id": "0",
        "expected_revision": 1,
        "payload": {"reason": "Operator action is required.", "instructions": "Apply the canonical action."},
    }
    value.update(overrides)
    return value


class ActionFacadeTests(unittest.TestCase):
    def test_artifact_save_rejects_ghost_run_and_replays_canonical_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed(workspace)
            write(workspace, f"runs/{RUN}.json", {"tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": "0", "gate_id": "GATE-0", "revision": 1, "input_hash": "a" * 64, "status": "in_progress", "attempt": 1, "created_at": "2026-08-20T00:00:00Z"})
            client = self.client(workspace)
            base = f"/v1/tenants/{TENANT}/projects/{PROJECT}"
            ghost = client.post(f"{base}/artifacts", json={"run_id": "run-ghost-0001"})
            self.assertEqual(422, ghost.status_code)
            save_candidate(client, base, workspace)
            before = client.get(f"{base}/artifacts").json()["data"]
            save_candidate(client, base, workspace)
            after = client.get(f"{base}/artifacts").json()["data"]
            self.assertEqual(before, after)
            conflicting = neutral_manifest()
            conflicting["target_audience"] = "A different but schema-valid audience synthesis"
            conflict = client.post(f"{base}/artifacts", json={
                "run_id": RUN,
                "expected_parent_revision": 1,
                "idempotency_key": "idem-artifact-save-0001",
                "primary_document": conflicting,
                "supporting_documents": (),
                "bundle": {},
                "gate_context": {"evidence_by_gate": {}},
            })
            self.assertEqual(409, conflict.status_code)
            self.assertEqual("ERR_IDEMPOTENCY_CONFLICT", conflict.json()["code"])

    def client(self, workspace: Path) -> TestClient:
        return TestClient(create_app(WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),)), ROOT))

    def route(self, verb: str, suffix: str) -> str:
        return f"/v1/tenants/{TENANT}/projects/{PROJECT}/actions/{verb}/{suffix}"

    def test_each_required_action_has_read_only_preview_with_exact_blocker_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed(workspace)
            client = self.client(workspace)

            for verb in VERBS:
                with self.subTest(verb=verb):
                    response = client.post(self.route(verb, "preview"), json=intent(verb))
                    self.assertEqual(200, response.status_code)
                    preview = response.json()
                    self.assertEqual(verb, preview["intent"]["action"])
                    self.assertEqual(64, len(preview["preview_hash"]))
            self.assertFalse((workspace / "v2/operator/events/events.jsonl").exists())
            start = client.post(self.route("start", "preview"), json=intent("start")).json()
            self.assertFalse(start["allowed"])
            self.assertEqual("ERR_GATE_REQUIRED", start["blockers"][0]["code"])

    def test_confirm_requires_explicit_admin_identity_and_fresh_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed(workspace)
            client = self.client(workspace)
            reviewed = intent("request-input")
            preview = client.post(self.route("request-input", "preview"), json=reviewed).json()

            unconfirmed = client.post(self.route("request-input", "confirm"), json={"intent": reviewed, "preview_hash": preview["preview_hash"], "idempotency_key": "idem-action-false-0001", "confirmed": False})
            wrong_actor = client.post(self.route("request-input", "preview"), json={**intent("request-input"), "actor_id": "operator-other-admin"})
            stale_revision = client.post(self.route("request-input", "preview"), json=intent("request-input", expected_revision=2))
            self.assertEqual(422, unconfirmed.status_code)
            self.assertEqual(422, wrong_actor.status_code)
            self.assertEqual(200, stale_revision.status_code)
            self.assertEqual("ERR_STALE_REVISION", stale_revision.json()["blockers"][0]["code"])

    def test_client_actor_authority_is_rejected_in_all_execution_modes(self) -> None:
        # Given: identical canonical workspaces behind real and simulated application modes.
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed(workspace)
            registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
            real = TestClient(create_app(registry, ROOT, AppConfig(ROOT, execution_mode="real")))
            simulated = TestClient(create_app(registry, ROOT, AppConfig(ROOT, execution_mode="simulated")))

            # When: the explicitly labelled automated test actor previews an action.
            payload = {**intent("request-input"), "actor_id": "operator-test-admin"}
            real_response = real.post(self.route("request-input", "preview"), json=payload)
            simulated_response = simulated.post(self.route("request-input", "preview"), json=payload)

            # Then: server-owned authority rejects a client actor in either mode.
            self.assertEqual(422, real_response.status_code)
            self.assertEqual(422, simulated_response.status_code)

    def test_each_verb_rejects_unconfirmed_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed(workspace)
            client = self.client(workspace)

            for verb in VERBS:
                with self.subTest(verb=verb):
                    reviewed = intent(verb)
                    preview = client.post(self.route(verb, "preview"), json=reviewed).json()
                    response = client.post(self.route(verb, "confirm"), json={"intent": reviewed, "preview_hash": preview["preview_hash"], "idempotency_key": f"idem-action-{verb}-0001", "confirmed": False})
                    self.assertEqual(422, response.status_code)
            self.assertFalse((workspace / "v2/operator/events/events.jsonl").exists())

    def test_operator_actions_confirm_through_canonical_record_readback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed(workspace)
            client = self.client(workspace)
            base = f"/v1/tenants/{TENANT}/projects/{PROJECT}"
            save_candidate(client, base, workspace)

            for index, verb in enumerate(("reject", "request-revision", "request-input", "escalate", "request-waiver")):
                with self.subTest(verb=verb):
                    reviewed = intent(verb)
                    preview = client.post(self.route(verb, "preview"), json=reviewed).json()
                    response = client.post(self.route(verb, "confirm"), json={"intent": reviewed, "preview_hash": preview["preview_hash"], "idempotency_key": f"idem-action-record-{index:04d}", "confirmed": True})
                    self.assertEqual(200, response.status_code)
                    self.assertEqual(200, client.get(response.json()["readback_urls"][0]).status_code)

    def test_resolve_requires_an_open_canonical_source_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed(workspace)
            client = self.client(workspace)
            base = f"/v1/tenants/{TENANT}/projects/{PROJECT}"
            save_candidate(client, base, workspace)
            reviewed = intent("resolve", payload={"source_type": "blocker", "source_id": "blocker-missing-0001"})

            preview = client.post(self.route("resolve", "preview"), json=reviewed)

            self.assertEqual(422, preview.status_code)

    def test_confirmation_reuses_the_preview_clock_value_after_clock_advances(self) -> None:
        class MutableClock:
            def __init__(self) -> None:
                self.value = "2026-08-20T00:00:00Z"

            def now(self) -> str:
                return self.value

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed(workspace)
            clock = MutableClock()
            registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
            client = TestClient(create_app(registry, ROOT, AppConfig(ROOT, clock=clock)))
            base = f"/v1/tenants/{TENANT}/projects/{PROJECT}"
            save_candidate(client, base, workspace)
            reviewed = intent("request-input")
            preview = client.post(self.route("request-input", "preview"), json=reviewed).json()
            clock.value = "2026-08-20T01:00:00Z"

            confirmed = client.post(self.route("request-input", "confirm"), json={"intent": reviewed, "preview_hash": preview["preview_hash"], "idempotency_key": "idem-action-clock-0001", "confirmed": True})

            self.assertEqual(200, confirmed.status_code)
            self.assertEqual("2026-08-20T00:00:00Z", confirmed.json()["canonical"]["record"]["reported_at"])

    def test_confirm_rejects_stale_preview_and_returns_canonical_readback_on_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed(workspace)
            client = self.client(workspace)
            reviewed = intent("request-input")
            preview = client.post(self.route("request-input", "preview"), json=reviewed).json()
            save_candidate(client, f"/v1/tenants/{TENANT}/projects/{PROJECT}", workspace)
            stale = client.post(self.route("request-input", "confirm"), json={"intent": reviewed, "preview_hash": preview["preview_hash"], "idempotency_key": "idem-action-stale-0001", "confirmed": True})
            self.assertEqual(409, stale.status_code)
            self.assertEqual("ERR_STALE_REVISION", stale.json()["code"])

            current = client.post(self.route("request-input", "preview"), json=reviewed).json()
            payload = {"intent": reviewed, "preview_hash": current["preview_hash"], "idempotency_key": "idem-action-replay-0001", "confirmed": True}
            accepted = client.post(self.route("request-input", "confirm"), json=payload)
            replayed = client.post(self.route("request-input", "confirm"), json=payload)
            conflicting = client.post(self.route("request-input", "confirm"), json={**payload, "intent": intent("request-input", payload={"reason": "Different reason.", "instructions": "Apply the canonical action."})})
            self.assertEqual(200, accepted.status_code)
            self.assertEqual(200, replayed.status_code)
            self.assertFalse(accepted.json()["replay"])
            self.assertTrue(replayed.json()["replay"])
            self.assertEqual(409, conflicting.status_code)
            self.assertEqual(200, client.get(accepted.json()["readback_urls"][0]).status_code)
            self.assertEqual(accepted.json()["canonical"], replayed.json()["canonical"])

    def test_confirm_rejects_preview_after_canonical_gate_or_run_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed(workspace)
            client = self.client(workspace)
            reviewed = intent("request-input")
            preview = client.post(self.route("request-input", "preview"), json=reviewed).json()
            write(workspace, "gates.json", [{"quality_gate_run_id": "qgr-action-0001"}])
            gate_stale = client.post(self.route("request-input", "confirm"), json={"intent": reviewed, "preview_hash": preview["preview_hash"], "idempotency_key": "idem-action-gate-0001", "confirmed": True})
            self.assertEqual(409, gate_stale.status_code)
            self.assertEqual("ERR_STALE_REVISION", gate_stale.json()["code"])

            refreshed = client.post(self.route("request-input", "preview"), json=reviewed).json()
            run = json.loads((workspace / f"v2/operator/runs/{RUN}.json").read_text(encoding="utf-8"))
            run["status"] = "in_progress"
            write(workspace, f"runs/{RUN}.json", run)
            run_stale = client.post(self.route("request-input", "confirm"), json={"intent": reviewed, "preview_hash": refreshed["preview_hash"], "idempotency_key": "idem-action-run-0001", "confirmed": True})
            self.assertEqual(409, run_stale.status_code)
            self.assertEqual("ERR_STALE_REVISION", run_stale.json()["code"])

    def test_action_routes_are_tenant_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed(workspace)
            client = self.client(workspace)
            route = "/v1/tenants/tenant-other/projects/project-neutral/actions/request-input/preview"
            self.assertEqual(404, client.post(route, json=intent("request-input", tenant_id="tenant-other")).status_code)


if __name__ == "__main__":
    unittest.main()
