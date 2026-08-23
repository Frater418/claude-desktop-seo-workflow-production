from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Final

from fastapi.testclient import TestClient
from pydantic import JsonValue

from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry
from tests.support.delivery_api import PROJECT, TENANT, seed_workspace


ROOT: Final = Path(__file__).resolve().parents[1]
RUN_ID: Final = "run-step-4a-0001"
CREATED_AT: Final = "2026-08-22T10:15:30Z"


class DiagnosticTraceApiTests(unittest.TestCase):
    def client(self, workspace: Path, diagnostic_root: Path) -> TestClient:
        registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
        return TestClient(create_app(registry, ROOT, AppConfig(ROOT, diagnostic_root=diagnostic_root)))

    def route(self, suffix: str = "") -> str:
        return f"/v1/tenants/{TENANT}/projects/{PROJECT}/diagnostic-traces{suffix}"

    def start(self, run_id: str = RUN_ID) -> dict[str, JsonValue]:
        return {
            "schema_version": "1.0.0",
            "tenant_id": TENANT,
            "project_id": PROJECT,
            "run_id": run_id,
            "scenario_id": "automated-smoke-0001",
            "source": "automated",
            "created_at": CREATED_AT,
        }

    def operation(self, operation_id: str = "operation-contract-0001") -> dict[str, JsonValue]:
        return {
            "operation_id": operation_id,
            "occurred_at": "2026-08-22T10:15:31Z",
            "action": "create_delivery",
            "route": f"/v1/tenants/{TENANT}/projects/{PROJECT}/delivery/exports",
            "api_method": "POST",
            "api_status": 201,
            "error_code": None,
            "remediation": None,
            "expected_actions": ["create_delivery"],
            "rendered_actions": ["create_delivery"],
            "disabled_actions": [],
            "evidence_references": [{"kind": "artifact", "relative_path": "delivery/exports/export-0001.json"}],
        }

    @staticmethod
    def snapshot(root: Path) -> dict[str, bytes]:
        return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}

    def test_create_replays_exact_start_and_rejects_changed_active_start_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            diagnostic_root = root / "diagnostic-root"
            seed_workspace(workspace)
            client = self.client(workspace, diagnostic_root)

            created = client.post(self.route(), json=self.start())
            replayed = client.post(self.route(), json=self.start())

            self.assertEqual(201, created.status_code)
            self.assertEqual("active", created.json()["status"])
            self.assertFalse(created.json()["replay"])
            self.assertEqual(200, replayed.status_code)
            self.assertTrue(replayed.json()["replay"])
            self.assertEqual(created.json()["trace_id"], replayed.json()["trace_id"])
            before_conflict = self.snapshot(diagnostic_root)
            changed = self.start()
            changed["scenario_id"] = "automated-smoke-0002"
            conflict = client.post(self.route(), json=changed)
            self.assertEqual(409, conflict.status_code)
            self.assertEqual("ERROR_DIAGNOSTIC_TRACE_CONFLICT", conflict.json()["code"])
            self.assertEqual(before_conflict, self.snapshot(diagnostic_root))

    def test_start_validates_strict_route_identity_and_canonical_run_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            diagnostic_root = root / "diagnostic-root"
            seed_workspace(workspace)
            client = self.client(workspace, diagnostic_root)
            invalid = self.start()
            invalid["unexpected"] = "value"
            for payload, status, code in (
                (invalid, 422, "ERROR_DIAGNOSTIC_TRACE_REQUEST_INVALID"),
                (dict(self.start(), tenant_id="tenant-other"), 409, "ERR_DIAGNOSTIC_TRACE_IDENTITY_CONFLICT"),
                (dict(self.start(), project_id="project-other"), 409, "ERR_DIAGNOSTIC_TRACE_IDENTITY_CONFLICT"),
                (self.start("run-missing-0001"), 404, "ERROR_DOMAIN_CONTRACT_FILE_MISSING"),
            ):
                with self.subTest(code=code):
                    response = client.post(self.route(), json=payload)
                    self.assertEqual(status, response.status_code)
                    self.assertEqual(code, response.json()["code"])
                    self.assertNotIn(str(diagnostic_root), response.text)
                    self.assertEqual({}, self.snapshot(diagnostic_root))

    def test_append_replays_exact_operation_rejects_reuse_and_preserves_route_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            diagnostic_root = root / "diagnostic-root"
            seed_workspace(workspace)
            client = self.client(workspace, diagnostic_root)
            trace_id = client.post(self.route(), json=self.start()).json()["trace_id"]
            target = self.route(f"/{trace_id}/entries")

            created = client.post(target, json=self.operation())
            replayed = client.post(target, json=self.operation())

            self.assertEqual(201, created.status_code)
            self.assertEqual(1, created.json()["sequence"])
            self.assertFalse(created.json()["replay"])
            self.assertEqual(200, replayed.status_code)
            self.assertTrue(replayed.json()["replay"])
            changed = self.operation()
            changed["action"] = "changed_delivery"
            conflict = client.post(target, json=changed)
            self.assertEqual(409, conflict.status_code)
            self.assertEqual("ERROR_DIAGNOSTIC_TRACE_CONFLICT", conflict.json()["code"])
            before_cross_route = self.snapshot(diagnostic_root)
            for cross_route in (
                client.post(f"/v1/tenants/tenant-other/projects/{PROJECT}/diagnostic-traces/{trace_id}/entries", json=self.operation("operation-contract-0002")),
                client.post(f"/v1/tenants/{TENANT}/projects/project-other/diagnostic-traces/{trace_id}/entries", json=self.operation("operation-contract-0002")),
            ):
                self.assertIn(cross_route.status_code, (404, 409))
            self.assertEqual(before_cross_route, self.snapshot(diagnostic_root))

    def test_close_replays_exact_close_identity_and_blocks_later_append(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            diagnostic_root = root / "diagnostic-root"
            seed_workspace(workspace)
            client = self.client(workspace, diagnostic_root)
            trace_id = client.post(self.route(), json=self.start()).json()["trace_id"]
            entry_route = self.route(f"/{trace_id}/entries")
            self.assertEqual(201, client.post(entry_route, json=self.operation()).status_code)
            close_route = self.route(f"/{trace_id}/close")
            close = {"close_id": "close-contract-0001", "closed_at": "2026-08-22T10:15:32Z"}
            invalid_close = dict(close, unexpected="value")
            rejected = client.post(close_route, json=invalid_close)
            self.assertEqual(422, rejected.status_code)
            self.assertEqual("ERROR_DIAGNOSTIC_TRACE_REQUEST_INVALID", rejected.json()["code"])

            closed = client.post(close_route, json=close)
            closed_bytes = self.snapshot(diagnostic_root)
            replayed = client.post(close_route, json=close)

            self.assertEqual(200, closed.status_code)
            self.assertEqual("closed", closed.json()["status"])
            self.assertEqual(close["close_id"], closed.json()["close_id"])
            self.assertEqual(close["closed_at"], closed.json()["closed_at"])
            self.assertFalse(closed.json()["replay"])
            self.assertEqual(200, replayed.status_code)
            self.assertTrue(replayed.json()["replay"])
            self.assertEqual(closed_bytes, self.snapshot(diagnostic_root))
            for changed_close in (
                dict(close, close_id="close-contract-0002"),
                dict(close, closed_at="2026-08-22T10:15:33Z"),
            ):
                conflict = client.post(close_route, json=changed_close)
                self.assertEqual(409, conflict.status_code)
                self.assertEqual("ERROR_DIAGNOSTIC_TRACE_CONFLICT", conflict.json()["code"])
            append = client.post(entry_route, json=self.operation("operation-contract-0002"))
            self.assertEqual(409, append.status_code)
            self.assertEqual("ERROR_DIAGNOSTIC_TRACE_CLOSED", append.json()["code"])

    def test_storage_limit_and_unknown_trace_errors_are_stable_and_path_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            diagnostic_root = root / "diagnostic-root"
            seed_workspace(workspace)
            client = self.client(workspace, diagnostic_root)
            unknown = client.post(self.route("/trace-00000000000000000000000000000000/entries"), json=self.operation())
            self.assertEqual(404, unknown.status_code)
            self.assertEqual("ERROR_DIAGNOSTIC_TRACE_UNAVAILABLE", unknown.json()["code"])
            self.assertFalse(diagnostic_root.exists())
            trace_id = client.post(self.route(), json=self.start()).json()["trace_id"]
            oversized = self.operation()
            oversized["evidence_references"] = [
                {"kind": "artifact", "relative_path": f"evidence/{index}-{'x' * 490}.json"}
                for index in range(128)
            ]
            limited = client.post(self.route(f"/{trace_id}/entries"), json=oversized)
            self.assertEqual(422, limited.status_code)
            self.assertEqual("ERROR_DIAGNOSTIC_RECORD_SIZE_LIMIT", limited.json()["code"])
            storage_path = root / "not-a-directory"
            storage_path.write_text("blocked", encoding="utf-8")
            storage = self.client(workspace, storage_path).post(self.route(), json=self.start())
            self.assertEqual(503, storage.status_code)
            self.assertEqual("ERROR_DIAGNOSTIC_TRACE_ROOT_INVALID", storage.json()["code"])
            for response in (unknown, limited, storage):
                self.assertEqual({"code", "message"}, set(response.json()))
                self.assertNotIn(str(root), response.text)

    def test_closed_files_use_only_the_injected_root_and_expose_no_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            diagnostic_root = root / "diagnostic-root"
            seed_workspace(workspace)
            client = self.client(workspace, diagnostic_root)
            created = client.post(self.route(), json=self.start()).json()
            trace_id = created["trace_id"]
            self.assertEqual(201, client.post(self.route(f"/{trace_id}/entries"), json=self.operation()).status_code)
            closed = client.post(self.route(f"/{trace_id}/close"), json={"close_id": "close-contract-0001", "closed_at": "2026-08-22T10:15:32Z"})

            current = json.loads((diagnostic_root / "current.json").read_text(encoding="utf-8"))
            index = json.loads((diagnostic_root / "index.jsonl").read_text(encoding="utf-8"))
            run = (diagnostic_root / current["relative_run_path"]).read_text(encoding="utf-8")
            self.assertEqual(trace_id, current["trace_id"])
            self.assertEqual(trace_id, index["trace_id"])
            self.assertIn(trace_id, run)
            self.assertFalse((workspace / "diagnostic-root").exists())
            self.assertNotIn(str(diagnostic_root), json.dumps([created, closed.json(), current, index, run]))

    def test_diagnostic_read_routes_and_openapi_read_operations_are_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            diagnostic_root = root / "diagnostic-root"
            seed_workspace(workspace)
            registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
            app = create_app(registry, ROOT, AppConfig(ROOT, diagnostic_root=diagnostic_root))
            client = TestClient(app)

            for target in (self.route(), self.route("/trace-00000000000000000000000000000000"), self.route("/search"), self.route("/download")):
                with self.subTest(target=target):
                    self.assertIn(client.get(target).status_code, (404, 405))
            for path, operations in app.openapi()["paths"].items():
                if "/diagnostic-traces" in path:
                    self.assertNotIn("get", operations)
                    self.assertFalse(any(operation["operationId"].lower().startswith(("get", "list", "download", "search")) for operation in operations.values()))


if __name__ == "__main__":
    unittest.main()
