#!/usr/bin/env python3
import copy
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from services.integration_contracts.notion_graph import (
    NotionGraphSchemas,
    NotionGraphTarget,
    validate_notion_graph,
)


INTEGRATIONS_DIR = REPO_ROOT / "standards" / "integrations"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "integrations" / "v2"
V1_FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "integrations"
SCHEMA_NAMES = {
    "event": "workflow-event-v2.schema.json",
    "record_map": "notion-record-v2.schema.json",
    "projection": "notion-projection-v2.schema.json",
    "proposal": "notion-proposal.schema.json",
    "snapshot": "notion-snapshot.schema.json",
    "simulation": "n8n-simulation-state.schema.json",
    "wait": "n8n-wait-subscription.schema.json",
    "retry": "n8n-retry-entry.schema.json",
    "dlq": "n8n-dlq-entry.schema.json",
}
EVENT_TYPES = {
    "project.created", "run.started", "step.blocked", "artifact.created", "gate.ready",
    "gate.approved", "gate.rejected", "task.created", "task.resolved", "defect.created",
    "escalation.created", "run.resumed", "release.created", "assignment.created",
    "approval.recorded", "blocker.resolved", "performance.checkpoint_due", "metric.recorded",
    "adjustment.proposed", "integration.delivery_failed", "integration.conflict_detected",
}
RECORD_TYPES = {
    "customer", "project", "run", "step", "task", "assignment", "artifact", "gate",
    "review", "approval", "blocker", "defect", "escalation", "performance_checkpoint",
    "metric", "adjustment_proposal", "integration_status",
}
ARCHETYPES = {
    "cross-border-finance.json", "english-international-resort-ota-social.json",
    "international-speaker-brand.json", "local-medical.json", "national-b2b.json",
    "programmatic-local-satellite-network.json", "regional-care.json",
    "regional-solo-expert.json", "sensitive-education-retreat.json",
    "sri-lankan-ayurveda-dach.json",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class IntegrationContractV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = {
            name: load_json(INTEGRATIONS_DIR / filename)
            for name, filename in SCHEMA_NAMES.items()
        }
        cls.registry = Registry().with_resources(
            (schema["$id"], Resource.from_contents(schema))
            for schema in cls.schemas.values()
        )
        cls.validators = {
            name: Draft202012Validator(
                schema, registry=cls.registry, format_checker=FormatChecker()
            )
            for name, schema in cls.schemas.items()
        }
        cls.notion_graph_schemas = NotionGraphSchemas(
            record_map=cls.schemas["record_map"],
            projection=cls.schemas["projection"],
            snapshot=cls.schemas["snapshot"],
        )

    def assert_valid(self, schema_name, instance):
        errors = sorted(
            self.validators[schema_name].iter_errors(instance),
            key=lambda error: list(error.absolute_path),
        )
        self.assertEqual([], errors, [error.message for error in errors])

    def assert_invalid(self, schema_name, instance):
        self.assertTrue(list(self.validators[schema_name].iter_errors(instance)))
        graph_target = {
            "projection": NotionGraphTarget.PROJECTION,
            "snapshot": NotionGraphTarget.SNAPSHOT,
        }.get(schema_name)
        if graph_target is not None:
            self.assertFalse(validate_notion_graph(instance, graph_target, self.notion_graph_schemas).valid)

    def assert_graph_valid(self, instance, target_kind):
        result = validate_notion_graph(
            instance, target_kind, self.notion_graph_schemas
        )
        self.assertTrue(result.valid, [error.code for error in result.errors])

    def test_v2_schemas_are_closed_and_have_unique_stable_ids(self):
        schema_ids = set()
        for schema in self.schemas.values():
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
            self.assertFalse(schema["additionalProperties"])
            self.assertTrue(schema["$id"].startswith("https://heartweb.example/schema/integrations/"))
            schema_ids.add(schema["$id"])
        self.assertEqual(len(self.schemas), len(schema_ids))

    def test_event_catalog_has_exact_v2_parity_and_purposes(self):
        catalog = load_json(INTEGRATIONS_DIR / "event-catalog-v2.json")
        self.assertEqual(EVENT_TYPES, set(catalog["events"]))
        self.assertEqual(EVENT_TYPES, set(catalog["purposes"]))
        self.assertEqual(EVENT_TYPES, set(self.schemas["event"]["properties"]["event_type"]["enum"]))

    def test_all_v2_events_have_closed_payloads_and_simulated_fixtures(self):
        events = load_json(FIXTURE_DIR / "positive-workflow-events.json")
        self.assertEqual(EVENT_TYPES, {event["event_type"] for event in events})
        for event in events:
            self.assertEqual("2.0.0", event["schema_version"])
            self.assertEqual("simulated", event["integration_mode"])
            self.assertIn("simulation_id", event)
            self.assertNotIn("live_connection_id", event)
            self.assert_valid("event", event)
            claimed_live = copy.deepcopy(event)
            claimed_live["integration_mode"] = "live"
            self.assert_invalid("event", claimed_live)
        payload_schemas = [
            definition for name, definition in self.schemas["event"]["$defs"].items()
            if name.endswith("Payload")
        ]
        self.assertEqual(len(EVENT_TYPES), len(payload_schemas))
        self.assertTrue(all(not definition["additionalProperties"] for definition in payload_schemas))

    def test_projection_covers_exact_record_types_and_requires_source_provenance(self):
        projection = load_json(FIXTURE_DIR / "positive-notion-projection.json")
        self.assertEqual(
            RECORD_TYPES,
            {record["record_type"] for record in projection["records"].values()},
        )
        self.assertEqual("transition_service", projection["state_authority"])
        self.assertFalse(projection["atomic_state_writer"])
        self.assert_valid("projection", projection)
        self.assert_graph_valid(projection, NotionGraphTarget.PROJECTION)
        missing_revision = copy.deepcopy(projection)
        del missing_revision["records"]["customer-00000001"]["source_revision"]
        self.assert_invalid("projection", missing_revision)
        duplicate_relation = copy.deepcopy(projection)
        duplicate_relation["records"]["customer-00000001"]["relations"] *= 2
        self.assert_invalid("projection", duplicate_relation)
        direct_write = copy.deepcopy(projection)
        direct_write["records"]["customer-00000001"]["canonical_status"] = "completed"
        self.assert_invalid("projection", direct_write)
        unknown_record = copy.deepcopy(projection)
        unknown_record["records"]["unknown-00000001"] = unknown_record["records"].pop("project-00000001")
        self.assert_invalid("projection", unknown_record)
        mismatched_type = copy.deepcopy(projection)
        mismatched_type["records"]["project-00000001"]["record_type"] = "customer"
        self.assert_invalid("projection", mismatched_type)
        record_entries = list(projection["records"].items())
        duplicate_attempt = [*record_entries, record_entries[0]]
        with self.assertRaises(AssertionError):
            self.assertEqual(len(duplicate_attempt), len({record_id for record_id, _ in duplicate_attempt}))

    def test_notion_proposals_are_human_intent_not_canonical_writes(self):
        proposal = load_json(FIXTURE_DIR / "positive-notion-proposal.json")
        self.assert_valid("proposal", proposal)
        self.assertEqual("approve", proposal["intent"])
        direct_write = copy.deepcopy(proposal)
        direct_write["canonical_status"] = "completed"
        self.assert_invalid("proposal", direct_write)

    def test_snapshot_is_simulated_non_authoritative_materialization(self):
        snapshot = load_json(FIXTURE_DIR / "positive-notion-snapshot.json")
        self.assert_valid("snapshot", snapshot)
        self.assert_graph_valid(snapshot, NotionGraphTarget.SNAPSHOT)
        self.assertFalse(snapshot["atomic_state_writer"])
        claimed_live = copy.deepcopy(snapshot)
        claimed_live["integration_mode"] = "live"
        self.assert_invalid("snapshot", claimed_live)

    def test_snapshot_rejects_array_and_untyped_records(self):
        snapshot = load_json(FIXTURE_DIR / "positive-notion-snapshot.json")
        array_snapshot = copy.deepcopy(snapshot)
        array_snapshot["records"] = [snapshot["records"]["project-00000001"]]
        self.assert_invalid("snapshot", array_snapshot)
        untyped_record = copy.deepcopy(snapshot)
        untyped_record["records"] = {"external-00000001": snapshot["records"]["project-00000001"]}
        untyped_record["records"]["external-00000001"]["record_type"] = "untyped_external_record"
        self.assert_invalid("snapshot", untyped_record)

    def test_projection_uses_a_shared_stable_record_map_contract(self):
        records = self.schemas["projection"]["properties"]["records"]
        snapshot_records = self.schemas["snapshot"]["properties"]["records"]
        self.assertEqual(
            "https://heartweb.example/schema/integrations/notion-record-v2.schema.json",
            records.get("$ref"),
        )
        self.assertEqual(records["$ref"], snapshot_records.get("$ref"))

    def test_n8n_retry_and_dlq_entries_require_bounded_provenance(self):
        simulation = load_json(FIXTURE_DIR / "positive-n8n-simulation-state.json")
        for field in ("tenant_id", "project_id"):
            missing_scope = copy.deepcopy(simulation)
            del missing_scope[field]
            self.assert_invalid("simulation", missing_scope)
        simulation["retry_policy"]["max_attempts"] = 5
        self.assert_invalid("simulation", simulation)
        retry = load_json(FIXTURE_DIR / "positive-n8n-retry-entry.json")
        retry["max_attempts"] = 5
        self.assert_invalid("retry", retry)
        retry["max_attempts"] = 3
        retry["attempt"] = 3
        self.assert_invalid("retry", retry)
        dlq = load_json(FIXTURE_DIR / "positive-n8n-dlq-entry.json")
        dlq["attempt"] = 1
        self.assert_invalid("dlq", dlq)
        dlq = load_json(FIXTURE_DIR / "positive-n8n-dlq-entry.json")
        del dlq["step_id"]
        self.assert_invalid("dlq", dlq)
        dlq = load_json(FIXTURE_DIR / "positive-n8n-dlq-entry.json")
        del dlq["expected_revision"]
        self.assert_invalid("dlq", dlq)
        for schema_name, filename, field in (
            ("retry", "positive-n8n-retry-entry.json", "first_failed_at"),
            ("retry", "positive-n8n-retry-entry.json", "original_command_sha256"),
            ("dlq", "positive-n8n-dlq-entry.json", "original_command_sha256"),
        ):
            missing_provenance = load_json(FIXTURE_DIR / filename)
            del missing_provenance[field]
            self.assert_invalid(schema_name, missing_provenance)

    def test_n8n_contracts_bound_retry_and_prohibit_state_authority(self):
        fixtures = {
            "simulation": "positive-n8n-simulation-state.json",
            "wait": "positive-n8n-wait-subscription.json",
            "retry": "positive-n8n-retry-entry.json",
            "dlq": "positive-n8n-dlq-entry.json",
        }
        for schema_name, filename in fixtures.items():
            instance = load_json(FIXTURE_DIR / filename)
            self.assert_valid(schema_name, instance)
            self.assertEqual("simulated", instance["integration_mode"])
            self.assertNotIn("live_connection_id", instance)
        simulation = load_json(FIXTURE_DIR / fixtures["simulation"])
        self.assertEqual([30, 60, 90], simulation["confirmed_checkpoint_days"])
        for forbidden_command in ("approve_gate", "complete_run"):
            invalid = copy.deepcopy(simulation)
            invalid["command_queue"][0]["command_type"] = forbidden_command
            self.assert_invalid("simulation", invalid)

    def test_negative_fixtures_cover_the_required_contract_boundaries(self):
        for path in sorted(FIXTURE_DIR.glob("negative-*.json")):
            fixture = load_json(path)
            self.assert_invalid(fixture["schema"], fixture["instance"])

    def test_v2_matrix_references_all_ten_client_neutral_archetypes(self):
        matrix = load_json(FIXTURE_DIR / "positive-archetype-matrix.json")
        self.assertEqual(ARCHETYPES, {entry["source_fixture"] for entry in matrix["archetypes"]})
        self.assertEqual({"standard", "international_multilingual", "regulated_local"}, set(matrix["variants"]))
        for entry in matrix["archetypes"]:
            self.assertNotIn("customer_name", entry)
            self.assertNotIn("customer_id", entry)

    def test_v1_schemas_and_fixtures_remain_compatible(self):
        v1_event = load_json(INTEGRATIONS_DIR / "workflow-event.schema.json")
        v1_projection = load_json(INTEGRATIONS_DIR / "notion-projection.schema.json")
        v1_n8n = load_json(INTEGRATIONS_DIR / "n8n-command.schema.json")
        pairs = (
            (v1_event, V1_FIXTURE_DIR / "workflow-events" / "artifact-created.json"),
            (v1_projection, V1_FIXTURE_DIR / "notion" / "project-projection.json"),
            (v1_n8n, V1_FIXTURE_DIR / "n8n" / "wait-for-gate-command.json"),
        )
        for schema, fixture_path in pairs:
            errors = Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(load_json(fixture_path))
            self.assertEqual([], list(errors), fixture_path)

    def test_contracts_contain_no_ahd_or_live_client_constants(self):
        for path in [*map(lambda name: INTEGRATIONS_DIR / name, SCHEMA_NAMES.values()), INTEGRATIONS_DIR / "event-catalog-v2.json"]:
            content = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("ahd", content)
            self.assertNotIn("customer-national-b2b", content)


if __name__ == "__main__":
    unittest.main()
