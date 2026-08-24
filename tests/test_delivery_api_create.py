from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.delivery.record_normalization import DeliveryInventoryError
from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry
from tests.support.delivery_api import (
    CREATED_AT,
    PROJECT,
    TENANT,
    changed_request,
    delivery_base,
    delivery_request,
    seed_workspace,
    write_projection,
    workspace_snapshot,
)


ROOT = Path(__file__).resolve().parents[1]


class RaisingClock:
    def now(self) -> str:
        raise AssertionError("Delivery endpoints must preserve caller-supplied timestamps without reading the server clock.")


class DeliveryApiCreateTests(unittest.TestCase):
    def client(self, workspace: Path) -> TestClient:
        registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
        return TestClient(create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock())))

    def route(self, suffix: str = "") -> str:
        return f"{delivery_base()}{suffix}"

    def test_create_returns_created_export_with_exact_caller_identity_and_no_clock_access(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            payload = delivery_request()

            response = self.client(workspace).post(self.route("/exports"), json=payload)

            self.assertEqual(201, response.status_code)
            result = response.json()
            self.assertEqual("created", result["replay_state"])
            self.assertEqual(payload["export_id"], result["export_id"])
            self.assertEqual(payload["delivery_package_id"], result["delivery_package_id"])
            self.assertEqual(payload["delivery_export_result_id"], result["delivery_export_result_id"])
            self.assertEqual(payload["export_request"]["delivery_export_request_id"], result["delivery_export_request_id"])
            self.assertEqual(CREATED_AT, result["created_at"])

    def test_identical_create_replay_returns_the_immutable_export_with_replayed_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)
            payload = delivery_request()

            created = client.post(self.route("/exports"), json=payload)
            replayed = client.post(self.route("/exports"), json=payload)

            self.assertEqual(201, created.status_code)
            self.assertEqual(200, replayed.status_code)
            expected = dict(created.json(), replay_state="replayed")
            self.assertEqual(expected, replayed.json())

    def test_same_idempotency_key_rejects_changed_scope_ids_timestamp_roles_and_notion_input(self) -> None:
        cases = (
            ("scope", lambda payload: payload["export_request"].update(scope="final")),
            ("export-id", lambda payload: payload.update(export_id="delivery-export-00000002")),
            ("package-id", lambda payload: payload.update(delivery_package_id="delivery-package-00000002")),
            ("result-id", lambda payload: payload.update(delivery_export_result_id="delivery-export-result-00000002")),
            ("timestamp", lambda payload: payload["export_request"].update(created_at="2026-08-22T10:15:31Z")),
            ("roles", lambda payload: payload.update(role_package_requests=[{"role": "copywriter", "role_handoff_manifest_id": "role-handoff-copywriter-00000002"}, {"role": "developer", "role_handoff_manifest_id": "role-handoff-developer-00000001"}])),
            ("notion", lambda payload: payload["notion_import_request"]["implementation_tasks"][0].update(title="Publish a changed delivery package")),
        )
        for name, mutate in cases:
            with self.subTest(change=name), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                seed_workspace(workspace)
                client = self.client(workspace)
                payload = delivery_request()
                conflicting = changed_request(payload)
                mutate(conflicting)

                self.assertEqual(201, client.post(self.route("/exports"), json=payload).status_code)
                response = client.post(self.route("/exports"), json=conflicting)

                self.assertEqual(409, response.status_code)
                self.assertEqual("ERR_IDEMPOTENCY_CONFLICT", response.json()["code"])

    def test_final_policy_rejection_happens_before_any_delivery_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace, incomplete_final=True)
            before = workspace_snapshot(workspace, include_delivery=True)

            response = self.client(workspace).post(self.route("/exports"), json=delivery_request(scope="final"))

            self.assertEqual(409, response.status_code)
            self.assertEqual("DELIVERY_FINAL_POLICY_REJECTED", response.json()["code"])
            self.assertEqual(before, workspace_snapshot(workspace, include_delivery=True))

    def test_final_policy_rejection_creates_no_delivery_directory_or_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace, incomplete_final=True)

            with patch("services.operator_api.delivery_persistence.OwnedFileLock") as lock:
                response = self.client(workspace).post(self.route("/exports"), json=delivery_request(scope="final"))

            self.assertEqual(409, response.status_code)
            self.assertEqual("DELIVERY_FINAL_POLICY_REJECTED", response.json()["code"])
            lock.assert_not_called()
            self.assertFalse((workspace / "v2/operator/delivery").exists())

    def test_provisioned_workspace_preview_and_create_use_effective_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            provisioning_root = Path(temporary) / "provisioned"
            workspace = provisioning_root / TENANT / PROJECT
            seed_workspace(workspace)
            project = workspace / "v2/operator/project.json"
            project.write_text(f"{project.read_text(encoding='utf-8')}\n", encoding="utf-8")
            client = TestClient(
                create_app(
                    registry=WorkspaceRegistry(()),
                    repository_root=ROOT,
                    config=AppConfig(ROOT, provisioning_root=provisioning_root, provisioning_enabled=True, clock=RaisingClock()),
                )
            )

            preview = client.get(self.route("/preview"), params={"scope": "checkpoint"})
            created = client.post(self.route("/exports"), json=delivery_request())

            self.assertEqual(200, preview.status_code)
            self.assertEqual(201, created.status_code)
            self.assertTrue((workspace / "v2/operator/delivery").is_dir())

    def test_create_changes_only_the_delivery_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            before = workspace_snapshot(workspace)

            response = self.client(workspace).post(self.route("/exports"), json=delivery_request())

            self.assertEqual(201, response.status_code)
            self.assertEqual(before, workspace_snapshot(workspace))
            self.assertTrue((workspace / "v2/operator/delivery").is_dir())

    def test_checkpoint_create_returns_originating_422_for_an_uncomposable_role(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
            client = TestClient(create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock())), raise_server_exceptions=False)

            with patch("services.operator_api.delivery_composer.build_role_package", side_effect=DeliveryInventoryError("ROLE_PACKAGE_EMPTY", "role composition failed")):
                response = client.post(self.route("/exports"), json=delivery_request())

            self.assertEqual(422, response.status_code)
            self.assertEqual("ROLE_PACKAGE_EMPTY", response.json()["code"])

    def test_checkpoint_create_returns_originating_422_for_an_uncomposable_notion_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            payload = changed_request(delivery_request())
            payload["notion_import_request"]["implementation_tasks"][0]["dependencies"] = ["task-implementation-00000002"]
            registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
            client = TestClient(create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock())), raise_server_exceptions=False)

            response = client.post(self.route("/exports"), json=payload)

            self.assertEqual(422, response.status_code)
            self.assertEqual("NOTION_RELATION_DANGLING", response.json()["code"])

    def test_api_validation_rejects_malformed_input_and_route_body_identity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)
            valid = delivery_request()
            malformed = (
                ("id", lambda payload: payload["export_request"].update(delivery_export_request_id="bad")),
                ("naive-time", lambda payload: payload["export_request"].update(created_at="2026-08-22T10:15:30")),
                ("extra", lambda payload: payload.update(unexpected="value")),
                ("duplicate-roles", lambda payload: payload["export_request"].update(requested_role_packages=["copywriter", "copywriter"])),
            )
            for name, mutate in malformed:
                with self.subTest(malformed=name):
                    payload = changed_request(valid)
                    mutate(payload)
                    response = client.post(self.route("/exports"), json=payload)
                    self.assertEqual(422, response.status_code)

            mismatch = changed_request(valid)
            mismatch["export_request"]["tenant_id"] = "tenant-other"
            response = client.post(self.route("/exports"), json=mismatch)
            self.assertEqual(409, response.status_code)
            self.assertEqual("ERR_DELIVERY_IDENTITY_CONFLICT", response.json()["code"])

    def test_duplicate_role_manifest_ids_return_stable_validation_error_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            payload = delivery_request()
            payload["role_package_requests"][1]["role_handoff_manifest_id"] = payload["role_package_requests"][0]["role_handoff_manifest_id"]
            before = workspace_snapshot(workspace, include_delivery=True)
            registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
            client = TestClient(create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock())), raise_server_exceptions=False)

            response = client.post(self.route("/exports"), json=payload)

            self.assertEqual(422, response.status_code)
            self.assertEqual({"code": "ERROR_DELIVERY_REQUEST_INVALID", "message": "Delivery request validation failed."}, response.json())
            self.assertFalse((workspace / "v2/operator/delivery").exists())
            self.assertEqual(before, workspace_snapshot(workspace, include_delivery=True))

    def test_delivery_request_validation_uses_the_advertised_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)
            expected = {"code": "ERROR_DELIVERY_REQUEST_INVALID", "message": "Delivery request validation failed."}
            responses = (
                client.post(self.route("/exports"), json={}),
                client.get(self.route("/preview"), params={"scope": "invalid"}),
                client.get(self.route("/exports/bad")),
            )

            for response in responses:
                with self.subTest(path=response.request.url.path):
                    self.assertEqual(422, response.status_code)
                    self.assertEqual(expected, response.json())

    def test_non_delivery_validation_retains_fastapi_detail_body(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)

            response = self.client(workspace).post(f"/v1/tenants/{TENANT}/projects/{PROJECT}/commands/start", json={})

            self.assertEqual(422, response.status_code)
            self.assertIsInstance(response.json()["detail"], list)

    def test_released_artifact_host_path_returns_archive_error_without_delivery_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            artifact_id = "artifact-strategy-0001"
            content = b"source_path=C:\\Users\\Alice\\delivery.md\n"
            content_sha256 = hashlib.sha256(content).hexdigest()
            (workspace / "v2/operator/artifact-content" / f"{artifact_id}.md").write_bytes(content)
            for relative in ("artifacts.json", "gates.json", "releases.json", "releases/release-artifact-strategy-0001.json"):
                value = json.loads((workspace / "v2/operator" / relative).read_text(encoding="utf-8"))
                records = value if isinstance(value, list) else [value]
                for record in records:
                    if record.get("artifact_id") == artifact_id:
                        for field in ("content_sha256", "artifact_sha256"):
                            if field in record:
                                record[field] = content_sha256
                write_projection(workspace, relative, value)
            before = workspace_snapshot(workspace, include_delivery=True)

            response = self.client(workspace).post(self.route("/exports"), json=delivery_request())

            self.assertEqual(422, response.status_code)
            self.assertEqual("DELIVERY_ARCHIVE_PUBLIC_HOST_PATH", response.json()["code"])
            self.assertFalse((workspace / "v2/operator/delivery").exists())
            self.assertEqual(before, workspace_snapshot(workspace, include_delivery=True))


if __name__ == "__main__":
    unittest.main()
