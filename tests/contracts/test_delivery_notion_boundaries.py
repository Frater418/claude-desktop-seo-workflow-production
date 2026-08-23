from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from services.delivery.contract_validation import validate_delivery_contracts, validate_notion_import_replay


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "delivery"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class DeliveryNotionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        schema = json.loads((ROOT / "standards" / "delivery" / "notion-import-manifest.schema.json").read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(schema, format_checker=FormatChecker())

    def assert_schema_valid(self, notion: dict) -> None:
        errors = list(self.validator.iter_errors(notion))
        self.assertEqual([], errors, [error.message for error in errors])

    def assert_semantic_error(self, notion: dict) -> None:
        self.assert_schema_valid(notion)
        result = validate_delivery_contracts(load("positive-final-package.json"), [load("positive-role-handoff.json")], notion)
        self.assertFalse(result.valid)

    def test_schema_rejects_implementation_artifact_mutation_and_missing_plan_reference(self) -> None:
        mutations = (
            ("artifact_mutation", lambda value: value["task_rows"][1].update(artifact_mutation="artifact-developer-001")),
            ("released_plan_artifact_id", lambda value: value["performance_checkpoint_rows"][0].pop("released_plan_artifact_id")),
        )
        for field, mutate in mutations:
            with self.subTest(field=field):
                notion = load("positive-notion-import.json")
                mutate(notion)
                self.assertTrue(list(self.validator.iter_errors(notion)))

    def test_semantic_rejects_each_dangling_row_reference(self) -> None:
        mutations = (
            ("artifact_rows", "project_external_id", 0), ("review_rows", "artifact_external_id", 0),
            ("approval_rows", "artifact_external_id", 0), ("blocker_rows", "artifact_external_id", 0),
            ("priority_rows", "task_external_id", 0), ("deadline_rows", "task_external_id", 0),
        )
        for collection, field, index in mutations:
            with self.subTest(collection=collection, field=field):
                notion = load("positive-notion-import.json")
                notion[collection][index][field] = "task-missing-0001" if "task" in field else "artifact-missing-0001"
                if collection == "artifact_rows":
                    notion[collection][index][field] = "project-missing"
                self.assert_semantic_error(notion)

    def test_semantic_rejects_each_duplicate_external_id(self) -> None:
        for collection in ("project_rows", "artifact_rows", "review_rows", "approval_rows", "blocker_rows", "assignment_rows"):
            with self.subTest(collection=collection):
                notion = load("positive-notion-import.json")
                duplicate = copy.deepcopy(notion[collection][0])
                if "source_sha256" in duplicate:
                    duplicate["source_sha256"] = "b" * 64
                elif "content_sha256" in duplicate:
                    duplicate["content_sha256"] = "b" * 64
                else:
                    duplicate["assignee"] = "other"
                notion[collection].append(duplicate)
                self.assert_semantic_error(notion)

    def test_replay_conflicts_for_changed_stable_collection_payloads(self) -> None:
        for collection in ("project_rows", "artifact_rows", "review_rows", "approval_rows", "blocker_rows", "assignment_rows"):
            with self.subTest(collection=collection):
                existing = load("positive-notion-import.json")
                replay = copy.deepcopy(existing)
                replay[collection][0]["source_sha256"] = "b" * 64 if "source_sha256" in replay[collection][0] else replay[collection][0].update(assignee="other")
                result = validate_notion_import_replay(existing, replay)
                self.assertIn("DELIVERY_REPLAY_CONFLICT", {error.code for error in result.errors})

    def test_replay_conflicts_for_added_or_removed_stable_rows(self) -> None:
        for collection in ("customer_rows", "project_rows", "task_rows"):
            for operation in ("added", "removed"):
                with self.subTest(collection=collection, operation=operation):
                    existing = load("positive-notion-import.json")
                    replay = copy.deepcopy(existing)
                    if operation == "added":
                        replay[collection].append(copy.deepcopy(replay[collection][-1]))
                    else:
                        replay[collection].pop()
                    result = validate_notion_import_replay(existing, replay)
                    self.assertIn("DELIVERY_REPLAY_CONFLICT", {error.code for error in result.errors})

    def test_exact_replay_is_stable_and_unmodified(self) -> None:
        existing = load("positive-notion-import.json")
        replay = copy.deepcopy(existing)
        baseline = json.dumps((existing, replay), sort_keys=True, separators=(",", ":"))
        result = validate_notion_import_replay(existing, replay)
        self.assertTrue(result.valid, result.errors)
        self.assertTrue(result.idempotent)
        self.assertEqual(baseline, json.dumps((existing, replay), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    unittest.main()
