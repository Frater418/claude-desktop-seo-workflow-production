from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Callable

from services.operator_api.diagnostic_trace_models import DiagnosticTraceOperation, DiagnosticTraceOperationRecord, DiagnosticTraceStart
from services.operator_api.diagnostic_trace_store import DiagnosticTraceFailureBoundary, DiagnosticTraceLimits, DiagnosticTraceStore, DiagnosticTraceStoreError


class DiagnosticTraceLimitTests(unittest.TestCase):
    def start(self, created_at: str = "2026-08-22T10:15:30Z") -> DiagnosticTraceStart:
        return DiagnosticTraceStart(
            schema_version="1.0.0",
            tenant_id="tenant-contract",
            project_id="project-contract",
            run_id="run-contract-0001",
            scenario_id="automated-smoke-0001",
            source="automated",
            created_at=created_at,
        )

    def operation(self, operation_id: str = "operation-contract-0001") -> DiagnosticTraceOperation:
        return DiagnosticTraceOperation(
            operation_id=operation_id,
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
            evidence_references=(),
        )

    def limits(self, **overrides: int) -> DiagnosticTraceLimits:
        values = {
            "max_closed_runs": 10,
            "max_operations_per_run": 10,
            "max_run_bytes": 1_000_000,
            "max_index_bytes": 1_000_000,
            "max_serialized_record_bytes": 100_000,
            "close_reserve_bytes": 1,
            "index_reserve_bytes": 1,
        }
        values.update(overrides)
        return DiagnosticTraceLimits(**values)

    def snapshot(self, root: Path) -> dict[Path, bytes]:
        paths = (Path("current.json"), Path("index.jsonl"), Path("pending.json"))
        runs = root / "runs"
        run_paths = tuple(path.relative_to(root) for path in runs.glob("*.jsonl")) if runs.exists() else ()
        return {path: (root / path).read_bytes() for path in (*paths, *run_paths) if (root / path).exists()}

    def record_bytes(self, record: DiagnosticTraceOperationRecord) -> bytes:
        return (
            json.dumps(record.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")

    def run_path(self, root: Path, trace_id: str) -> Path:
        return next((root / "runs").glob(f"*_{trace_id}.jsonl"))

    def interrupted(self, expected: DiagnosticTraceFailureBoundary) -> Callable[[DiagnosticTraceFailureBoundary], None]:
        def inject(actual: DiagnosticTraceFailureBoundary) -> None:
            if actual is expected:
                raise RuntimeError(actual.value)

        return inject

    def assert_error(self, action: Callable[[], object], code: str) -> None:
        with self.assertRaises(DiagnosticTraceStoreError) as raised:
            action()
        self.assertEqual(code, raised.exception.code)

    def assert_close_recovery(self, boundary: DiagnosticTraceFailureBoundary, before: dict[Path, bytes], after: dict[Path, bytes]) -> None:
        run = next(path for path in before if path.parent == Path("runs"))
        if boundary is DiagnosticTraceFailureBoundary.PENDING_CLOSE_INTENT:
            self.assertTrue(after[run].startswith(before[run]))
            self.assertNotEqual(before[run], after[run])
        else:
            self.assertEqual(before[run], after[run])
        if boundary in (DiagnosticTraceFailureBoundary.PENDING_CLOSE_INTENT, DiagnosticTraceFailureBoundary.TERMINAL_RECORD):
            self.assertNotIn(Path("index.jsonl"), before)
            self.assertIn(Path("index.jsonl"), after)
        else:
            self.assertEqual(before[Path("index.jsonl")], after[Path("index.jsonl")])
        if boundary is DiagnosticTraceFailureBoundary.CLOSE_CURRENT_REPLACE:
            self.assertEqual(before[Path("current.json")], after[Path("current.json")])
        else:
            self.assertNotEqual(before[Path("current.json")], after[Path("current.json")])

    def test_default_limits_are_the_approved_production_bounds(self) -> None:
        limits = DiagnosticTraceLimits()

        self.assertEqual(
            (100, 1_000, 5 * 1024 * 1024, 1 * 1024 * 1024, 64 * 1024, 4 * 1024, 4 * 1024),
            (
                limits.max_closed_runs,
                limits.max_operations_per_run,
                limits.max_run_bytes,
                limits.max_index_bytes,
                limits.max_serialized_record_bytes,
                limits.close_reserve_bytes,
                limits.index_reserve_bytes,
            ),
        )

    def test_operation_count_record_and_run_limits_accept_the_boundary_and_reject_first_over(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            trace = DiagnosticTraceStore(root).create(self.start())
            operation = self.operation()
            record = DiagnosticTraceOperationRecord(record_type="operation", operation=operation.model_copy(update={"sequence": 1}))
            record_size = len(self.record_bytes(record))
            base_size = self.run_path(root, trace.trace_id).stat().st_size
            close_reserve = self.limits().close_reserve_bytes

            count_store = DiagnosticTraceStore(root, limits=self.limits(max_operations_per_run=1))
            count_store.append(trace.trace_id, operation)
            before_count = self.snapshot(root)
            with self.assertRaises(DiagnosticTraceStoreError):
                count_store.append(trace.trace_id, self.operation("operation-contract-0002"))
            self.assertEqual(before_count, self.snapshot(root))

        for name, limit, rejected in (
            ("record", self.limits(max_serialized_record_bytes=record_size), self.limits(max_serialized_record_bytes=record_size - 1)),
            ("run", self.limits(max_run_bytes=base_size + record_size + close_reserve), self.limits(max_run_bytes=base_size + record_size + close_reserve - 1)),
        ):
            with self.subTest(limit=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                trace = DiagnosticTraceStore(root).create(self.start())
                DiagnosticTraceStore(root, limits=limit).append(trace.trace_id, operation)

            with self.subTest(limit=f"{name}-first-over"), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                trace = DiagnosticTraceStore(root).create(self.start())
                before = self.snapshot(root)
                with self.assertRaises(DiagnosticTraceStoreError):
                    DiagnosticTraceStore(root, limits=rejected).append(trace.trace_id, operation)
                self.assertEqual(before, self.snapshot(root))

    def test_create_reserves_index_capacity_and_closed_run_retention_before_writing(self) -> None:
        for name, limits, code in (
            ("index-exact", lambda size: self.limits(max_index_bytes=size + 1), None),
            ("index-first-over", lambda size: self.limits(max_index_bytes=size), "ERROR_DIAGNOSTIC_INDEX_SIZE_LIMIT"),
            ("retention", lambda size: self.limits(max_closed_runs=1), "ERROR_DIAGNOSTIC_RETENTION_LIMIT"),
        ):
            with self.subTest(limit=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                store = DiagnosticTraceStore(root)
                first = store.create(self.start())
                store.close(first.trace_id, close_id="close-contract-0001", closed_at="2026-08-22T10:15:32Z")
                before = self.snapshot(root)
                candidate = self.start("2026-08-22T10:15:33Z")
                bounded = DiagnosticTraceStore(root, limits=limits(len(before[Path("index.jsonl")])))
                if code is None:
                    self.assertEqual("active", bounded.create(candidate).status)
                else:
                    self.assert_error(lambda: bounded.create(candidate), code)
                    self.assertEqual(before, self.snapshot(root))

    def test_create_and_close_replay_only_the_missing_pending_stages(self) -> None:
        create_boundaries = (
            DiagnosticTraceFailureBoundary.PENDING_CREATE,
            DiagnosticTraceFailureBoundary.START_RECORD,
            DiagnosticTraceFailureBoundary.CREATE_CURRENT_REPLACE,
        )
        for boundary in create_boundaries:
            with self.subTest(operation="create", boundary=boundary), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                failing = DiagnosticTraceStore(root, failure_injector=self.interrupted(boundary))
                with self.assertRaises(RuntimeError):
                    failing.create(self.start())
                before = self.snapshot(root)
                recovery = DiagnosticTraceStore(root)
                recovered = recovery.create(self.start())
                after = self.snapshot(root)
                self.assertFalse((root / "pending.json").exists())
                self.assertEqual("active", recovered.status)
                self.assertTrue(recovery.replay)
                if boundary is not DiagnosticTraceFailureBoundary.PENDING_CREATE:
                    run = next(path for path in before if path.parent == Path("runs"))
                    self.assertEqual(before[run], after[run])
                if boundary is DiagnosticTraceFailureBoundary.CREATE_CURRENT_REPLACE:
                    self.assertEqual(before[Path("current.json")], after[Path("current.json")])

        close_boundaries = (
            DiagnosticTraceFailureBoundary.PENDING_CLOSE_INTENT,
            DiagnosticTraceFailureBoundary.TERMINAL_RECORD,
            DiagnosticTraceFailureBoundary.INDEX_APPEND,
            DiagnosticTraceFailureBoundary.CLOSE_CURRENT_REPLACE,
        )
        for boundary in close_boundaries:
            with self.subTest(operation="close", boundary=boundary), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                failing = DiagnosticTraceStore(root, failure_injector=self.interrupted(boundary))
                trace = failing.create(self.start())
                with self.assertRaises(RuntimeError):
                    failing.close(trace.trace_id, close_id="close-contract-0001", closed_at="2026-08-22T10:15:32Z")
                before = self.snapshot(root)
                recovery = DiagnosticTraceStore(root)
                recovered = recovery.close(trace.trace_id, close_id="close-contract-0001", closed_at="2026-08-22T10:15:32Z")
                after = self.snapshot(root)
                self.assertFalse((root / "pending.json").exists())
                self.assertEqual("closed", recovered.status)
                self.assertTrue(recovery.replay)
                self.assert_close_recovery(boundary, before, after)

    def test_pending_conflicts_and_tampering_fail_closed_without_changing_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            failing = DiagnosticTraceStore(root, failure_injector=self.interrupted(DiagnosticTraceFailureBoundary.PENDING_CREATE))
            with self.assertRaises(RuntimeError):
                failing.create(self.start())
            before = self.snapshot(root)
            store = DiagnosticTraceStore(root)
            trace_id = f"trace-{'0' * 32}"
            for action in (
                lambda: store.create(self.start("2026-08-22T10:15:33Z")),
                lambda: store.append(trace_id, self.operation()),
                lambda: store.close(trace_id, close_id="close-contract-0002", closed_at="2026-08-22T10:15:34Z"),
            ):
                self.assert_error(action, "ERROR_DIAGNOSTIC_RECOVERY_REQUIRED")
                self.assertEqual(before, self.snapshot(root))

        for name, corrupt in (("partial-jsonl", b'{"record_type":"trace_start"}'), ("tampered-pending", b'{"stage":"tampered"}\n')):
            with self.subTest(material=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                store = DiagnosticTraceStore(root)
                trace = store.create(self.start())
                target = self.run_path(root, trace.trace_id) if name == "partial-jsonl" else root / "pending.json"
                target.write_bytes(corrupt)
                before = self.snapshot(root)
                with self.assertRaises(DiagnosticTraceStoreError):
                    store.append(trace.trace_id, self.operation())
                self.assertEqual(before, self.snapshot(root))

    def test_append_writes_exactly_one_record_and_rejection_preserves_prior_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = DiagnosticTraceStore(root)
            trace = store.create(self.start())
            path = self.run_path(root, trace.trace_id)
            before = path.read_bytes()
            operation = self.operation()
            recorded = store.append(trace.trace_id, operation)
            expected = self.record_bytes(DiagnosticTraceOperationRecord(record_type="operation", operation=recorded))
            self.assertEqual(before + expected, path.read_bytes())
            immutable = path.read_bytes()
            with self.assertRaises(DiagnosticTraceStoreError):
                store.append(trace.trace_id, operation.model_copy(update={"action": "different_delivery_action"}))
            self.assertEqual(immutable, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
