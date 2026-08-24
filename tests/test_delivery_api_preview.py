from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry
from tests.support.delivery_api import PROJECT, TENANT, delivery_base, seed_workspace, workspace_snapshot


ROOT = Path(__file__).resolve().parents[1]


class RaisingClock:
    def now(self) -> str:
        raise AssertionError("Delivery endpoints must preserve caller-supplied timestamps without reading the server clock.")


class DeliveryApiPreviewTests(unittest.TestCase):
    def client(self, workspace: Path) -> TestClient:
        registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
        return TestClient(create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock())))

    def route(self, suffix: str = "") -> str:
        return f"{delivery_base()}{suffix}"

    def test_preview_checkpoint_reports_eligibility_missing_and_selected_deliverables_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            before = workspace_snapshot(workspace, include_delivery=True)

            response = self.client(workspace).get(self.route("/preview"), params={"scope": "checkpoint"})

            self.assertEqual(200, response.status_code)
            preview = response.json()
            self.assertEqual("checkpoint", preview["scope"])
            self.assertTrue(preview["policy_eligible"])
            self.assertNotIn("eligible", preview)
            self.assertEqual((), tuple(preview["missing_deliverable_ids"]))
            self.assertEqual(7, len(preview["selected_deliverables"]))
            self.assertEqual(before, workspace_snapshot(workspace, include_delivery=True))

    def test_preview_final_reports_policy_failure_without_creating_delivery_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace, incomplete_final=True)

            response = self.client(workspace).get(self.route("/preview"), params={"scope": "final"})

            self.assertEqual(200, response.status_code)
            preview = response.json()
            self.assertFalse(preview["policy_eligible"])
            self.assertNotIn("eligible", preview)
            self.assertIn("developer-handoff", preview["missing_deliverable_ids"])
            self.assertFalse((workspace / "v2/operator/delivery").exists())

    def test_registry_rejects_unknown_cross_tenant_and_traversal_delivery_workspaces(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)

            known = client.get(self.route("/preview"), params={"scope": "checkpoint"})
            responses = (
                client.get("/v1/tenants/tenant-other/projects/project-demo/delivery/preview", params={"scope": "checkpoint"}),
                client.get(f"/v1/tenants/{TENANT}/projects/project-unknown/delivery/preview", params={"scope": "checkpoint"}),
                client.get(f"/v1/tenants/{TENANT}/projects/..%2Fsecret/delivery/preview", params={"scope": "checkpoint"}),
            )

            self.assertEqual(200, known.status_code)
            self.assertEqual(404, responses[0].status_code)
            self.assertEqual(404, responses[1].status_code)
            self.assertIn(responses[2].status_code, {404, 422})


if __name__ == "__main__":
    unittest.main()
