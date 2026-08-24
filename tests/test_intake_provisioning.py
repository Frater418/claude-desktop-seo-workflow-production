from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistry


ROOT = Path(__file__).resolve().parents[1]
TENANT = "tenant-invalid-intake"


class IntakeProvisioningTests(unittest.TestCase):
    def test_invalid_intake_acceptance_fails_before_provisioning_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            provisioning_root = Path(temporary) / "provisioned"
            app = create_app(
                WorkspaceRegistry(()),
                ROOT,
                AppConfig(
                    repository_root=ROOT,
                    provisioning_root=provisioning_root,
                    provisioning_enabled=True,
                ),
            )
            client = TestClient(app)
            preview = client.post(
                f"/v1/tenants/{TENANT}/intake/preview",
                json={"markdown": "# Incomplete intake"},
            )
            reviewed = preview.json()["data"]

            response = client.post(
                f"/v1/tenants/{TENANT}/intake/accept",
                json={
                    "markdown": "# Incomplete intake",
                    "source_sha256": reviewed["source_sha256"],
                    "reviewed": reviewed["reviewed"],
                    "preview_hash": reviewed["preview_hash"],
                    "confirmed": True,
                },
            )

            self.assertEqual(200, preview.status_code)
            self.assertFalse(reviewed["eligible"])
            self.assertEqual(422, response.status_code)
            self.assertEqual("ERROR_CONTEXT_SCHEMA_INVALID", response.json()["code"])
            self.assertFalse(provisioning_root.exists())


if __name__ == "__main__":
    unittest.main()
