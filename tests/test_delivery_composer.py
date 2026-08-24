from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from jsonschema import Draft202012Validator, FormatChecker

from services.delivery.archive_validation import validate_archive
from services.operator_api.delivery_composer import DeliveryCompositionError, compose_delivery, preview_delivery
from services.operator_api.delivery_models import DeliveryCreateRequest
from services.operator_api.delivery_repository import DeliverySnapshotRepository
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry
from tests.support.delivery_api import PROJECT, TENANT, delivery_request, seed_workspace, workspace_snapshot


ROOT = Path(__file__).resolve().parents[1]


class DeliveryComposerTests(unittest.TestCase):
    def snapshot(self, workspace: Path):
        registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
        return DeliverySnapshotRepository(registry).snapshot(TENANT, PROJECT)

    def request(self, **changes: str) -> DeliveryCreateRequest:
        payload = delivery_request(**changes)
        return DeliveryCreateRequest.model_validate(payload)

    def test_preview_reports_checkpoint_and_final_policy_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace, incomplete_final=True)
            before = workspace_snapshot(workspace, include_delivery=True)

            checkpoint = preview_delivery(self.snapshot(workspace), self.request())
            final = preview_delivery(self.snapshot(workspace), self.request(scope="final"))

            self.assertTrue(checkpoint.policy_eligible)
            self.assertFalse(final.policy_eligible)
            self.assertIn("developer-handoff", final.missing_deliverable_ids)
            self.assertEqual(before, workspace_snapshot(workspace, include_delivery=True))

    def test_composition_preserves_identity_and_is_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            snapshot = self.snapshot(workspace)
            request = self.request()
            before = workspace_snapshot(workspace, include_delivery=True)

            first = compose_delivery(snapshot, request)
            second = compose_delivery(snapshot, request)

            self.assertEqual(first.archive.zip_bytes, second.archive.zip_bytes)
            self.assertEqual(request.export_id, first.result.export_id)
            self.assertEqual(request.delivery_package_id, first.package_record.delivery_package_id)
            self.assertEqual(request.delivery_export_result_id, first.result.delivery_export_result_id)
            self.assertEqual(request.export_request.created_at, first.result.created_at)
            self.assertEqual(hashlib.sha256(first.archive.zip_bytes).hexdigest(), first.result.zip_sha256)
            self.assertEqual(first.archive.package_sha256, validate_archive(first.archive.zip_bytes).package_sha256)
            self.assertEqual(before, workspace_snapshot(workspace, include_delivery=True))
            with zipfile.ZipFile(io.BytesIO(first.archive.zip_bytes)) as archive:
                package_bytes = b"\n".join(archive.read(name) for name in archive.namelist())
            self.assertTrue(all(token not in package_bytes for token in (b"/home/", b"C:\\Users\\", b"api_key", b"task_completion_callback")))

    def test_composition_validates_task_one_contracts_and_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            composition = compose_delivery(self.snapshot(workspace), self.request())
            validators = {
                name: Draft202012Validator(
                    json.loads((ROOT / "standards" / "delivery" / f"{name}.schema.json").read_text(encoding="utf-8")),
                    format_checker=FormatChecker(),
                )
                for name in ("delivery-export-request", "delivery-export-result", "delivery-package-record")
            }

            self.assertEqual((), tuple(validators["delivery-export-request"].iter_errors(composition.request.export_request.model_dump(mode="json", exclude_none=True))))
            self.assertEqual((), tuple(validators["delivery-export-result"].iter_errors(composition.result.model_dump(mode="json", exclude_none=True))))
            self.assertEqual((), tuple(validators["delivery-package-record"].iter_errors(composition.package_record.model_dump(mode="json", exclude_none=True))))
            self.assertEqual(composition.archive.package_sha256, validate_archive(composition.archive.zip_bytes).package_sha256)

    def test_caller_snapshot_revision_binds_every_generated_delivery_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            project_path = workspace / "v2/operator/project-v2.json"
            project = json.loads(project_path.read_text(encoding="utf-8"))
            project["revision"] = 99
            project_path.write_text(json.dumps(project), encoding="utf-8")
            payload = delivery_request()
            payload["export_request"]["source_snapshot_revision"] = 23

            composition = compose_delivery(self.snapshot(workspace), DeliveryCreateRequest.model_validate(payload))

            with zipfile.ZipFile(io.BytesIO(composition.archive.zip_bytes)) as archive:
                names = archive.namelist()
                project_summary = json.loads(archive.read(next(name for name in names if name.endswith("project-summary.json"))))
                role_manifests = tuple(json.loads(archive.read(name)) for name in names if name.endswith("role-handoff-manifest.json"))
                notion_manifest = json.loads(archive.read(next(name for name in names if name.endswith("notion-import-manifest.json"))))
            self.assertEqual(23, project_summary["source_snapshot_revision"])
            self.assertEqual(23, composition.package_record.source_snapshot_revision)
            self.assertEqual(23, composition.result.source_snapshot_revision)
            self.assertEqual({23}, {manifest["source_snapshot_revision"] for manifest in role_manifests})
            self.assertEqual(23, notion_manifest["source_snapshot_revision"])

    def test_checkpoint_package_omits_final_only_fields_for_schema_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)

            package = compose_delivery(self.snapshot(workspace), self.request()).package_record.model_dump(mode="json", exclude_none=True)

            self.assertEqual("checkpoint", package["scope"])
            self.assertTrue({"task_assignment_manifest_path", "quality_summary", "export_manifest_path", "checksums_path"}.isdisjoint(package))

    def test_unsupported_role_fails_before_package_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            request = self.request()
            unsupported = request.model_copy(
                update={
                    "role_package_requests": (
                        request.role_package_requests[0].model_copy(update={"role": "admin"}),
                        request.role_package_requests[1],
                    )
                }
            )

            with self.assertRaises(DeliveryCompositionError) as error:
                compose_delivery(self.snapshot(workspace), unsupported)

            self.assertEqual("ROLE_UNSUPPORTED", error.exception.code)


if __name__ == "__main__":
    unittest.main()
