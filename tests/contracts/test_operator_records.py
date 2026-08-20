#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATOR_DIR = REPO_ROOT / "standards" / "operator"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "operator"
SCHEMA_NAMES = (
    "operator-task",
    "blocker-record",
    "revision-request",
    "workflow-defect",
    "escalation-record",
    "resolution-record",
)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def stale_artifact_errors(record):
    artifact = record["artifact"]
    fields = ("artifact_id", "content_sha256", "revision")
    return [field for field in fields if record[f"current_{field}"] != artifact[field]]


class OperatorRecordContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validators = {
            name: Draft202012Validator(
                load_json(OPERATOR_DIR / f"{name}.schema.json"),
                format_checker=FormatChecker(),
            )
            for name in SCHEMA_NAMES
        }

    def assert_valid(self, schema_name, fixture_name):
        errors = list(self.validators[schema_name].iter_errors(load_json(FIXTURE_DIR / fixture_name)))
        self.assertEqual([], errors, [error.message for error in errors])

    def test_positive_operator_records_are_schema_valid(self):
        fixtures = {
            "operator-task": "valid-operator-task.json",
            "blocker-record": "valid-blocker-record.json",
            "revision-request": "valid-revision-request.json",
            "workflow-defect": "valid-workflow-defect.json",
            "escalation-record": "valid-escalation-record.json",
            "resolution-record": "valid-resolution-record.json",
        }
        for schema_name, fixture_name in fixtures.items():
            with self.subTest(schema_name=schema_name):
                self.assert_valid(schema_name, fixture_name)

    def test_all_operator_schemas_are_closed_draft_2020_12_contracts(self):
        for schema_name in SCHEMA_NAMES:
            schema = load_json(OPERATOR_DIR / f"{schema_name}.schema.json")
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
            self.assertEqual(
                f"https://heartweb.example/schema/operator/{schema_name}.schema.json",
                schema["$id"],
            )
            self.assertFalse(schema["additionalProperties"])

    def test_operator_task_rejects_unknown_fields_wrong_ids_and_missing_action(self):
        validator = self.validators["operator-task"]
        cases = (
            "negative-operator-unknown-field.json",
            "negative-operator-wrong-ids.json",
            "negative-operator-missing-operator-action.json",
        )
        for fixture_name in cases:
            with self.subTest(fixture_name=fixture_name):
                self.assertTrue(list(validator.iter_errors(load_json(FIXTURE_DIR / fixture_name))))

    def test_workflow_defect_rejects_invalid_status(self):
        errors = list(
            self.validators["workflow-defect"].iter_errors(
                load_json(FIXTURE_DIR / "negative-workflow-defect-invalid-status.json")
            )
        )
        self.assertTrue(errors)
        self.assertTrue(any(list(error.absolute_path) == ["status"] for error in errors))

    def test_revision_request_detects_stale_artifact_linkage(self):
        record = load_json(FIXTURE_DIR / "negative-revision-request-stale-artifact.json")
        self.assertEqual([], list(self.validators["revision-request"].iter_errors(record)))
        self.assertEqual(["content_sha256"], stale_artifact_errors(record))


if __name__ == "__main__":
    unittest.main()
