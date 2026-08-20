#!/usr/bin/env python3
import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATIONS_DIR = REPO_ROOT / "standards" / "integrations"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "integrations"
EVENT_TYPES = {
    "project.created",
    "run.started",
    "step.blocked",
    "artifact.created",
    "gate.ready",
    "gate.approved",
    "gate.rejected",
    "task.created",
    "task.resolved",
    "defect.created",
    "escalation.created",
    "run.resumed",
    "release.created",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class IntegrationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.event_schema = load_json(INTEGRATIONS_DIR / "workflow-event.schema.json")
        cls.catalog = load_json(INTEGRATIONS_DIR / "event-catalog.json")
        cls.notion_schema = load_json(INTEGRATIONS_DIR / "notion-projection.schema.json")
        cls.n8n_schema = load_json(INTEGRATIONS_DIR / "n8n-command.schema.json")
        cls.event_validator = Draft202012Validator(cls.event_schema, format_checker=FormatChecker())
        cls.notion_validator = Draft202012Validator(cls.notion_schema, format_checker=FormatChecker())
        cls.n8n_validator = Draft202012Validator(cls.n8n_schema, format_checker=FormatChecker())

    def assert_valid(self, validator, instance):
        errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))
        self.assertEqual([], errors, [error.message for error in errors])

    def assert_invalid(self, validator, instance):
        self.assertTrue(list(validator.iter_errors(instance)))

    def test_schemas_are_closed_draft_2020_12_contracts(self):
        for schema in (self.event_schema, self.notion_schema, self.n8n_schema):
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
            self.assertTrue(schema["$id"].startswith("https://heartweb.example/schema/integrations/"))
            self.assertFalse(schema["additionalProperties"])

    def test_event_catalog_covers_exactly_the_required_typed_events(self):
        self.assertEqual(EVENT_TYPES, set(self.catalog["events"]))
        self.assertEqual(EVENT_TYPES, set(self.event_schema["properties"]["event_type"]["enum"]))

    def test_simulated_event_fixtures_are_valid_and_cannot_masquerade_as_live(self):
        event_paths = sorted((FIXTURE_DIR / "workflow-events").glob("*.json"))
        self.assertEqual(EVENT_TYPES, {load_json(path)["event_type"] for path in event_paths})
        for path in event_paths:
            event = load_json(path)
            self.assertEqual("simulated", event["integration_mode"], path)
            self.assert_valid(self.event_validator, event)
            claimed_live = copy.deepcopy(event)
            claimed_live["integration_mode"] = "live"
            self.assert_invalid(self.event_validator, claimed_live)

    def test_event_schema_rejects_unknown_payload_fields_and_invalid_identity_binding(self):
        event = load_json(FIXTURE_DIR / "workflow-events" / "artifact-created.json")
        unknown_field = copy.deepcopy(event)
        unknown_field["payload"]["unapproved"] = True
        invalid_identity = copy.deepcopy(event)
        invalid_identity["identity"]["run_id"] = "run-invalid"
        self.assert_invalid(self.event_validator, unknown_field)
        self.assert_invalid(self.event_validator, invalid_identity)

    def test_notion_projection_is_operational_only_and_field_edits_cannot_bypass_transition_service(self):
        projection = load_json(FIXTURE_DIR / "notion" / "project-projection.json")
        self.assertEqual("simulated", projection["integration_mode"])
        self.assertEqual("operative_projection", projection["projection_role"])
        self.assertEqual("transition_service", projection["state_authority"])
        self.assertFalse(projection["atomic_state_writer"])
        self.assert_valid(self.notion_validator, projection)
        field_edit = copy.deepcopy(projection)
        field_edit["records"][0]["projected_status"] = "completed"
        self.assert_valid(self.notion_validator, field_edit)
        self.assertEqual("transition_service", field_edit["state_authority"])
        self.assertFalse(field_edit["atomic_state_writer"])
        edited_projection = copy.deepcopy(projection)
        edited_projection["state_authority"] = "notion"
        edited_projection["atomic_state_writer"] = True
        self.assert_invalid(self.notion_validator, edited_projection)
        claimed_live = copy.deepcopy(projection)
        claimed_live["integration_mode"] = "live"
        self.assert_invalid(self.notion_validator, claimed_live)
        live_projection = copy.deepcopy(projection)
        live_projection["integration_mode"] = "live"
        del live_projection["simulation_id"]
        live_projection["live_connection_id"] = "live-local-notion-001"
        self.assert_valid(self.notion_validator, live_projection)

    def test_n8n_commands_are_simulated_idempotent_and_cannot_approve_or_complete(self):
        command = load_json(FIXTURE_DIR / "n8n" / "wait-for-gate-command.json")
        self.assertEqual("simulated", command["integration_mode"])
        for field in ("idempotency_key", "correlation_id", "expected_revision", "integration_mode"):
            self.assertIn(field, command)
        self.assert_valid(self.n8n_validator, command)
        for forbidden_type in ("approve_gate", "complete_run"):
            forbidden_command = copy.deepcopy(command)
            forbidden_command["command_type"] = forbidden_type
            self.assert_invalid(self.n8n_validator, forbidden_command)
        claimed_live = copy.deepcopy(command)
        claimed_live["integration_mode"] = "live"
        self.assert_invalid(self.n8n_validator, claimed_live)
        live_command = copy.deepcopy(command)
        live_command["integration_mode"] = "live"
        del live_command["simulation_id"]
        live_command["live_connection_id"] = "live-local-n8n-001"
        self.assert_valid(self.n8n_validator, live_command)


if __name__ == "__main__":
    unittest.main()
