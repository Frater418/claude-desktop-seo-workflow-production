from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from services.integration_contracts.notion_graph import NotionGraphTarget, validate_notion_graph
from services.integrations.notion_simulator import (
    NotionContracts,
    NotionSimulationError,
    materialize_events,
    materialize_projection,
    translate_proposal,
)


ROOT = Path(__file__).resolve().parents[1]
INTEGRATIONS = ROOT / "standards" / "integrations"
DOMAINS = ROOT / "tests" / "fixtures" / "domain" / "real-customer-matrix"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def contracts() -> NotionContracts:
    return NotionContracts(
        event_schema=load_json(INTEGRATIONS / "workflow-event-v2.schema.json"),
        event_catalog=load_json(INTEGRATIONS / "event-catalog-v2.json"),
        proposal_schema=load_json(INTEGRATIONS / "notion-proposal.schema.json"),
        graph_schemas={
            "record_map": load_json(INTEGRATIONS / "notion-record-v2.schema.json"),
            "projection": load_json(INTEGRATIONS / "notion-projection-v2.schema.json"),
            "snapshot": load_json(INTEGRATIONS / "notion-snapshot.schema.json"),
        },
    )


def event(event_type: str, event_id: str, revision: int = 1, *, project_id: str = "project-demo", customer_id: str = "customer-demo") -> dict:
    payloads = {
        "project.created": {"customer_id": customer_id, "owner_id": "owner-demo"},
        "run.started": {"attempt": 1, "input_hash": "a" * 64},
        "artifact.created": {"artifact_id": "artifact-demo-0001", "content_sha256": "b" * 64},
        "gate.ready": {"gate_id": "GATE-1"},
        "gate.approved": {"gate_id": "GATE-1", "approval_id": "approval-demo-0001"},
        "gate.rejected": {"gate_id": "GATE-1", "reason": "revision needed"},
        "task.created": {"task_id": "task-demo-0001", "task_type": "review"},
        "assignment.created": {"assignment_id": "assignment-demo-0001", "task_id": "task-demo-0001", "assigned_role": "reviewer"},
        "approval.recorded": {"approval_id": "approval-demo-0001", "gate_id": "GATE-1", "decision": "approved"},
        "step.blocked": {"blocker_id": "blocker-demo-0001", "reason": "evidence missing"},
        "blocker.resolved": {"blocker_id": "blocker-demo-0001", "resolution_id": "resolution-demo-0001"},
        "defect.created": {"defect_id": "defect-demo-0001", "severity": "P2"},
        "escalation.created": {"escalation_id": "escalation-demo-0001", "decision_owner": "business_owner"},
        "performance.checkpoint_due": {"checkpoint_id": "checkpoint-demo-0001", "day_after_publication": 30},
        "metric.recorded": {"metric_id": "metric-demo-0001", "metric_name": "clicks", "value": 4, "unit": "count"},
        "adjustment.proposed": {"proposal_id": "adjustment-demo-0001", "checkpoint_id": "checkpoint-demo-0001", "source_artifact_id": "artifact-demo-0001"},
    }
    return {
        "event_id": event_id,
        "event_type": event_type,
        "schema_version": "2.0.0",
        "occurred_at": f"2026-08-20T00:00:{int(event_id[-2:]):02d}Z",
        "correlation_id": "corr-demo-0001",
        "idempotency_key": f"idem-demo-{event_id[6:]}",
        "identity": {"tenant_id": "tenant-demo", "project_id": project_id, "run_id": "run-demo-0001", "step_id": "1", "revision": revision},
        "integration_mode": "simulated",
        "simulation_id": "sim-demo-0001",
        "payload": payloads[event_type],
    }


