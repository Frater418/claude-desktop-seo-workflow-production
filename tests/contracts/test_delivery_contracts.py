from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from services.delivery.contract_validation import validate_delivery_contracts


ROOT = Path(__file__).resolve().parents[2]
DELIVERY_DIR = ROOT / "standards" / "delivery"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "delivery"
SCHEMA_NAMES = (
    "delivery-package-record",
    "delivery-export-request",
    "delivery-export-result",
    "role-handoff-manifest",
    "notion-import-manifest",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def assert_closed_objects(test_case: unittest.TestCase, value, label: str) -> None:
    if isinstance(value, dict):
        if value.get("type") == "object":
            test_case.assertIs(value.get("additionalProperties"), False, label)
        for key, child in value.items():
            assert_closed_objects(test_case, child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_closed_objects(test_case, child, f"{label}[{index}]")


class DeliveryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {
            name: load_json(DELIVERY_DIR / f"{name}.schema.json") for name in SCHEMA_NAMES
        }
        cls.validators = {
            name: Draft202012Validator(schema, format_checker=FormatChecker())
            for name, schema in cls.schemas.items()
        }

    def assert_valid_fixture(self, schema_name: str, fixture_name: str) -> None:
        value = load_json(FIXTURE_DIR / fixture_name)
        errors = list(self.validators[schema_name].iter_errors(value))
        self.assertEqual([], errors, [error.message for error in errors])

    def assert_semantically_valid(self, package_name: str, role_name: str, notion_name: str) -> None:
        result = validate_delivery_contracts(
            load_json(FIXTURE_DIR / package_name),
            [load_json(FIXTURE_DIR / role_name)],
            load_json(FIXTURE_DIR / notion_name),
        )
        self.assertTrue(result.valid, result.errors)

    def assert_invalid_fixture(self, schema_name: str, fixture_name: str, validator: str) -> None:
        errors = list(self.validators[schema_name].iter_errors(load_json(FIXTURE_DIR / fixture_name)))
        self.assertTrue(errors)
        self.assertIn(validator, {error.validator for error in errors})

    def test_schemas_are_closed_draft_2020_12_contracts(self) -> None:
        ids = []
        for name, schema in self.schemas.items():
            with self.subTest(schema_name=name):
                Draft202012Validator.check_schema(schema)
                self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
                self.assertEqual(
                    f"https://heartweb.example/schema/delivery/{name}.schema.json",
                    schema["$id"],
                )
                assert_closed_objects(self, schema, name)
                ids.append(schema["$id"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_positive_checkpoint_and_final_delivery_records_validate(self) -> None:
        self.assert_valid_fixture("delivery-package-record", "positive-checkpoint-package.json")
        self.assert_valid_fixture("delivery-package-record", "positive-final-package.json")

    def test_positive_delivery_supporting_manifests_validate(self) -> None:
        fixtures = {
            "delivery-export-request": "positive-export-request.json",
            "delivery-export-result": "positive-export-result.json",
            "role-handoff-manifest": "positive-role-handoff.json",
            "notion-import-manifest": "positive-notion-import.json",
        }
        for schema_name, fixture_name in fixtures.items():
            with self.subTest(schema_name=schema_name):
                self.assert_valid_fixture(schema_name, fixture_name)

    def test_complete_delivery_fixture_is_semantically_valid(self) -> None:
        self.assert_semantically_valid("positive-final-package.json", "positive-role-handoff.json", "positive-notion-import.json")

    def test_semantic_validator_rejects_mismatched_identity_and_duplicate_references(self) -> None:
        package = load_json(FIXTURE_DIR / "positive-final-package.json")
        role = load_json(FIXTURE_DIR / "positive-role-handoff.json")
        notion = load_json(FIXTURE_DIR / "positive-notion-import.json")
        role["source_records"][0]["tenant_id"] = "tenant-other"
        notion["relations"].append(copy.deepcopy(notion["relations"][0]))
        result = validate_delivery_contracts(package, [role], notion)
        self.assertFalse(result.valid)
        self.assertIn("DELIVERY_SOURCE_SCOPE_INVALID", {error.code for error in result.errors})
        self.assertIn("DELIVERY_DUPLICATE_RELATION", {error.code for error in result.errors})

    def test_semantic_validator_rejects_dangling_relation_and_duplicate_external_task_id(self) -> None:
        package = load_json(FIXTURE_DIR / "positive-final-package.json")
        role = load_json(FIXTURE_DIR / "positive-role-handoff.json")
        notion = load_json(FIXTURE_DIR / "positive-notion-import.json")
        notion["relations"][0]["to_record_id"] = "task-missing-0001"
        notion["task_rows"].append(copy.deepcopy(notion["task_rows"][0]))
        result = validate_delivery_contracts(package, [role], notion)
        self.assertFalse(result.valid)
        self.assertIn("DELIVERY_RELATION_DANGLING", {error.code for error in result.errors})
        self.assertIn("DELIVERY_DUPLICATE_EXTERNAL_ID", {error.code for error in result.errors})

    def test_semantic_validator_accepts_idempotent_positive_replay(self) -> None:
        self.assert_semantically_valid("positive-final-package.json", "positive-role-handoff.json", "positive-notion-import.json")

    def test_notion_rows_reject_core_mutation_and_history_edits(self) -> None:
        notion = load_json(FIXTURE_DIR / "positive-notion-import.json")
        implementation = copy.deepcopy(notion)
        implementation["task_rows"][1]["resume_run"] = "run-demo-0001"
        history = copy.deepcopy(notion)
        history["task_rows"][0]["status"] = "done"
        completion = copy.deepcopy(notion)
        completion["task_rows"][1]["gate_approval"] = "approval-demo-0001"
        for value in (implementation, history, completion):
            errors = list(self.validators["notion-import-manifest"].iter_errors(value))
            self.assertTrue(any(error.validator in {"additionalProperties", "not"} for error in errors))

    def test_notion_manifest_rejects_incomplete_performance_checkpoint_set(self) -> None:
        notion = load_json(FIXTURE_DIR / "positive-notion-import.json")
        notion["performance_checkpoint_rows"] = notion["performance_checkpoint_rows"][:2]
        errors = list(self.validators["notion-import-manifest"].iter_errors(notion))
        self.assertTrue(any(error.validator in {"minItems", "contains"} for error in errors))

    def test_semantic_validator_rejects_customer_project_and_task_reference_gaps(self) -> None:
        package = load_json(FIXTURE_DIR / "positive-final-package.json")
        role = load_json(FIXTURE_DIR / "positive-role-handoff.json")
        notion = load_json(FIXTURE_DIR / "positive-notion-import.json")
        notion["customer_rows"].append(copy.deepcopy(notion["customer_rows"][0]))
        notion["project_rows"][0]["customer_external_id"] = "customer-missing"
        notion["assignment_rows"][0]["task_external_id"] = "task-missing-0001"
        result = validate_delivery_contracts(package, [role], notion)
        self.assertFalse(result.valid)
        self.assertIn("DELIVERY_DUPLICATE_EXTERNAL_ID", {error.code for error in result.errors})
        self.assertIn("DELIVERY_ROW_REFERENCE_DANGLING", {error.code for error in result.errors})

    def test_package_rejects_cross_tenant_source_identity(self) -> None:
        self.assert_invalid_fixture(
            "delivery-package-record", "invalid-cross-tenant-package.json", "required"
        )

    def test_package_rejects_path_escape_and_absolute_paths(self) -> None:
        self.assert_invalid_fixture("delivery-package-record", "invalid-path-escape-package.json", "pattern")
        self.assert_invalid_fixture("delivery-package-record", "invalid-absolute-path-package.json", "pattern")

    def test_package_rejects_missing_invalid_hash_and_duplicate_path(self) -> None:
        self.assert_invalid_fixture("delivery-package-record", "invalid-missing-hash-package.json", "required")
        self.assert_invalid_fixture("delivery-package-record", "invalid-hash-package.json", "pattern")
        self.assert_invalid_fixture("delivery-package-record", "invalid-duplicate-path-package.json", "uniqueItems")

    def test_final_package_rejects_missing_released_deliverables(self) -> None:
        errors = list(
            self.validators["delivery-package-record"].iter_errors(
                load_json(FIXTURE_DIR / "invalid-premature-final-package.json")
            )
        )
        self.assertTrue(errors)
        self.assertTrue(
            any(error.validator == "maxItems" and list(error.absolute_path) == ["missing_deliverables"] for error in errors),
            [error.message for error in errors],
        )

    def test_final_export_request_excludes_drafts(self) -> None:
        request = load_json(FIXTURE_DIR / "positive-export-request.json")
        request["scope"] = "final"
        errors = list(self.validators["delivery-export-request"].iter_errors(request))
        self.assertTrue(any(error.validator == "const" for error in errors))

    def test_delivery_contracts_reject_authority_and_live_integration_fields(self) -> None:
        package = load_json(FIXTURE_DIR / "positive-checkpoint-package.json")
        package["workflow_status"] = "released"
        request = load_json(FIXTURE_DIR / "positive-export-request.json")
        request["notion_live"] = True
        result = load_json(FIXTURE_DIR / "positive-export-result.json")
        result["n8n_job_id"] = "job-forbidden"
        for schema_name, value in (
            ("delivery-package-record", package),
            ("delivery-export-request", request),
            ("delivery-export-result", result),
        ):
            with self.subTest(schema_name=schema_name):
                errors = list(self.validators[schema_name].iter_errors(copy.deepcopy(value)))
                self.assertTrue(any(error.validator == "additionalProperties" for error in errors))


if __name__ == "__main__":
    unittest.main()
