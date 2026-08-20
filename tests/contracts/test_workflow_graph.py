#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / "standards" / "workflow"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "workflow"
CANONICAL_ROUTE = ["0", "1", "1b", "1c", "2", "3", "4a", "4b"]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class WorkflowGraphContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_json(WORKFLOW_DIR / "workflow-graph.schema.json")
        cls.graph = load_json(WORKFLOW_DIR / "workflow-graph.json")
        cls.validator = Draft202012Validator(cls.schema)

    def test_canonical_graph_is_schema_valid_and_has_exact_initial_route(self):
        errors = list(self.validator.iter_errors(self.graph))
        self.assertEqual([], errors, [error.message for error in errors])
        self.assertEqual(CANONICAL_ROUTE, self.graph["initial_route"])
        self.assertEqual(
            list(zip(CANONICAL_ROUTE, CANONICAL_ROUTE[1:])),
            [(edge["from_step_id"], edge["to_step_id"]) for edge in self.graph["initial_edges"]],
        )

    def test_post_publication_sideflow_is_not_an_initial_route_edge(self):
        sideflow = self.graph["post_publication_sideflows"][0]
        self.assertEqual("3b", sideflow["step_id"])
        self.assertEqual("post_publication", sideflow["trigger"])
        self.assertEqual([30, 60, 90], sideflow["days_after_publication"])
        initial_edges = {(edge["from_step_id"], edge["to_step_id"]) for edge in self.graph["initial_edges"]}
        self.assertNotIn(("3", "3b"), initial_edges)

    def test_illegal_initial_3_to_3b_edge_has_structured_schema_failure(self):
        invalid_graph = load_json(FIXTURE_DIR / "invalid-initial-3-to-3b-graph.json")
        errors = list(self.validator.iter_errors(invalid_graph))
        self.assertTrue(errors)
        structural_errors = [{"path": list(error.absolute_path), "message": error.message} for error in errors]
        self.assertTrue(any(error["path"] == ["initial_edges", 5, "to_step_id"] for error in structural_errors))
        self.assertTrue(any("4a" in error["message"] for error in structural_errors))

    def test_all_object_contracts_are_closed_and_use_draft_2020_12(self):
        schema_paths = list((REPO_ROOT / "standards").glob("workflow/*.json"))
        schema_paths.extend((REPO_ROOT / "standards").glob("runtime/*.schema.json"))
        for path in schema_paths:
            document = load_json(path)
            if path.name.endswith(".schema.json"):
                self.assertEqual("https://json-schema.org/draft/2020-12/schema", document["$schema"])
                self.assertTrue(document["$id"].startswith("https://heartweb.example/schema/"))
                self.assertFalse(document.get("additionalProperties", True), path)


if __name__ == "__main__":
    unittest.main()
