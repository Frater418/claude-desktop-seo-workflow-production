from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.operator_api.app import AppConfig, create_app
from services.operator_api.delivery_composer import compose_delivery
from services.operator_api.delivery_models import DeliveryCreateRequest
from services.operator_api.delivery_persistence import DeliveryExportRepository, DeliveryPersistenceError
from services.operator_api.delivery_persistence_values import DeliveryFailureBoundary, DeliveryPersistRequest
from services.operator_api.delivery_repository import DeliverySnapshotRepository
from services.operator_api.recovery_inventory import RecoveryInventory
from services.operator_api.repository import ProjectRepository, WorkspaceRegistration, WorkspaceRegistry
from services.owned_file_lock import OwnedFileLock
from tests.support.delivery_api import (
    PROJECT,
    TENANT,
    changed_request,
    delivery_base,
    delivery_request,
    seed_workspace,
)


ROOT = Path(__file__).resolve().parents[1]


class RaisingClock:
    def now(self) -> str:
        raise AssertionError("Delivery endpoints must preserve caller-supplied timestamps without reading the server clock.")


class DeliveryApiRecoveryTests(unittest.TestCase):
    def client(self, workspace: Path) -> TestClient:
        registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
        return TestClient(create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock())))

    def route(self, suffix: str = "") -> str:
        return f"{delivery_base()}{suffix}"

    def test_interrupted_delivery_is_unready_conflict_cannot_consume_recovery_and_matching_replay_repairs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)
            first = delivery_request()
            self.assertEqual(201, client.post(self.route("/exports"), json=first).status_code)

            from services.operator_api.delivery_persistence import _atomic_write_once

            interrupted = delivery_request(
                idempotency_key="idem-delivery-00000002",
                export_id="delivery-export-00000002",
                delivery_package_id="delivery-package-00000002",
                delivery_export_result_id="delivery-export-result-00000002",
                delivery_export_request_id="delivery-export-request-00000002",
            )
            interrupted["role_package_requests"][0]["role_handoff_manifest_id"] = "role-handoff-copywriter-00000002"
            interrupted["role_package_requests"][1]["role_handoff_manifest_id"] = "role-handoff-developer-00000002"
            interrupted["notion_import_request"]["notion_import_manifest_id"] = "notion-import-00000002"
            original_write = _atomic_write_once

            def fail_after_recovery(path: Path, content: bytes) -> None:
                if path.name == "archive.zip":
                    raise OSError("injected archive interruption")
                original_write(path, content)

            with patch("services.operator_api.delivery_persistence._atomic_write_once", side_effect=fail_after_recovery):
                failed = client.post(self.route("/exports"), json=interrupted)

            self.assertEqual(503, failed.status_code)
            recovery_root = workspace / "v2/operator/delivery/recovery"
            self.assertTrue(any(recovery_root.iterdir()))
            self.assertEqual(503, client.get("/readyz").status_code)
            conflicting = changed_request(interrupted)
            conflicting["export_request"]["scope"] = "final"
            conflict = client.post(self.route("/exports"), json=conflicting)
            self.assertEqual(409, conflict.status_code)
            self.assertTrue(any(recovery_root.iterdir()))

            repaired = client.post(self.route("/exports"), json=interrupted)

            self.assertEqual(200, repaired.status_code)
            self.assertEqual("replayed", repaired.json()["replay_state"])
            self.assertFalse(any(recovery_root.iterdir()))
            self.assertEqual(200, client.get("/readyz").status_code)

    def test_active_delivery_lock_returns_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            lock_path = workspace / "v2/operator/delivery/locks/project.lock"
            lock_path.parent.mkdir(parents=True)

            with OwnedFileLock(lock_path, grace_seconds=0):
                response = self.client(workspace).post(self.route("/exports"), json=delivery_request())

            self.assertEqual(409, response.status_code)
            self.assertEqual("ERR_CONCURRENT_DELIVERY_CONFLICT", response.json()["code"])

    def test_same_workspace_projection_recovery_blocks_create_before_delivery_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            recovery = workspace / "v2/operator/projection-recovery/project-demo.json"
            recovery.parent.mkdir()
            recovery.write_text("{}", encoding="utf-8")

            with patch("services.operator_api.delivery_persistence.OwnedFileLock") as lock:
                response = self.client(workspace).post(self.route("/exports"), json=delivery_request())

            self.assertEqual(503, response.status_code)
            self.assertEqual("ERROR_CONTEXT_SOURCE_INVALID", response.json()["code"])
            lock.assert_not_called()
            self.assertFalse((workspace / "v2/operator/delivery").exists())

    def test_registered_other_workspace_recovery_blocks_delivery_create_globally(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace-current"
            other_workspace = root / "workspace-other"
            seed_workspace(workspace)
            recovery = other_workspace / "v2/operator/runtime-recovery/run-other-0001.json"
            recovery.parent.mkdir(parents=True)
            recovery.write_text("{}", encoding="utf-8")
            registry = WorkspaceRegistry(
                (
                    WorkspaceRegistration(TENANT, PROJECT, workspace),
                    WorkspaceRegistration("tenant-other", "project-other", other_workspace),
                )
            )
            client = TestClient(create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock())))

            response = client.post(self.route("/exports"), json=delivery_request())

            self.assertEqual(503, response.status_code)
            self.assertEqual("ERROR_CONTEXT_SOURCE_INVALID", response.json()["code"])
            self.assertFalse((workspace / "v2/operator/delivery").exists())

    def test_completed_index_with_pending_sidecar_is_repaired_before_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
            request = DeliveryCreateRequest.model_validate(delivery_request())
            composition = compose_delivery(DeliverySnapshotRepository(registry).snapshot(TENANT, PROJECT), request)
            persisted = DeliveryPersistRequest(
                tenant_id=TENANT,
                project_id=PROJECT,
                create_request=request,
                result=composition.result,
                package_record=composition.package_record,
                archive_bytes=composition.archive.zip_bytes,
            )

            def fail_before_removal(boundary: DeliveryFailureBoundary) -> None:
                if boundary is DeliveryFailureBoundary.BEFORE_SIDECAR_REMOVAL:
                    raise OSError(boundary.value)

            repository = DeliveryExportRepository(ProjectRepository(registry), fail_before_removal)
            with repository.lock(TENANT, PROJECT), self.assertRaises(DeliveryPersistenceError):
                repository.persist(persisted)
            recovery = workspace / "v2/operator/delivery/recovery"
            exports = workspace / "v2/operator/delivery/exports" / request.export_id
            before = {path.name: path.read_bytes() for path in exports.iterdir()}
            self.assertTrue(any(recovery.iterdir()))
            self.assertEqual(1, len(tuple((workspace / "v2/operator/delivery/idempotency").iterdir())))
            restarted = TestClient(create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock())))
            self.assertEqual(503, restarted.get("/readyz").status_code)

            replay = restarted.post(self.route("/exports"), json=delivery_request())

            self.assertEqual(200, replay.status_code)
            self.assertEqual("replayed", replay.json()["replay_state"])
            self.assertFalse(any(recovery.iterdir()))
            self.assertEqual(1, len(restarted.get(self.route("/exports")).json()["data"]))
            self.assertEqual(1, len(tuple((workspace / "v2/operator/delivery/idempotency").iterdir())))
            self.assertEqual(200, restarted.get("/readyz").status_code)
            self.assertEqual(before, {path.name: path.read_bytes() for path in exports.iterdir()})

    def test_delivery_admission_is_global_across_registered_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_workspace, second_workspace = root / "first", root / "second"
            seed_workspace(first_workspace)
            seed_workspace(second_workspace)
            second_tenant, second_project = "tenant-other", "project-other"
            for path in second_workspace.rglob("*"):
                if path.is_file():
                    path.write_bytes(path.read_bytes().replace(TENANT.encode(), second_tenant.encode()).replace(PROJECT.encode(), second_project.encode()))
            registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, first_workspace), WorkspaceRegistration(second_tenant, second_project, second_workspace)))
            app = create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock()))
            first_entered, second_entered, release = threading.Event(), threading.Event(), threading.Event()
            original_authorize = RecoveryInventory.authorize

            def authorize(inventory: RecoveryInventory, replay=None):
                if replay is not None and replay.project_id == PROJECT:
                    first_entered.set()
                    release.wait(timeout=2)
                elif replay is not None:
                    second_entered.set()
                return original_authorize(inventory, replay)

            statuses: list[int] = []
            first = threading.Thread(target=lambda: statuses.append(TestClient(app).post(self.route("/exports"), json=delivery_request()).status_code))
            second_payload = json.loads(json.dumps(delivery_request()).replace(TENANT, second_tenant).replace(PROJECT, second_project))
            second_route = f"/v1/tenants/{second_tenant}/projects/{second_project}/delivery/exports"
            second = threading.Thread(target=lambda: statuses.append(TestClient(app).post(second_route, json=second_payload).status_code))
            with patch.object(RecoveryInventory, "authorize", new=authorize):
                first.start()
                self.assertTrue(first_entered.wait(timeout=2))
                second.start()
                try:
                    self.assertFalse(second_entered.wait(timeout=1))
                finally:
                    release.set()
                    first.join(timeout=2)
                    second.join(timeout=2)

            self.assertEqual([201, 201], sorted(statuses))

    def test_second_project_observes_recovery_left_by_first_project_before_creating_a_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_workspace, second_workspace = root / "first", root / "second"
            seed_workspace(first_workspace)
            seed_workspace(second_workspace)
            second_tenant, second_project = "tenant-other", "project-other"
            for path in second_workspace.rglob("*"):
                if path.is_file():
                    path.write_bytes(path.read_bytes().replace(TENANT.encode(), second_tenant.encode()).replace(PROJECT.encode(), second_project.encode()))
            registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, first_workspace), WorkspaceRegistration(second_tenant, second_project, second_workspace)))
            app = create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock()))
            first_entered, second_entered, release_first, release_second, sidecar_written = (threading.Event() for _ in range(5))
            original_authorize = RecoveryInventory.authorize

            def authorize(inventory: RecoveryInventory, replay=None):
                if replay is not None and replay.project_id == PROJECT:
                    first_entered.set()
                    release_first.wait(timeout=2)
                elif replay is not None:
                    second_entered.set()
                    release_second.wait(timeout=2)
                return original_authorize(inventory, replay)

            def interrupt_after_sidecar(_: DeliveryExportRepository, boundary: DeliveryFailureBoundary) -> None:
                if boundary is DeliveryFailureBoundary.SIDECAR_WRITTEN:
                    sidecar_written.set()
                    raise DeliveryPersistenceError("ERROR_DELIVERY_PERSISTENCE", "injected sidecar interruption")

            statuses: list[int] = []
            first = threading.Thread(target=lambda: statuses.append(TestClient(app, raise_server_exceptions=False).post(self.route("/exports"), json=delivery_request()).status_code))
            second_payload = json.loads(json.dumps(delivery_request()).replace(TENANT, second_tenant).replace(PROJECT, second_project))
            second_route = f"/v1/tenants/{second_tenant}/projects/{second_project}/delivery/exports"
            second = threading.Thread(target=lambda: statuses.append(TestClient(app, raise_server_exceptions=False).post(second_route, json=second_payload).status_code))
            with patch.object(RecoveryInventory, "authorize", new=authorize), patch.object(DeliveryExportRepository, "_inject", new=interrupt_after_sidecar):
                first.start()
                self.assertTrue(first_entered.wait(timeout=2))
                second.start()
                try:
                    self.assertFalse(second_entered.wait(timeout=1))
                finally:
                    release_first.set()
                    self.assertTrue(sidecar_written.wait(timeout=2))
                    release_second.set()
                    first.join(timeout=2)
                    second.join(timeout=2)

            self.assertEqual([503, 503], sorted(statuses))
            self.assertFalse((second_workspace / "v2/operator/delivery/recovery").exists())

    def test_final_policy_rejection_occurs_before_recovery_admission(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace, incomplete_final=True)
            registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
            client = TestClient(create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock())), raise_server_exceptions=False)

            with patch.object(RecoveryInventory, "authorize", side_effect=AssertionError("policy rejection entered delivery admission")):
                response = client.post(self.route("/exports"), json=delivery_request(scope="final"))

            self.assertEqual(409, response.status_code)
            self.assertEqual("DELIVERY_FINAL_POLICY_REJECTED", response.json()["code"])
            self.assertFalse((workspace / "v2/operator/delivery").exists())


if __name__ == "__main__":
    unittest.main()
