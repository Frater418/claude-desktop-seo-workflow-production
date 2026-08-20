from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from services.operator_api.event_store import EventStore, EventStoreError


ROOT = Path(__file__).resolve().parents[1]


def event() -> dict[str, object]:
    return {
        "event_id": "event-00000001",
        "event_type": "run.started",
        "schema_version": "2.0.0",
        "occurred_at": "2026-08-20T00:00:00Z",
        "correlation_id": "corr-00000001",
        "idempotency_key": "idem-00000001",
        "identity": {
            "tenant_id": "tenant-demo",
            "project_id": "project-demo",
            "run_id": "run-00000001",
            "step_id": "0",
            "revision": 1,
        },
        "integration_mode": "simulated",
        "simulation_id": "sim-00000001",
        "payload": {"attempt": 1, "input_hash": "0" * 64},
    }


class EventStoreTests(unittest.TestCase):
    def store(self, workspace: Path) -> EventStore:
        return EventStore.from_repository_root(ROOT, workspace)

    def test_rejects_invalid_event_before_creating_log(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            invalid = event()
            invalid["event_type"] = "invented.event"

            with self.assertRaisesRegex(EventStoreError, "ERROR_CONTEXT_SCHEMA_INVALID"):
                self.store(workspace).append(invalid)

            self.assertFalse((workspace / "v2/operator/events/events.jsonl").exists())

    def test_replays_identical_event_and_rejects_idempotency_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = self.store(Path(temporary))
            first = store.append(event())
            replay = store.append(event())
            conflicting = copy.deepcopy(event())
            conflicting["event_id"] = "event-00000002"
            conflicting["payload"] = {"attempt": 2, "input_hash": "0" * 64}

            self.assertFalse(first.replay)
            self.assertTrue(replay.replay)
            with self.assertRaisesRegex(EventStoreError, "ERR_IDEMPOTENCY_CONFLICT"):
                store.append(conflicting)
            lines = (Path(temporary) / "v2/operator/events/events.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual([event()], [json.loads(line) for line in lines])

    def test_rejects_partial_tail_and_duplicate_event_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            events = workspace / "v2/operator/events"
            events.mkdir(parents=True)
            (events / "events.jsonl").write_text(json.dumps(event()), encoding="utf-8")

            with self.assertRaisesRegex(EventStoreError, "ERROR_CONTEXT_SOURCE_INVALID"):
                self.store(workspace).append(event())

            duplicate = event()
            duplicate["idempotency_key"] = "idem-00000002"
            (events / "events.jsonl").write_text(
                f"{json.dumps(event())}\n{json.dumps(duplicate)}\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(EventStoreError, "ERROR_CONTEXT_SOURCE_INVALID"):
                self.store(workspace).append(event())


if __name__ == "__main__":
    unittest.main()
