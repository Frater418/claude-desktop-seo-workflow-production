#!/usr/bin/env python3
import copy
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = REPO_ROOT / "standards" / "runtime"
WORKFLOW_DIR = REPO_ROOT / "standards" / "workflow"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "workflow"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def schema_errors(validator, command):
    errors = []
    for error in validator.iter_errors(command):
        path = list(error.absolute_path)
        if error.validator == "required":
            missing_property = next(property_name for property_name in error.validator_value if property_name not in error.instance)
            path.append(missing_property)
        errors.append({"code": "ERR_SCHEMA_VALIDATION", "path": path, "message": error.message})
    return errors


def state_errors(command, graph, current_revision, now):
    errors = []
    initial_edges = {(edge["from_step_id"], edge["to_step_id"]) for edge in graph["initial_edges"]}
    if (command["from_step_id"], command["to_step_id"]) not in initial_edges:
        errors.append({"code": "ERR_TRANSITION_NOT_ALLOWED", "path": ["to_step_id"], "message": "transition is not an initial workflow edge"})
    if command["expected_revision"] != current_revision:
        errors.append({"code": "ERR_STALE_REVISION", "path": ["expected_revision"], "message": "expected revision does not match current revision"})
    if command["operation"] in {"approve", "complete"} and "approval" in command and command.get("artifacts"):
        artifact = command["artifacts"][0]
        approval = command["approval"]
        quality_gate = command.get("quality_gate", {})
        approval_expiry = datetime.fromisoformat(approval["expires_at"].replace("Z", "+00:00"))
        if approval_expiry <= now or approval["artifact_id"] != artifact["artifact_id"] or approval["artifact_revision"] != artifact["revision"] or approval["artifact_sha256"] != artifact["content_sha256"]:
            errors.append({"code": "ERR_APPROVAL_STALE", "path": ["approval"], "message": "approval is not bound to the current artifact revision and hash"})
        if quality_gate.get("artifact_id") != artifact["artifact_id"] or quality_gate.get("artifact_sha256") != artifact["content_sha256"]:
            errors.append({"code": "ERR_GATE_REQUIRED", "path": ["quality_gate"], "message": "passed quality gate is not bound to the artifact"})
    return errors


class TransitionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema = load_json(RUNTIME_DIR / "transition-command.schema.json")
        cls.validator = Draft202012Validator(schema, format_checker=FormatChecker())
        cls.graph = load_json(WORKFLOW_DIR / "workflow-graph.json")
        cls.now = datetime(2026, 8, 19, 13, 0, tzinfo=timezone.utc)

    def test_valid_transition_is_schema_and_state_valid(self):
        command = load_json(FIXTURE_DIR / "valid-transition-command.json")
        self.assertEqual([], schema_errors(self.validator, command))
        self.assertEqual([], state_errors(command, self.graph, 7, self.now))

    def test_schema_rejects_missing_artifact_hash_and_reviewer_with_paths(self):
        command = load_json(FIXTURE_DIR / "valid-transition-command.json")
        missing_artifact = copy.deepcopy(command)
        del missing_artifact["artifacts"]
        missing_hash = copy.deepcopy(command)
        del missing_hash["output_hash"]
        missing_reviewer = copy.deepcopy(command)
        del missing_reviewer["approval"]["reviewer_id"]
        cases = ((missing_artifact, ["artifacts"]), (missing_hash, ["output_hash"]), (missing_reviewer, ["approval"]))
        for invalid_command, expected_path_prefix in cases:
            errors = schema_errors(self.validator, invalid_command)
            self.assertTrue(errors)
            self.assertTrue(any(error["path"][:len(expected_path_prefix)] == expected_path_prefix for error in errors), errors)

    def test_stale_approval_has_stable_state_error(self):
        command = load_json(FIXTURE_DIR / "stale-approval-transition-command.json")
        self.assertEqual([], schema_errors(self.validator, command))
        errors = state_errors(command, self.graph, 7, self.now)
        self.assertEqual(["ERR_APPROVAL_STALE"], [error["code"] for error in errors])
        self.assertEqual(["approval"], errors[0]["path"])

    def test_illegal_initial_3_to_3b_transition_has_stable_state_error(self):
        command = load_json(FIXTURE_DIR / "illegal-initial-transition-command.json")
        self.assertEqual([], schema_errors(self.validator, command))
        errors = state_errors(command, self.graph, 7, self.now)
        self.assertEqual("ERR_TRANSITION_NOT_ALLOWED", errors[0]["code"])
        self.assertEqual(["to_step_id"], errors[0]["path"])


if __name__ == "__main__":
    unittest.main()
