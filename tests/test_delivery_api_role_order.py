from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry
from tests.support.delivery_api import PROJECT, TENANT, delivery_base, delivery_request, seed_workspace


ROOT = Path(__file__).resolve().parents[1]
_ROLE_ORDER = ("copywriter", "developer")
_MANIFEST_ORDER = tuple(f"role-handoff-{role}-00000001" for role in _ROLE_ORDER)


class RaisingClock:
    def now(self) -> str:
        raise AssertionError("Delivery endpoints must preserve caller-supplied timestamps without reading the server clock.")


class DeliveryApiRoleOrderTests(unittest.TestCase):
    def client(self, workspace: Path) -> TestClient:
        registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
        return TestClient(create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock())))

    @staticmethod
    def route(suffix: str = "") -> str:
        return f"{delivery_base()}{suffix}"

    def test_reversed_role_requests_are_canonical_and_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            payload = delivery_request(roles=tuple(reversed(_ROLE_ORDER)))
            client = self.client(workspace)

            created = client.post(self.route("/exports"), json=payload)

            self.assertEqual(201, created.status_code)
            export_id = payload["export_id"]
            self.assertEqual(200, client.get(self.route("/exports")).status_code)
            self.assertEqual(200, client.get(self.route(f"/exports/{export_id}")).status_code)
            self.assertEqual(200, client.get(self.route(f"/exports/{export_id}/download")).status_code)
            export_root = workspace / "v2/operator/delivery/exports" / str(export_id)
            request = json.loads((export_root / "request.json").read_text(encoding="utf-8"))
            result = json.loads((export_root / "result.json").read_text(encoding="utf-8"))
            package = json.loads((export_root / "delivery-package-record.json").read_text(encoding="utf-8"))
            index = json.loads(next((workspace / "v2/operator/delivery/idempotency").iterdir()).read_text(encoding="utf-8"))
            self.assertEqual(list(_ROLE_ORDER), request["export_request"]["requested_role_packages"])
            self.assertEqual(list(_ROLE_ORDER), [item["role"] for item in request["role_package_requests"]])
            self.assertEqual(list(_MANIFEST_ORDER), [item["manifest_id"] for item in result["role_handoff_manifests"]])
            self.assertEqual(list(_ROLE_ORDER), [item["role"] for item in package["role_packages"]])
            self.assertEqual(list(_MANIFEST_ORDER), index["role_handoff_manifest_ids"])

    def test_role_order_permutations_are_identical_replays(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)
            reversed_payload = delivery_request(roles=tuple(reversed(_ROLE_ORDER)))
            canonical_payload = delivery_request(roles=_ROLE_ORDER)

            created = client.post(self.route("/exports"), json=reversed_payload)
            replayed = client.post(self.route("/exports"), json=canonical_payload)

            self.assertEqual(201, created.status_code)
            self.assertEqual(200, replayed.status_code)
            self.assertEqual("replayed", replayed.json()["replay_state"])
            self.assertEqual(1, len(client.get(self.route("/exports")).json()["data"]))
            export_root = workspace / "v2/operator/delivery/exports" / str(reversed_payload["export_id"])
            self.assertEqual(1, len(tuple((workspace / "v2/operator/delivery/idempotency").iterdir())))
            self.assertTrue((export_root / "archive.zip").is_file())


if __name__ == "__main__":
    unittest.main()
