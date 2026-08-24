from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.operator_api.app import AppConfig, create_app
from services.operator_api.delivery_persistence import DeliveryExportRepository, DeliveryPersistenceError
from services.operator_api.delivery_persistence_values import DeliveryFailureBoundary
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry
from tests.support.delivery_api import PROJECT, TENANT, changed_request, delivery_base, delivery_request, seed_workspace, write_projection


ROOT = Path(__file__).resolve().parents[1]
_MISSING_ARTIFACT = "artifact-strategy-0001.md"


class RaisingClock:
    def now(self) -> str:
        raise AssertionError("Delivery endpoints must preserve caller-supplied timestamps without reading the server clock.")


class DeliveryApiReplaySourcesTests(unittest.TestCase):
    def client(self, workspace: Path, *, raise_server_exceptions: bool = True) -> TestClient:
        registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
        return TestClient(
            create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock())),
            raise_server_exceptions=raise_server_exceptions,
        )

    @staticmethod
    def route(suffix: str = "") -> str:
        return f"{delivery_base()}{suffix}"

    @staticmethod
    def remove_source(workspace: Path) -> None:
        (workspace / "v2/operator/artifact-content" / _MISSING_ARTIFACT).unlink()

    def test_completed_replay_succeeds_after_source_disappears(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)
            payload = delivery_request()

            self.assertEqual(201, client.post(self.route("/exports"), json=payload).status_code)
            self.remove_source(workspace)
            replayed = client.post(self.route("/exports"), json=payload)

            self.assertEqual(200, replayed.status_code)
            self.assertEqual("replayed", replayed.json()["replay_state"])
            self.assertEqual(1, len(client.get(self.route("/exports")).json()["data"]))

    def test_completed_replay_ignores_later_final_policy_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)
            payload = delivery_request(scope="final")

            self.assertEqual(201, client.post(self.route("/exports"), json=payload).status_code)
            (workspace / "v2/operator/releases/release-artifact-developer-handoff-0001.json").unlink()
            write_projection(workspace, "releases.json", [])
            replayed = client.post(self.route("/exports"), json=payload)

            self.assertEqual(200, replayed.status_code)
            self.assertEqual("replayed", replayed.json()["replay_state"])

    def test_idempotency_conflict_precedes_missing_source_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)
            payload = delivery_request()

            self.assertEqual(201, client.post(self.route("/exports"), json=payload).status_code)
            self.remove_source(workspace)
            conflicting = changed_request(payload)
            conflicting["export_request"]["scope"] = "final"
            response = client.post(self.route("/exports"), json=conflicting)

            self.assertEqual(409, response.status_code)
            self.assertEqual("ERR_IDEMPOTENCY_CONFLICT", response.json()["code"])

    def test_new_request_still_requires_current_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            self.remove_source(workspace)

            response = self.client(workspace, raise_server_exceptions=False).post(self.route("/exports"), json=delivery_request())

            self.assertEqual(503, response.status_code)
            self.assertEqual("ERROR_CONTEXT_SOURCE_INVALID", response.json()["code"])
            self.assertFalse((workspace / "v2/operator/delivery").exists())

    def test_exact_recovery_succeeds_after_source_disappears(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            payload = delivery_request()
            client = self.client(workspace, raise_server_exceptions=False)

            def interrupt(repository: DeliveryExportRepository, boundary: DeliveryFailureBoundary) -> None:
                if boundary is DeliveryFailureBoundary.ARCHIVE_WRITTEN:
                    raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "injected interruption")

            with patch.object(DeliveryExportRepository, "_inject", new=interrupt):
                self.assertEqual(503, client.post(self.route("/exports"), json=payload).status_code)
            recovery = workspace / "v2/operator/delivery/recovery"
            self.assertTrue(any(recovery.iterdir()))
            self.remove_source(workspace)
            repaired = client.post(self.route("/exports"), json=payload)

            self.assertEqual(200, repaired.status_code)
            self.assertFalse(any(recovery.iterdir()))
            self.assertEqual(200, client.get("/readyz").status_code)


if __name__ == "__main__":
    unittest.main()
