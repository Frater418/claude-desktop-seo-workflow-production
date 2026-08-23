from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from services.operator_api.delivery_persistence import DeliveryExportRepository, DeliveryPersistenceError
from services.operator_api.delivery_persistence_values import (
    DeliveryFailureBoundary,
    DeliveryPersistRequest,
    DeliveryRecoverySidecar,
    canonical_json_bytes,
)
from services.operator_api.recovery_inventory import RecoveryInventory, RecoveryReplayIdentity
from services.operator_api.repository import ProjectRepository, RepositoryError, WorkspaceRegistration, WorkspaceRegistry
from services.owned_file_lock import OwnedFileLock
from tests.support.delivery_api import PROJECT, TENANT
from tests.support.delivery_persistence import ARCHIVE, transaction


class DeliveryPersistenceTests(unittest.TestCase):
    def repository(self, workspace: Path, failure: DeliveryFailureBoundary | None = None) -> DeliveryExportRepository:
        registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))

        def inject(boundary: DeliveryFailureBoundary) -> None:
            if boundary == failure:
                raise OSError(boundary.value)

        return DeliveryExportRepository(ProjectRepository(registry), inject if failure is not None else None)

    def persist(self, repository: DeliveryExportRepository, request: DeliveryPersistRequest):
        with repository.lock(TENANT, PROJECT):
            return repository.persist(request)

    def test_first_write_replay_history_record_and_archive_are_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository = self.repository(workspace)
            request = transaction()
            workflow = workspace / "v2/operator/workflow.json"
            workflow.parent.mkdir(parents=True)
            workflow.write_bytes(b'{"canonical":"workflow"}\n')

            created = self.persist(repository, request)
            replayed = self.persist(repository, request)

            self.assertEqual("created", created.result.replay_state)
            self.assertEqual("replayed", replayed.result.replay_state)
            self.assertEqual((request.result,), repository.list_results(TENANT, PROJECT))
            self.assertEqual(request.package_record, repository.package_record(TENANT, PROJECT, request.result.export_id))
            self.assertEqual(ARCHIVE, repository.archive_bytes(TENANT, PROJECT, request.result.export_id))
            self.assertEqual(b'{"canonical":"workflow"}\n', workflow.read_bytes())
            root = workspace / "v2/operator/delivery/exports" / request.result.export_id
            self.assertEqual({"archive.zip", "delivery-package-record.json", "request.json", "result.json"}, {path.name for path in root.iterdir()})

    def test_changed_key_payload_and_identifier_reuse_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = self.repository(Path(temporary))
            self.persist(repository, transaction())

            with self.assertRaisesRegex(DeliveryPersistenceError, "idempotency"):
                self.persist(repository, transaction(export_id="delivery-export-00000002"))
            with self.assertRaises(DeliveryPersistenceError):
                self.persist(repository, transaction(export_id="delivery-export-00000002", idempotency_key="idem-delivery-00000002"))
            with self.assertRaises(DeliveryPersistenceError):
                self.persist(repository, transaction(export_id="delivery-export-00000002", package_id="delivery-package-00000002", result_id="delivery-export-result-00000001", idempotency_key="idem-delivery-00000003"))

    def test_lock_contention_is_a_stable_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository = self.repository(workspace)
            lock_path = workspace / "v2/operator/delivery/locks/project.lock"
            lock_path.parent.mkdir(parents=True)
            with OwnedFileLock(lock_path, grace_seconds=0), self.assertRaisesRegex(DeliveryPersistenceError, "already in progress"):
                with repository.lock(TENANT, PROJECT):
                    pass

    def test_every_failure_boundary_keeps_recovery_until_matching_repair(self) -> None:
        boundaries = tuple(DeliveryFailureBoundary)
        for boundary in boundaries:
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                request = transaction()
                failing = self.repository(workspace, boundary)
                with self.assertRaises(DeliveryPersistenceError):
                    self.persist(failing, request)
                recovery = workspace / "v2/operator/delivery/recovery"
                self.assertTrue(recovery.is_dir())
                self.assertTrue(any(recovery.iterdir()))
                with self.assertRaises(DeliveryPersistenceError):
                    self.persist(self.repository(workspace), transaction(export_id="delivery-export-00000002"))
                self.assertTrue(any(recovery.iterdir()))
                repaired = self.persist(self.repository(workspace), request)
                self.assertEqual("replayed", repaired.result.replay_state)
                self.assertFalse(any(recovery.iterdir()))

    def test_recovery_blocks_readiness_and_authorizes_only_matching_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            request = transaction()
            failing = self.repository(workspace, DeliveryFailureBoundary.ARCHIVE_WRITTEN)
            with self.assertRaises(DeliveryPersistenceError):
                self.persist(failing, request)
            inventory = RecoveryInventory(WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),)))
            sidecar = inventory.sidecars()[0]
            self.assertTrue(inventory.blocked())
            with self.assertRaises(RepositoryError):
                inventory.authorize(RecoveryReplayIdentity(TENANT, PROJECT, "delivery-recovery", "delivery/recovery/other.json"))
            self.assertEqual(sidecar, inventory.authorize(RecoveryReplayIdentity(TENANT, PROJECT, sidecar.family, sidecar.relative_path)).replay.sidecar())

    def test_corrupt_json_archive_hash_unknown_and_sorted_history_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository = self.repository(workspace)
            later = transaction(export_id="delivery-export-00000002", package_id="delivery-package-00000002", result_id="delivery-export-result-00000002", request_id="delivery-export-request-00000002", idempotency_key="idem-delivery-00000002", created_at="2026-08-22T10:15:31Z")
            earlier = transaction(export_id="delivery-export-00000003", package_id="delivery-package-00000003", result_id="delivery-export-result-00000003", request_id="delivery-export-request-00000003", idempotency_key="idem-delivery-00000003", created_at="2026-08-22T10:15:29Z")
            self.persist(repository, later)
            self.persist(repository, earlier)
            self.assertEqual((earlier.result, later.result), repository.list_results(TENANT, PROJECT))
            with self.assertRaisesRegex(DeliveryPersistenceError, "unavailable"):
                repository.package_record(TENANT, PROJECT, "delivery-export-unknown-0001")
            archive = workspace / "v2/operator/delivery/exports" / earlier.result.export_id / "archive.zip"
            archive.write_bytes(b"corrupt archive")
            with self.assertRaises(DeliveryPersistenceError):
                repository.archive_bytes(TENANT, PROJECT, earlier.result.export_id)
            target = workspace / "v2/operator/delivery/exports" / later.result.export_id / "result.json"
            target.write_text(json.dumps({"bad": "json"}), encoding="utf-8")
            with self.assertRaises(DeliveryPersistenceError):
                repository.package_record(TENANT, PROJECT, later.result.export_id)

    def test_completed_index_binds_exact_canonical_metadata_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            request = transaction()
            self.persist(self.repository(workspace), request)
            index = json.loads(next((workspace / "v2/operator/delivery/idempotency").iterdir()).read_text(encoding="utf-8"))
            material = (
                ("request.json", "request_sha256"),
                ("result.json", "result_sha256"),
                ("delivery-package-record.json", "package_record_sha256"),
            )
            for filename, hash_field in material:
                with self.subTest(material=filename):
                    content = (workspace / "v2/operator/delivery/exports" / request.result.export_id / filename).read_bytes()
                    self.assertTrue(content.endswith(b"\n"))
                    self.assertIn(hash_field, index)
                    self.assertEqual(hashlib.sha256(content).hexdigest(), index[hash_field])
            self.assertIn("archive_sha256", index)
            self.assertIn("archive_size_bytes", index)
            self.assertEqual(hashlib.sha256(request.archive_bytes).hexdigest(), index["archive_sha256"])
            self.assertEqual(len(request.archive_bytes), index["archive_size_bytes"])

    def test_canonical_semantic_tampering_of_each_completed_material_fails_closed(self) -> None:
        mutations = (
            ("request.json", "package_revision", 8),
            ("result.json", "created_at", "2026-08-22T10:15:31Z"),
            ("delivery-package-record.json", "package_revision", 8),
            ("idempotency", "request_sha256", "0" * 64),
        )
        for filename, field, value in mutations:
            with self.subTest(material=filename), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                request = transaction()
                repository = self.repository(workspace)
                self.persist(repository, request)
                path = next((workspace / "v2/operator/delivery/idempotency").iterdir()) if filename == "idempotency" else workspace / "v2/operator/delivery/exports" / request.result.export_id / filename
                content = json.loads(path.read_text(encoding="utf-8"))
                content[field] = value
                path.write_bytes(canonical_json_bytes(content))
                with self.assertRaises(DeliveryPersistenceError):
                    repository.package_record(TENANT, PROJECT, request.result.export_id)

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            request = transaction()
            repository = self.repository(workspace)
            self.persist(repository, request)
            (workspace / "v2/operator/delivery/exports" / request.result.export_id / "archive.zip").write_bytes(b"tampered archive")
            with self.assertRaises(DeliveryPersistenceError):
                repository.package_record(TENANT, PROJECT, request.result.export_id)

    def test_recovery_sidecar_binds_exact_canonical_material_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            request = transaction()
            with self.assertRaises(DeliveryPersistenceError):
                self.persist(self.repository(workspace, DeliveryFailureBoundary.SIDECAR_WRITTEN), request)
            sidecar = json.loads(next((workspace / "v2/operator/delivery/recovery").iterdir()).read_text(encoding="utf-8"))
            material = (
                ("create_request_sha256", canonical_json_bytes(request.create_request.model_dump(mode="json"))),
                ("result_sha256", canonical_json_bytes(request.result.model_dump(mode="json"))),
                ("package_record_sha256", canonical_json_bytes(request.package_record.model_dump(mode="json", exclude_none=True))),
                ("archive_sha256", request.archive_bytes),
            )
            for hash_field, content in material:
                with self.subTest(material=hash_field):
                    self.assertIn(hash_field, sidecar)
                    self.assertEqual(hashlib.sha256(content).hexdigest(), sidecar[hash_field])

    def test_recovery_rejects_tampered_material_and_preserves_conflicts_until_exact_replay(self) -> None:
        mutations = (
            ("create_request", "package_revision", 8),
            ("result", "created_at", "2026-08-22T10:15:31Z"),
            ("package_record", "package_revision", 8),
        )
        for section, field, value in mutations:
            with self.subTest(material=section), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                request = transaction()
                with self.assertRaises(DeliveryPersistenceError):
                    self.persist(self.repository(workspace, DeliveryFailureBoundary.SIDECAR_WRITTEN), request)
                sidecar = next((workspace / "v2/operator/delivery/recovery").iterdir())
                content = json.loads(sidecar.read_text(encoding="utf-8"))
                content[section][field] = value
                sidecar.write_bytes(canonical_json_bytes(content))
                with self.assertRaises(DeliveryPersistenceError) as raised:
                    self.persist(self.repository(workspace), request)
                self.assertEqual("ERROR_DELIVERY_PERSISTENCE", raised.exception.code)

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            request = transaction()
            with self.assertRaises(DeliveryPersistenceError):
                self.persist(self.repository(workspace, DeliveryFailureBoundary.ARCHIVE_WRITTEN), request)
            sidecar = next((workspace / "v2/operator/delivery/recovery").iterdir())
            original = sidecar.read_bytes()
            with self.assertRaises(DeliveryPersistenceError):
                self.persist(self.repository(workspace), transaction(export_id="delivery-export-00000002"))
            self.assertEqual(original, sidecar.read_bytes())
            self.assertEqual("replayed", self.persist(self.repository(workspace), request).result.replay_state)
            self.assertFalse(sidecar.exists())


if __name__ == "__main__":
    unittest.main()
