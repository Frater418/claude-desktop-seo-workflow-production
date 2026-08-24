from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry
from tests.support.delivery_api import PROJECT, TENANT, delivery_base, delivery_request, seed_workspace


ROOT = Path(__file__).resolve().parents[1]


class RaisingClock:
    def now(self) -> str:
        raise AssertionError("Delivery endpoints must preserve caller-supplied timestamps without reading the server clock.")


class DeliveryApiRecoveryInventorySafetyTests(unittest.TestCase):
    def test_unsafe_recovery_inventory_blocks_readiness_and_create_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            seed_workspace(workspace)
            outside = Path(temporary) / "outside"
            outside.mkdir()
            (workspace / "v2/operator/delivery").mkdir()
            os.symlink(outside, workspace / "v2/operator/delivery/recovery")
            registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
            client = TestClient(create_app(registry, ROOT, AppConfig(ROOT, allow_unready=True, clock=RaisingClock())), raise_server_exceptions=False)

            ready = client.get("/readyz")
            created = client.post(f"{delivery_base()}/exports", json=delivery_request())

            self.assertEqual(503, ready.status_code)
            self.assertEqual(503, created.status_code)
            self.assertEqual("ERROR_CONTEXT_SOURCE_INVALID", created.json()["code"])
            self.assertFalse((workspace / "v2/operator/delivery/locks/project.lock").exists())
            self.assertFalse((workspace / "v2/operator/delivery/exports").exists())
            self.assertFalse(any((workspace / "v2/operator/delivery/recovery").iterdir()))


if __name__ == "__main__":
    unittest.main()