def proposal(expected_revision: int) -> dict:
    return {
        "proposal_id": "notion-proposal-demo-0001",
        "schema_version": "2.0.0",
        "integration_mode": "simulated",
        "simulation_id": "sim-demo-0001",
        "submitted_at": "2026-08-20T00:00:00Z",
        "intent": "resume",
        "expected_revision": expected_revision,
        "actor": {"actor_id": "operator-demo", "role": "operator"},
        "correlation_id": "corr-demo-0001",
        "idempotency_key": "idem-demo-proposal-0001",
        "target": {"tenant_id": "tenant-demo", "project_id": "project-demo", "run_id": "run-demo-0001", "step_id": "1"},
    }


class NotionSimulatorTests(unittest.TestCase):
    def test_rejects_live_event_before_projecting(self) -> None:
        invalid = event("project.created", "event-demo-0001")
        invalid["integration_mode"] = "live"
        with self.assertRaisesRegex(NotionSimulationError, "NOTION_SIMULATION_EVENT_INVALID"):
            materialize_events([invalid], contracts())

    def test_rejects_masquerading_and_unknown_catalog_events(self) -> None:
        masquerading = event("project.created", "event-demo-0001")
        masquerading["live_connection_id"] = "live-demo-0001"
        with self.assertRaises(NotionSimulationError):
            materialize_events([masquerading], contracts())
        catalog = contracts()
        catalog.event_catalog["events"] = ["project.created"]
        with self.assertRaisesRegex(NotionSimulationError, "NOTION_SIMULATION_CATALOG_MISMATCH"):
            materialize_events([event("run.started", "event-demo-0002")], catalog)

    def test_materializes_a_schema_valid_relation_graph_without_input_mutation(self) -> None:
        events = [
            event("assignment.created", "event-demo-0008"), event("project.created", "event-demo-0001"),
            event("run.started", "event-demo-0002"), event("task.created", "event-demo-0007"),
            event("artifact.created", "event-demo-0003"), event("gate.ready", "event-demo-0004"),
            event("approval.recorded", "event-demo-0009"), event("step.blocked", "event-demo-0010"),
            event("blocker.resolved", "event-demo-0011"),
            event("defect.created", "event-demo-0012"), event("escalation.created", "event-demo-0013"),
            event("performance.checkpoint_due", "event-demo-0014"), event("metric.recorded", "event-demo-0015"),
            event("adjustment.proposed", "event-demo-0016"),
        ]
        baseline = copy.deepcopy(events)
        snapshot = materialize_events(events, contracts())
        self.assertEqual(snapshot, materialize_events(list(reversed(events)), contracts()))
        self.assertEqual(events, baseline)
        result = validate_notion_graph(snapshot, NotionGraphTarget.SNAPSHOT, contracts().graph_schemas)
        self.assertTrue(result.valid, result.errors)
        projection = materialize_projection(events, contracts())
        self.assertTrue(validate_notion_graph(projection, NotionGraphTarget.PROJECTION, contracts().graph_schemas).valid)
        self.assertEqual("transition_service", snapshot["state_authority"])
        self.assertFalse(snapshot["atomic_state_writer"])
        assignment = snapshot["records"]["assignment-demo-0001"]
        self.assertEqual("assignment", assignment["record_type"])
        self.assertEqual("reviewer", assignment["projected_status"])
        self.assertIn("review-demo-0004", snapshot["records"])
        self.assertEqual("unassigned", snapshot["records"]["task-demo-0001"]["projected_status"])
        self.assertEqual("resolved", snapshot["records"]["blocker-demo-0001"]["projected_status"])

    def test_projects_every_typed_assignment_role_without_defaulting_an_owner(self) -> None:
        for role in ("copywriter", "designer", "developer", "reviewer"):
            assignment = event("assignment.created", "event-demo-0008")
            assignment["payload"]["assigned_role"] = role
            snapshot = materialize_events([event("task.created", "event-demo-0007"), assignment], contracts())
            self.assertEqual(role, snapshot["records"]["assignment-demo-0001"]["projected_status"])

    def test_replay_order_and_stale_revision_are_deterministic(self) -> None:
        project = event("project.created", "event-demo-0001", revision=2)
        replay = copy.deepcopy(project)
        self.assertEqual(materialize_events([project, replay], contracts()), materialize_events([replay, project], contracts()))
        stale = event("project.created", "event-demo-0002", revision=1)
        stale_snapshot = materialize_events([project, stale], contracts())
        self.assertEqual(2, stale_snapshot["records"]["project-demo"]["source_revision"])
        self.assertTrue(stale_snapshot["conflicts"])
        changed = copy.deepcopy(project)
        changed["payload"]["owner_id"] = "owner-other"
        with self.assertRaisesRegex(NotionSimulationError, "NOTION_SIMULATION_EVENT_CONFLICT"):
            materialize_events([project, changed], contracts())

    def test_translates_only_a_stored_current_proposal_to_a_core_intent(self) -> None:
        current = proposal(3)
        intent = translate_proposal(current, 3, contracts().proposal_schema)
        self.assertEqual("core_command_request", intent["request_kind"])
        self.assertEqual("resume", intent["operation"])
        self.assertNotIn("canonical_status", intent)
        with self.assertRaisesRegex(NotionSimulationError, "NOTION_SIMULATION_STALE_PROPOSAL"):
            translate_proposal(proposal(2), 3, contracts().proposal_schema)

    def test_projects_each_neutral_domain_fixture(self) -> None:
        paths = sorted(DOMAINS.glob("*.json"))
        self.assertEqual(10, len(paths))
        for path in paths:
            domain = load_json(path)
            snapshot = materialize_events(
                [event("project.created", "event-demo-0001", project_id=domain["project_id"], customer_id=domain["customer"]["customer_id"])],
                contracts(),
            )
            self.assertIn(domain["project_id"], snapshot["records"], path.name)

    def test_source_has_no_live_io_or_client_constants(self) -> None:
        source = (ROOT / "services" / "integrations" / "notion_simulator.py").read_text(encoding="utf-8")
        for forbidden in ("open(", "Path(", "os.", "socket", "subprocess", "http", "requests", "urllib", "datetime.now", "agentseo", "ahd"):
            self.assertNotIn(forbidden, source)

    def test_materializes_every_schema_valid_v2_event_and_conflict(self) -> None:
        given_events = load_json(ROOT / "tests" / "fixtures" / "integrations" / "v2" / "positive-workflow-events.json")

        when_snapshot = materialize_events(given_events, contracts())

        self.assertTrue(validate_notion_graph(when_snapshot, NotionGraphTarget.SNAPSHOT, contracts().graph_schemas).valid)
        self.assertIn("integration-status-00000001", when_snapshot["records"])
        self.assertTrue(when_snapshot["conflicts"])
        self.assertEqual("event-00000021", when_snapshot["records"]["integration-status-00000001"]["source_event_id"])
        self.assertEqual(1, when_snapshot["records"]["integration-status-00000001"]["source_revision"])

    def test_projects_one_canonical_gate_with_prior_event_conflict_evidence(self) -> None:
        given_events = [event("gate.ready", "event-demo-0005"), event("gate.approved", "event-demo-0006")]

        when_snapshot = materialize_events(given_events, contracts())

        gates = [record for record in when_snapshot["records"].values() if record["record_type"] == "gate"]
        self.assertEqual(1, len(gates))
        self.assertEqual("approved", gates[0]["projected_status"])
        self.assertTrue(when_snapshot["conflicts"])

    def test_keeps_new_subjects_from_lower_revisions_and_audits_stale_subjects(self) -> None:
        given_events = [
            event("project.created", "event-demo-0001", revision=2),
            event("task.created", "event-demo-0002", revision=1),
        ]

        when_snapshot = materialize_events(given_events, contracts())

        self.assertIn("task-demo-0001", when_snapshot["records"])
        self.assertEqual(2, when_snapshot["records"]["project-demo"]["source_revision"])
        self.assertTrue(when_snapshot["conflicts"])


if __name__ == "__main__":
    unittest.main()
