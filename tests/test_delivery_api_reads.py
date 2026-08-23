from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from fastapi.testclient import TestClient

from services.operator_api.app import AppConfig, create_app
from services.operator_api.delivery_persistence_values import DeliveryFailureBoundary
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry
from tests.support.delivery_api import (
    PROJECT,
    TENANT,
    delivery_base,
    delivery_request,
    seed_workspace,
    workspace_snapshot,
)
from tests.support.delivery_persistence import transaction, write_incomplete_delivery


ROOT = Path(__file__).resolve().parents[1]


class RaisingClock:
    def now(self) -> str:
        raise AssertionError("Delivery endpoints must preserve caller-supplied timestamps without reading the server clock.")


class DeliveryApiReadsTests(unittest.TestCase):
    def client(self, workspace: Path) -> TestClient:
        registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
        return TestClient(create_app(registry=registry, repository_root=ROOT, config=AppConfig(ROOT, clock=RaisingClock())))

    def route(self, suffix: str = "") -> str:
        return f"{delivery_base()}{suffix}"

    def test_history_is_empty_then_sorted_by_created_at_and_export_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)

            empty = client.get(self.route("/exports"))
            self.assertEqual(200, empty.status_code)
            self.assertEqual([], empty.json()["data"])

            later = delivery_request(
                idempotency_key="idem-delivery-00000002",
                created_at="2026-08-22T10:15:31Z",
                export_id="delivery-export-00000002",
                delivery_package_id="delivery-package-00000002",
                delivery_export_result_id="delivery-export-result-00000002",
                delivery_export_request_id="delivery-export-request-00000002",
            )
            earlier = delivery_request(
                idempotency_key="idem-delivery-00000003",
                created_at="2026-08-22T10:15:29Z",
                export_id="delivery-export-00000003",
                delivery_package_id="delivery-package-00000003",
                delivery_export_result_id="delivery-export-result-00000003",
                delivery_export_request_id="delivery-export-request-00000003",
            )
            for payload, sequence in ((later, "00000002"), (earlier, "00000003")):
                payload["role_package_requests"][0]["role_handoff_manifest_id"] = f"role-handoff-copywriter-{sequence}"
                payload["role_package_requests"][1]["role_handoff_manifest_id"] = f"role-handoff-developer-{sequence}"
                payload["notion_import_request"]["notion_import_manifest_id"] = f"notion-import-{sequence}"
            self.assertEqual(201, client.post(self.route("/exports"), json=later).status_code)
            self.assertEqual(201, client.post(self.route("/exports"), json=earlier).status_code)

            history = client.get(self.route("/exports"))

            self.assertEqual(200, history.status_code)
            self.assertEqual(
                ["delivery-export-00000003", "delivery-export-00000002"],
                [result["export_id"] for result in history.json()["data"]],
            )

    def test_package_record_and_download_expose_exact_persisted_archive_with_controlled_headers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)
            payload = delivery_request()

            created = client.post(self.route("/exports"), json=payload)
            self.assertEqual(201, created.status_code)
            record = client.get(self.route(f"/exports/{payload['export_id']}"))
            download = client.get(self.route(f"/exports/{payload['export_id']}/download"))

            self.assertEqual(200, record.status_code)
            self.assertEqual(payload["delivery_package_id"], record.json()["delivery_package_id"])
            self.assertEqual(payload["export_id"], record.json()["export_id"])
            self.assertTrue({"task_assignment_manifest_path", "quality_summary", "export_manifest_path", "checksums_path"}.isdisjoint(record.json()))
            self.assertEqual(200, download.status_code)
            self.assertEqual("application/zip", download.headers["content-type"])
            self.assertEqual('attachment; filename="project-demo-checkpoint-r7.zip"', download.headers["content-disposition"])
            archive_path = workspace / "v2/operator/delivery/exports/delivery-export-00000001/archive.zip"
            self.assertEqual(archive_path.read_bytes(), download.content)

    def test_unknown_delivery_record_and_download_return_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)
            unknown = "delivery-export-unknown-0001"

            self.assertEqual(200, client.get(self.route("/exports")).status_code)
            record = client.get(self.route(f"/exports/{unknown}"))
            download = client.get(self.route(f"/exports/{unknown}/download"))

            self.assertEqual(404, record.status_code)
            self.assertEqual(404, download.status_code)

    def test_each_caller_owned_identity_reuse_conflicts_without_second_completion(self) -> None:
        identities = (
            ("delivery_export_request_id", lambda request: request["export_request"].__setitem__("delivery_export_request_id", "delivery-export-request-00000001")),
            ("export_id", lambda request: request.__setitem__("export_id", "delivery-export-00000001")),
            ("delivery_package_id", lambda request: request.__setitem__("delivery_package_id", "delivery-package-00000001")),
            ("delivery_export_result_id", lambda request: request.__setitem__("delivery_export_result_id", "delivery-export-result-00000001")),
            ("copywriter_manifest", lambda request: request["role_package_requests"][0].__setitem__("role_handoff_manifest_id", "role-handoff-copywriter-00000001")),
            ("developer_manifest", lambda request: request["role_package_requests"][1].__setitem__("role_handoff_manifest_id", "role-handoff-developer-00000001")),
            ("notion_manifest", lambda request: request["notion_import_request"].__setitem__("notion_import_manifest_id", "notion-import-00000001")),
        )
        for identity, reuse in identities:
            with self.subTest(identity=identity), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                seed_workspace(workspace)
                client = self.client(workspace)
                self.assertEqual(201, client.post(self.route("/exports"), json=delivery_request()).status_code)
                replay = delivery_request(
                    idempotency_key="idem-delivery-00000002",
                    export_id="delivery-export-00000002",
                    delivery_package_id="delivery-package-00000002",
                    delivery_export_result_id="delivery-export-result-00000002",
                    delivery_export_request_id="delivery-export-request-00000002",
                )
                replay["role_package_requests"][0]["role_handoff_manifest_id"] = "role-handoff-copywriter-00000002"
                replay["role_package_requests"][1]["role_handoff_manifest_id"] = "role-handoff-developer-00000002"
                replay["notion_import_request"]["notion_import_manifest_id"] = "notion-import-00000002"
                reuse(replay)
                response = client.post(self.route("/exports"), json=replay)
                self.assertEqual(409, response.status_code)
                self.assertEqual(["delivery-export-00000001"], [item["export_id"] for item in client.get(self.route("/exports")).json()["data"]])

    def test_incomplete_material_is_hidden_from_history_and_unavailable_to_record_or_download(self) -> None:
        boundaries = (
            DeliveryFailureBoundary.SIDECAR_WRITTEN,
            DeliveryFailureBoundary.ARCHIVE_WRITTEN,
            DeliveryFailureBoundary.PACKAGE_RECORD_WRITTEN,
            DeliveryFailureBoundary.RESULT_WRITTEN,
            DeliveryFailureBoundary.BEFORE_IDEMPOTENCY,
        )
        for boundary in boundaries:
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                seed_workspace(workspace)
                request = transaction()
                write_incomplete_delivery(workspace, request, boundary)
                client = self.client(workspace)
                self.assertEqual([], client.get(self.route("/exports")).json()["data"])
                record = client.get(self.route(f"/exports/{request.result.export_id}"))
                download = client.get(self.route(f"/exports/{request.result.export_id}/download"))
                self.assertEqual(503, record.status_code)
                self.assertEqual("ERROR_DELIVERY_PERSISTENCE", record.json()["code"])
                self.assertEqual(503, download.status_code)
                self.assertEqual("ERROR_DELIVERY_PERSISTENCE", download.json()["code"])

    def test_corrupt_export_metadata_archive_and_hash_binding_fail_closed(self) -> None:
        mutations = (
            ("metadata", "delivery-package-record.json", b"{not-json"),
            ("archive", "archive.zip", b"not-a-zip"),
            ("hash", "result.json", None),
        )
        for name, filename, content in mutations:
            with self.subTest(corruption=name), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                seed_workspace(workspace)
                client = self.client(workspace)
                payload = delivery_request()
                self.assertEqual(201, client.post(self.route("/exports"), json=payload).status_code)
                export_root = workspace / "v2/operator/delivery/exports/delivery-export-00000001"
                target = export_root / filename
                if content is None:
                    result = json.loads(target.read_text(encoding="utf-8"))
                    result["zip_sha256"] = "0" * 64
                    target.write_text(json.dumps(result, separators=(",", ":"), sort_keys=True), encoding="utf-8")
                else:
                    target.write_bytes(content)

                response = client.get(self.route(f"/exports/{payload['export_id']}"))

                self.assertEqual(503, response.status_code)
                self.assertEqual("ERROR_DELIVERY_PERSISTENCE", response.json()["code"])

    def test_generated_package_has_no_host_paths_credentials_callback_authority_or_mutation_instructions(self) -> None:
        forbidden = (
            b"/home/",
            b"C:\\Users\\",
            b"\\\\host\\",
            b"api_key",
            b"client_secret",
            b"callback",
            b"resume_run",
            b"artifact_mutation",
            b"task_completion_callback",
        )
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)
            payload = delivery_request()
            self.assertEqual(201, client.post(self.route("/exports"), json=payload).status_code)

            download = client.get(self.route(f"/exports/{payload['export_id']}/download"))

            self.assertEqual(200, download.status_code)
            with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
                package_bytes = b"\n".join(archive.read(name) for name in archive.namelist())
            self.assertTrue(all(token not in package_bytes for token in forbidden))

    def test_read_routes_do_not_mutate_workflow_or_any_canonical_workspace_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            client = self.client(workspace)
            payload = delivery_request()
            self.assertEqual(201, client.post(self.route("/exports"), json=payload).status_code)
            before = workspace_snapshot(workspace, include_delivery=True)

            history = client.get(self.route("/exports"))
            record = client.get(self.route(f"/exports/{payload['export_id']}"))
            download = client.get(self.route(f"/exports/{payload['export_id']}/download"))

            self.assertEqual(200, history.status_code)
            self.assertEqual(200, record.status_code)
            self.assertEqual(200, download.status_code)
            self.assertEqual(before, workspace_snapshot(workspace, include_delivery=True))


if __name__ == "__main__":
    unittest.main()
