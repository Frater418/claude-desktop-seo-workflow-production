from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from services.operator_api.diagnostic_trace_store import (
    DiagnosticTraceStore,
    DiagnosticTraceStoreError,
)
from services.operator_api.diagnostic_trace_models import (
    DiagnosticTrace,
    DiagnosticTraceOperation,
    DiagnosticTraceStart,
    TraceEvidenceReference,
)


class DiagnosticTraceStoreTests(unittest.TestCase):
    def start_request(self) -> DiagnosticTraceStart:
        return DiagnosticTraceStart(
            schema_version="1.0.0",
            tenant_id="tenant-contract",
            project_id="project-contract",
            run_id="run-contract-0001",
            scenario_id="automated-smoke-0001",
            source="automated",
            created_at="2026-08-22T10:15:30Z",
        )

    def success(self) -> DiagnosticTraceOperation:
        return DiagnosticTraceOperation(
            operation_id="operation-contract-0001",
            occurred_at="2026-08-22T10:15:31Z",
            action="create_delivery",
            route="/v1/tenants/tenant-contract/projects/project-contract/delivery/exports",
            api_method="POST",
            api_status=201,
            error_code=None,
            remediation=None,
            expected_actions=("create_delivery",),
            rendered_actions=("create_delivery",),
            disabled_actions=(),
            evidence_references=(
                TraceEvidenceReference(
                    kind="screenshot",
                    relative_path="screenshots/delivery-created.png",
                ),
            ),
        )

    def failure(self) -> DiagnosticTraceOperation:
        return DiagnosticTraceOperation(
            operation_id="operation-contract-0002",
            occurred_at="2026-08-22T10:15:32Z",
            action="download_delivery",
            route="/v1/tenants/tenant-contract/projects/project-contract/delivery/exports/export-0001/download",
            api_method="GET",
            api_status=503,
            error_code="ERROR_DELIVERY_PERSISTENCE",
            remediation="repair-delivery-recovery",
            expected_actions=("download_delivery",),
            rendered_actions=("download_delivery",),
            disabled_actions=(),
            evidence_references=(),
        )

    def create_started(self, root: Path) -> tuple[DiagnosticTraceStore, DiagnosticTrace]:
        store = DiagnosticTraceStore(root)
        return store, store.create(self.start_request())

    def test_create_current_ordered_append_exact_replay_and_immutable_close(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store, started = self.create_started(root)
            run_path = root / "runs" / f"20260822T101530Z_{started.trace_id}.jsonl"

            self.assertTrue(started.trace_id)
            self.assertEqual("active", started.status)
            self.assertEqual("tenant-contract", started.tenant_id)
            self.assertEqual("project-contract", started.project_id)
            self.assertEqual("run-contract-0001", started.run_id)
            self.assertEqual("automated-smoke-0001", started.scenario_id)
            self.assertTrue(run_path.is_file())
            self.assertEqual(started, store.current())
            self.assertEqual(
                {
                    "trace_id": started.trace_id,
                    "relative_run_path": str(run_path.relative_to(root)),
                    "tenant_id": started.tenant_id,
                    "project_id": started.project_id,
                    "run_id": started.run_id,
                    "scenario_id": started.scenario_id,
                    "status": "active",
                },
                json.loads((root / "current.json").read_text(encoding="utf-8")),
            )
            first = store.append(started.trace_id, self.success())
            replay = store.append(started.trace_id, self.success())
            second = store.append(started.trace_id, self.failure())
            self.assertEqual(first, replay)
            self.assertEqual(
                ("operation-contract-0001", "operation-contract-0002"),
                tuple(item.operation_id for item in store.current().operations),
            )
            changed = self.success().model_copy(update={"action": "different_delivery_action"})
            with self.assertRaises(DiagnosticTraceStoreError):
                store.append(started.trace_id, changed)

            closed = store.close(started.trace_id, close_id="close-contract-0001", closed_at="2026-08-22T10:15:33Z")
            closed_bytes = run_path.read_bytes()
            self.assertEqual("operation-contract-0001", closed.last_successful_operation_id)
            self.assertEqual("operation-contract-0002", closed.first_failing_operation_id)
            self.assertEqual("closed", closed.status)
            self.assertEqual(
                {
                    "trace_id": started.trace_id,
                    "relative_run_path": str(run_path.relative_to(root)),
                    "tenant_id": started.tenant_id,
                    "project_id": started.project_id,
                    "run_id": started.run_id,
                    "scenario_id": started.scenario_id,
                    "status": "closed",
                },
                json.loads((root / "current.json").read_text(encoding="utf-8")),
            )
            self.assertEqual((started.trace_id,), tuple(item.trace_id for item in store.index()))
            index_entries = [
                json.loads(line)
                for line in (root / "index.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual([started.trace_id], [entry["trace_id"] for entry in index_entries])
            self.assertEqual(["closed"], [entry["status"] for entry in index_entries])
            self.assertEqual(closed, store.current())
            with self.assertRaises(DiagnosticTraceStoreError):
                store.append(started.trace_id, self.failure())
            self.assertEqual(closed_bytes, run_path.read_bytes())

    def test_retry_creates_a_distinct_trace_linked_to_the_closed_predecessor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store, started = self.create_started(root)
            closed = store.close(started.trace_id, close_id="close-contract-0001", closed_at="2026-08-22T10:15:31Z")
            closed_path = root / "runs" / f"20260822T101530Z_{closed.trace_id}.jsonl"
            closed_bytes = closed_path.read_bytes()

            retry = store.retry(closed.trace_id, started_at="2026-08-22T10:16:00Z")
            retry_path = root / "runs" / f"20260822T101600Z_{retry.trace_id}.jsonl"

            self.assertNotEqual(closed.trace_id, retry.trace_id)
            self.assertEqual(closed.trace_id, retry.predecessor_trace_id)
            self.assertEqual("active", retry.status)
            self.assertEqual(
                (closed.tenant_id, closed.project_id, closed.run_id, closed.scenario_id),
                (retry.tenant_id, retry.project_id, retry.run_id, retry.scenario_id),
            )
            self.assertTrue(retry_path.is_file())
            self.assertEqual(retry, store.current())
            self.assertEqual((closed.trace_id,), tuple(item.trace_id for item in store.index()))
            self.assertEqual(
                [closed.trace_id],
                [
                    json.loads(line)["trace_id"]
                    for line in (root / "index.jsonl").read_text(encoding="utf-8").splitlines()
                ],
            )
            self.assertEqual(closed_bytes, closed_path.read_bytes())
            retried_closed = store.close(retry.trace_id, close_id="close-contract-0002", closed_at="2026-08-22T10:16:01Z")
            self.assertEqual("closed", retried_closed.status)
            self.assertEqual((closed.trace_id, retry.trace_id), tuple(item.trace_id for item in store.index()))


if __name__ == "__main__":
    unittest.main()
