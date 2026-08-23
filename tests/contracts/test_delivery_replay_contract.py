from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from services.delivery.contract_validation import validate_notion_import_replay


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "delivery" / "positive-notion-import.json"


def manifest() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class DeliveryReplayContractTests(unittest.TestCase):
    def test_exact_replay_is_idempotent_without_input_mutation(self) -> None:
        existing = manifest()
        replay = copy.deepcopy(existing)
        baseline = copy.deepcopy((existing, replay))
        result = validate_notion_import_replay(existing, replay)
        self.assertTrue(result.valid, result.errors)
        self.assertTrue(result.idempotent)
        self.assertEqual(baseline, (existing, replay))

    def test_changed_stable_rows_and_revisions_conflict(self) -> None:
        for mutate in (
            lambda value: value["task_rows"][1].update(title="Changed"),
            lambda value: value["customer_rows"].append(copy.deepcopy(value["customer_rows"][0])),
            lambda value: value.update(source_snapshot_revision=10),
            lambda value: value["relations"][0].update(relation_type="depends_on"),
        ):
            with self.subTest(mutate=mutate):
                replay = manifest()
                mutate(replay)
                result = validate_notion_import_replay(manifest(), replay)
                self.assertFalse(result.valid)
                self.assertIn("DELIVERY_REPLAY_CONFLICT", {error.code for error in result.errors})


if __name__ == "__main__":
    unittest.main()
