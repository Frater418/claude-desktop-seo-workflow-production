import copy
import json
import unittest
from pathlib import Path

from services.integration_contracts.notion_graph import (
    NotionGraphValidationError,
    NotionGraphTarget,
    NotionGraphSchemas,
    validate_notion_graph,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
INTEGRATIONS_DIR = REPO_ROOT / "standards" / "integrations"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "integrations" / "v2"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def notion_schemas():
    return NotionGraphSchemas(
        record_map=load_json(INTEGRATIONS_DIR / "notion-record-v2.schema.json"),
        projection=load_json(INTEGRATIONS_DIR / "notion-projection-v2.schema.json"),
        snapshot=load_json(INTEGRATIONS_DIR / "notion-snapshot.schema.json"),
    )


class NotionGraphValidatorTests(unittest.TestCase):
    def setUp(self):
        self.schemas = notion_schemas()
        self.projection = load_json(FIXTURE_DIR / "positive-notion-projection.json")
        self.snapshot = load_json(FIXTURE_DIR / "positive-notion-snapshot.json")

    def assert_error_code(self, result, code):
        self.assertFalse(result.valid)
        self.assertIn(code, {error.code for error in result.errors})

    def test_validates_complete_projection_and_snapshot(self):
        projection_result = validate_notion_graph(
            self.projection, NotionGraphTarget.PROJECTION, self.schemas
        )
        snapshot_result = validate_notion_graph(
            self.snapshot, NotionGraphTarget.SNAPSHOT, self.schemas
        )

        self.assertTrue(projection_result.valid)
        self.assertEqual("projection", projection_result.target_kind)
        self.assertEqual(17, projection_result.record_count)
        self.assertTrue(snapshot_result.valid)
        self.assertEqual("snapshot", snapshot_result.target_kind)

    def test_rejects_record_map_key_that_differs_from_subject_id(self):
        invalid_projection = copy.deepcopy(self.projection)
        invalid_projection["records"]["project-copy00001"] = invalid_projection[
            "records"
        ]["project-00000001"]

        result = validate_notion_graph(
            invalid_projection, NotionGraphTarget.PROJECTION, self.schemas
        )

        self.assert_error_code(result, "NOTION_GRAPH_SUBJECT_ID_MISMATCH")

    def test_accepts_distinct_entity_when_key_and_subject_id_change_together(self):
        distinct_projection = copy.deepcopy(self.projection)
        record = distinct_projection["records"].pop("project-00000001")
        record["subject_id"] = "project-distinct01"
        distinct_projection["records"]["project-distinct01"] = record
        for value in distinct_projection["records"].values():
            for relation in value["relations"]:
                if relation["target_record_id"] == "project-00000001":
                    relation["target_record_id"] = "project-distinct01"

        result = validate_notion_graph(
            distinct_projection, NotionGraphTarget.PROJECTION, self.schemas
        )

        self.assertTrue(result.valid)

    def test_rejects_dangling_relation_target(self):
        invalid_projection = copy.deepcopy(self.projection)
        invalid_projection["records"]["customer-00000001"]["relations"][0][
            "target_record_id"
        ] = "project-dangling01"

        result = validate_notion_graph(
            invalid_projection, NotionGraphTarget.PROJECTION, self.schemas
        )

        self.assert_error_code(result, "NOTION_GRAPH_RELATION_TARGET_MISSING")

    def test_rejects_relation_type_to_target_family_mismatch(self):
        invalid_projection = copy.deepcopy(self.projection)
        invalid_projection["records"]["customer-00000001"]["relations"][0][
            "target_record_id"
        ] = "customer-00000001"

        result = validate_notion_graph(
            invalid_projection, NotionGraphTarget.PROJECTION, self.schemas
        )

        self.assert_error_code(result, "NOTION_GRAPH_RELATION_TARGET_TYPE_MISMATCH")

    def test_rejects_duplicate_relation_edge_with_reordered_fields(self):
        invalid_projection = copy.deepcopy(self.projection)
        invalid_projection["records"]["customer-00000001"]["relations"].append(
            {
                "target_record_id": "project-00000001",
                "relation_type": "project",
            }
        )

        result = validate_notion_graph(
            invalid_projection, NotionGraphTarget.PROJECTION, self.schemas
        )

        self.assert_error_code(result, "NOTION_GRAPH_DUPLICATE_EDGE")

    def test_missing_injected_schema_ids_raise_structured_error(self):
        for schema_name in ("record_map", "projection", "snapshot"):
            with self.subTest(schema_name=schema_name):
                invalid_schemas = copy.deepcopy(self.schemas)
                del invalid_schemas[schema_name]["$id"]

                with self.assertRaises(NotionGraphValidationError) as raised:
                    validate_notion_graph(
                        self.projection,
                        NotionGraphTarget.PROJECTION,
                        invalid_schemas,
                    )

                self.assertEqual(
                    "NOTION_GRAPH_SCHEMA_ID_INVALID",
                    raised.exception.error.code,
                )
                self.assertEqual(
                    (schema_name, "$id"),
                    raised.exception.error.path,
                )


if __name__ == "__main__":
    unittest.main()
