from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry


ROOT = Path(__file__).resolve().parents[1]
TENANT = "tenant-delete-test"
PROJECT = "project-delete-test"
RUN = "run-delete-test"


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical(value), encoding="utf-8")


def _seed(workspace: Path, *, run_status: str = "awaiting_gate") -> None:
    identity = {"tenant_id": TENANT, "project_id": PROJECT}
    operator = workspace / "v2/operator"
    _write(
        operator / "project.json",
        {
            **identity,
            "name": "Delete Test Project",
            "customer": "Delete Test GmbH",
            "current_step": "0",
            "progress": "1 von 8 Schritten",
            "blocker_count": 0,
            "owner": "Heartweb Admin Operator",
            "next_action": "GATE-0 prüfen",
        },
    )
    _write(
        operator / f"runs/{RUN}.json",
        {
            **identity,
            "run_id": RUN,
            "step_id": "0",
            "revision": 1,
            "status": run_status,
        },
    )
    _write(operator / "artifacts.json", [{**identity, "artifact_id": "artifact-delete-test"}])
    _write(operator / "approvals.json", [])
    _write(operator / "releases/release-delete-test.json", {**identity, "release_id": "release-delete-test"})
    content = operator / "artifact-content/artifact-delete-test.md"
    content.parent.mkdir(parents=True, exist_ok=True)
    content.write_text("delete test artifact\n", encoding="utf-8")


def _snapshot(workspace: Path) -> dict[str, bytes]:
    return {
        path.relative_to(workspace).as_posix(): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }


def _client(provisioning_root: Path, registry: WorkspaceRegistry | None = None) -> TestClient:
    return TestClient(
        create_app(
            registry or WorkspaceRegistry(()),
            ROOT,
            AppConfig(
                repository_root=ROOT,
                provisioning_root=provisioning_root,
                provisioning_enabled=True,
            ),
        )
    )


def _base() -> str:
    return f"/v1/tenants/{TENANT}/projects/{PROJECT}"


class ProjectDeletionTests(unittest.TestCase):
    def test_preview_is_read_only_and_confirm_requires_exact_keyword(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Kunden"
            workspace = root / TENANT / PROJECT
            _seed(workspace)
            before = _snapshot(workspace)
            client = _client(root)

            preview_response = client.post(f"{_base()}/deletion/preview")

            self.assertEqual(200, preview_response.status_code)
            preview = preview_response.json()["data"]
            self.assertTrue(preview["allowed"])
            self.assertEqual(PROJECT, preview["project_id"])
            self.assertEqual("Delete Test Project", preview["project_name"])
            self.assertGreater(preview["file_count"], 0)
            self.assertEqual(before, _snapshot(workspace))

            wrong = client.post(
                f"{_base()}/deletion/confirm",
                json={
                    "preview_hash": preview["preview_hash"],
                    "idempotency_key": "idem-project-delete-0001",
                    "confirmed": True,
                    "confirmation_text": "loeschen",
                },
            )

            self.assertEqual(422, wrong.status_code)
            self.assertEqual("ERROR_PROJECT_DELETE_CONFIRMATION_INVALID", wrong.json()["code"])
            self.assertTrue(workspace.is_dir())
            self.assertEqual(before, _snapshot(workspace))

    def test_confirm_deletes_only_the_bound_project_and_reads_absence_back(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Kunden"
            workspace = root / TENANT / PROJECT
            sibling = root / TENANT / "project-delete-sibling"
            _seed(workspace)
            _seed_sibling(sibling)
            client = _client(root)
            preview = client.post(f"{_base()}/deletion/preview").json()["data"]
            request = {
                "preview_hash": preview["preview_hash"],
                "idempotency_key": "idem-project-delete-0002",
                "confirmed": True,
                "confirmation_text": "LOESCHEN",
            }

            response = client.post(f"{_base()}/deletion/confirm", json=request)

            self.assertEqual(200, response.status_code)
            result = response.json()["data"]
            self.assertTrue(result["deleted"])
            self.assertFalse(result["replay"])
            self.assertEqual(PROJECT, result["project_id"])
            self.assertFalse(workspace.exists())
            self.assertTrue(sibling.is_dir())
            project_list = client.get(f"/v1/tenants/{TENANT}/projects")
            self.assertEqual(200, project_list.status_code)
            self.assertEqual(["project-delete-sibling"], [item["project_id"] for item in project_list.json()["data"]])
            self.assertEqual(404, client.get(_base()).status_code)

            replay = client.post(f"{_base()}/deletion/confirm", json=request)
            self.assertEqual(200, replay.status_code)
            self.assertTrue(replay.json()["data"]["replay"])

    def test_changed_workspace_rejects_stale_preview_without_deleting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Kunden"
            workspace = root / TENANT / PROJECT
            _seed(workspace)
            client = _client(root)
            preview = client.post(f"{_base()}/deletion/preview").json()["data"]
            (workspace / "v2/operator/changed-after-preview.txt").write_text("changed\n", encoding="utf-8")

            response = client.post(
                f"{_base()}/deletion/confirm",
                json={
                    "preview_hash": preview["preview_hash"],
                    "idempotency_key": "idem-project-delete-0003",
                    "confirmed": True,
                    "confirmation_text": "LOESCHEN",
                },
            )

            self.assertEqual(409, response.status_code)
            self.assertEqual("ERROR_PROJECT_DELETE_PREVIEW_STALE", response.json()["code"])
            self.assertTrue(workspace.is_dir())

    def test_active_run_blocks_preview_and_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Kunden"
            workspace = root / TENANT / PROJECT
            _seed(workspace, run_status="in_progress")
            client = _client(root)

            preview = client.post(f"{_base()}/deletion/preview").json()["data"]

            self.assertFalse(preview["allowed"])
            self.assertEqual([RUN], preview["active_run_ids"])
            self.assertEqual("ERROR_PROJECT_DELETE_ACTIVE_RUN", preview["blockers"][0]["code"])
            self.assertTrue(workspace.is_dir())

    def test_explicitly_registered_workspace_is_not_deletable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Kunden"
            explicit_workspace = Path(temporary) / "explicit" / PROJECT
            _seed(explicit_workspace)
            registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, explicit_workspace),))
            client = _client(root, registry)

            response = client.post(f"{_base()}/deletion/preview")

            self.assertEqual(403, response.status_code)
            self.assertEqual("ERROR_PROJECT_DELETE_NOT_MANAGED", response.json()["code"])
            self.assertTrue(explicit_workspace.is_dir())


def _seed_sibling(workspace: Path) -> None:
    identity = {"tenant_id": TENANT, "project_id": "project-delete-sibling"}
    _write(
        workspace / "v2/operator/project.json",
        {
            **identity,
            "name": "Sibling Project",
            "customer": "Sibling GmbH",
            "current_step": "0",
            "progress": "0 von 8 Schritten",
            "blocker_count": 0,
            "owner": "Heartweb Admin Operator",
            "next_action": "Schritt 0 starten",
        },
    )


if __name__ == "__main__":
    unittest.main()
