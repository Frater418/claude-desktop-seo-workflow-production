from __future__ import annotations

import copy
import hashlib
import json
import os
import socket
import subprocess
import tempfile
import unittest
import urllib.request
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.context_builder import build_context_package, build_llm_request, canonical_json_bytes, validate_context_package
from services.integrations.n8n_simulator import N8nSimulationError, simulate_n8n
from services.integrations.notion_simulator import materialize_events
from services.operator_api.app import create_app
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry
from tests.test_context_builder import loaded_validator, records_for, step_one_inputs, step_zero_inputs
from tests.test_n8n_simulator import command, contracts as n8n_contracts, request
from tests.test_notion_simulator import contracts as notion_contracts, event
from tests.test_operator_api import RUN, TENANT, PROJECT, command as api_command, operator_record, record_command


ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ROOT / "tests" / "fixtures" / "domain" / "real-customer-matrix"


def _write(workspace: Path, name: str, value: dict[str, str] | list[dict[str, str]]) -> None:
    path = workspace / "v2" / "operator" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _seed_workspace(workspace: Path, tenant_id: str, project_id: str) -> None:
    _write(workspace, "project.json", {"tenant_id": tenant_id, "project_id": project_id, "name": "Neutral Project"})
    _write(workspace, "logical-session.json", {"tenant_id": tenant_id, "project_id": project_id, "logical_session_id": "session-00000001"})
    _write(workspace, "workflow.json", {"tenant_id": tenant_id, "project_id": project_id, "sideflows": [{"step_id": "3b", "status": "not_due"}]})
    _write(workspace, "runs/run-00000001.json", {"tenant_id": tenant_id, "project_id": project_id, "run_id": "run-00000001", "step_id": "0", "revision": "1"})
    for collection in ("steps", "artifacts", "gates", "tasks", "tickets", "assignments", "context-packages", "llm-runs", "performance-checkpoints", "metrics", "adjustment-proposals", "integrations-status"):
        _write(workspace, f"{collection}.json", [])


def _seed_transition_workspace(workspace: Path) -> None:
    _seed_workspace(workspace, TENANT, PROJECT)
    _write(workspace, f"runs/{RUN}.json", {"tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": "0", "gate_id": "GATE-0", "revision": 1, "input_hash": "0" * 64, "status": "pending", "attempt": 1})
    _write(workspace, "steps.json", [{"step_id": "0", "status": "pending"}])
    supporting = {"artifact_id": "artifact-contract-0001", "tenant_id": TENANT, "project_id": PROJECT, "run_id": "run-contract-0001", "step_id": "0", "revision": 1, "content_sha256": "c" * 64}
    _write(workspace, "artifacts.json", [supporting])
    _write(workspace, "gates.json", [{"quality_gate_run_id": "qgr-contract-0001", "quality_gate_id": "qg-domain-contract", "human_gate_id": "GATE-0", "tenant_id": TENANT, "run_id": "run-contract-0001", "step_id": "0", "artifact_id": supporting["artifact_id"], "artifact_sha256": supporting["content_sha256"], "artifact_revision": 1, "registry_version": "1.1.0", "policy_version": "1.1.0", "result": "passed", "evidence": {"schema_id": "runtime", "schema_version": "1.0.0", "artifact_sha256": supporting["content_sha256"], "validator_result": "passed"}, "checked_at": "2026-08-20T00:00:00Z", "checker_version": "test-1.0.0"}])


def _forbid_live_io() -> ExitStack:
    stack = ExitStack()
    failure = AssertionError("Stage D integration tests permit only in-process TestClient and injected local values.")
    stack.enter_context(patch.object(socket, "create_connection", side_effect=failure))
    stack.enter_context(patch.object(subprocess, "run", side_effect=failure))
    stack.enter_context(patch.object(os, "getenv", side_effect=failure))
    stack.enter_context(patch.object(urllib.request, "urlopen", side_effect=failure))
    return stack


def _trace_projection(package: dict[str, object], llm_request: dict[str, object]) -> list[dict[str, object]]:
    return [{
        "context_package_id": package["context_package_id"], "package_sha256": package["package_sha256"],
        "prompt_version": package["prompt"]["prompt_version"], "worker_profile_id": llm_request["worker_profile_id"],
        "worker_profile_sha256": llm_request["worker_profile_sha256"], "model_id": llm_request["model_id"],
        "tool_policy_id": llm_request["tool_policy_id"], "tool_policy_sha256": llm_request["tool_policy_sha256"],
        "output_hash": hashlib.sha256(b'{"output":"neutral"}').hexdigest(),
    }]


def _typed_record_command(verb: str, record_type: str, fixture: str, event_type: str, payload: dict[str, object], suffix: str) -> dict[str, object]:
    record = json.loads((ROOT / "tests" / "fixtures" / "operator" / fixture).read_text(encoding="utf-8"))
    record.update({"tenant_id": TENANT, "project_id": PROJECT, "step_id": "0"})
    if record_type == "workflow-defect":
        record["affected_run_id"] = RUN
    else:
        record["run_id"] = RUN
    command_value = record_command("request-input", operator_record("task-00000001"), suffix)
    command_value.update(command=verb, record_type=record_type, operator_record=record)
    command_value["event"].update(event_type=event_type, payload=payload)
    return command_value


class Sprint4LocalIntegrationTests(unittest.TestCase):
    def test_parameterized_neutral_archetypes_cover_api_dispatch_assignment_checkpoint_and_projection(self) -> None:
        # Given: all ten neutral, local customer archetypes and isolated temporary workspaces.
        paths = sorted(DOMAINS.glob("*.json"))
        self.assertEqual(10, len(paths))
        for path in paths:
            with self.subTest(archetype=path.name), tempfile.TemporaryDirectory() as temporary:
                domain = json.loads(path.read_text(encoding="utf-8"))
                tenant_id = domain["tenant"]["tenant_id"]
                project_id = domain["project_id"]
                workspace = Path(temporary)
                _seed_workspace(workspace, tenant_id, project_id)
                api = TestClient(create_app(WorkspaceRegistry((WorkspaceRegistration(tenant_id, project_id, workspace),)), ROOT))

                n8n_command = {**command(), "tenant_id": tenant_id, "project_id": project_id}
                n8n_state = {**request(n8n_command).state, "tenant_id": tenant_id, "project_id": project_id}
                project_event = event("project.created", "event-demo-0001", project_id=project_id, customer_id=domain["customer"]["customer_id"])
                project_event["identity"]["tenant_id"] = tenant_id
                task = event("task.created", "event-demo-0007", project_id=project_id)
                task["identity"]["tenant_id"] = tenant_id
                assignment = event("assignment.created", "event-demo-0008", project_id=project_id)
                assignment["identity"]["tenant_id"] = tenant_id
                with _forbid_live_io():
                    project = api.get(f"/v1/tenants/{tenant_id}/projects/{project_id}")
                    dispatched = simulate_n8n(replace(request(n8n_command), state=n8n_state), n8n_contracts())
                    projected = materialize_events([project_event, task, assignment], notion_contracts())
                    checkpoint_results = [
                        simulate_n8n(replace(request({**command(step_id="3b"), "tenant_id": tenant_id, "project_id": project_id}, checkpoint_day=day), state=n8n_state), n8n_contracts())
                        for day in (30, 60, 90)
                    ]
                self.assertEqual(200, project.status_code)
                self.assertEqual(project_id, project.json()["data"]["project_id"])
                self.assertEqual("1", dispatched.dispatch_intents[0]["step_id"])
                self.assertEqual("reviewer", projected["records"]["assignment-demo-0001"]["projected_status"])
                self.assertEqual(project_id, projected["records"][project_id]["subject_id"])
                self.assertEqual("customer", projected["records"][domain["customer"]["customer_id"]]["record_type"])
                self.assertEqual(["3b", "3b", "3b"], [result.dispatch_intents[0]["step_id"] for result in checkpoint_results])

    def test_explicit_operator_scenario_matrix_uses_real_transition_and_typed_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            _seed_transition_workspace(workspace)
            api = TestClient(create_app(WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),)), ROOT))
            base = f"/v1/tenants/{TENANT}/projects/{PROJECT}/commands"
            typed = (
                ("revision_preview", "request-revision", _typed_record_command("request-revision", "revision-request", "valid-revision-request.json", "task.created", {"task_id": "task-revision-0001", "task_type": "revision"}, "revision")),
                ("missing_input_blocker", "request-input", _typed_record_command("request-input", "operator-task", "valid-operator-task.json", "step.blocked", {"blocker_id": "blocker-input-0001", "reason": "input required"}, "input")),
                ("workflow_defect", "create-defect", _typed_record_command("create-defect", "workflow-defect", "valid-workflow-defect.json", "defect.created", {"defect_id": "defect-routing-0001", "severity": "P2"}, "defect")),
                ("escalation", "escalate", _typed_record_command("escalate", "escalation-record", "valid-escalation-record.json", "escalation.created", {"escalation_id": "escalation-scope-0001", "decision_owner": "business_owner"}, "escalation")),
                ("waiver", "request-waiver", _typed_record_command("request-waiver", "operator-task", "valid-operator-task.json", "task.created", {"task_id": "task-waiver-0001", "task_type": "waiver"}, "waiver")),
            )
            with _forbid_live_io():
                golden = api.post(f"{base}/start", json=api_command())
                self.assertEqual(200, golden.status_code)
                self.assertFalse(golden.json()["replay"])
                self.assertEqual("in_progress", json.loads((workspace / f"v2/operator/runs/{RUN}.json").read_text(encoding="utf-8"))["status"])
                for scenario, verb, payload in typed:
                    with self.subTest(scenario=scenario):
                        self.assertEqual(200, api.post(f"{base}/{verb}", json=payload).status_code)
                replay_payload = typed[1][2]
                replay = api.post(f"{base}/request-input", json=replay_payload)
                conflict = copy.deepcopy(replay_payload)
                conflict["event"]["event_id"] = "event-record-input-conflict"
                changed = api.post(f"{base}/request-input", json=conflict)
                before_failure = (workspace / "v2/operator/events/events.jsonl").read_text(encoding="utf-8")
                invalid = api_command()
                invalid["expected_revision"] = 9
                failed = api.post(f"{base}/start", json=invalid)
                self.assertTrue(replay.json()["replay"])
                self.assertEqual(409, changed.status_code)
                self.assertEqual(409, failed.status_code)
                self.assertEqual(before_failure, (workspace / "v2/operator/events/events.jsonl").read_text(encoding="utf-8"))
                self.assertEqual("in_progress", json.loads((workspace / f"v2/operator/runs/{RUN}.json").read_text(encoding="utf-8"))["status"])

    def test_context_builder_traceability_rebuild_rejection_and_orchestration_matrix(self) -> None:
        specification, sources, source_bytes, registry = step_zero_inputs()
        baseline = copy.deepcopy((specification, sources, source_bytes))
        package = build_context_package(specification, sources, source_bytes, registry, loaded_validator())
        rebuilt = build_context_package(specification, tuple(reversed(sources)), source_bytes, registry, loaded_validator())
        revision_specification, revision_sources, revision_bytes, revision_registry = step_one_inputs()
        revision_specification.update({"context_package_id": "context-preview-0001", "run_id": "run-preview-0001", "logical_session_id": "logical-session-preview-0001", "trigger": "revision", "target_revision": 2, "revision_context": {"revision_request_id": "revision-request-0001", "rejected_artifact_revision": 1, "expected_new_revision": 2, "finding_logical_ref": "runtime:gate/finding-0001"}})
        revision_extra = (
            {"source_kind": "rejected_artifact", "source_id": "artifact-rejected", "tenant_id": "tenant-demo", "project_id": "project-demo", "revision": 1, "logical_ref": "runtime:artifact/artifact-rejected", "source_status": "rejected", "trust_level": "trusted"},
            {"source_kind": "revision_request", "source_id": "revision-request-0001", "tenant_id": "tenant-demo", "project_id": "project-demo", "revision": 1, "logical_ref": "operator:revision/revision-request-0001", "source_status": "active", "trust_level": "trusted"},
            {"source_kind": "operator_instruction", "source_id": "instruction-0001", "tenant_id": "tenant-demo", "project_id": "project-demo", "revision": 1, "logical_ref": "operator:instruction/instruction-0001", "source_status": "active", "trust_level": "operator_asserted"},
            {"source_kind": "quality_gate_run", "source_id": "finding-0001", "tenant_id": "tenant-demo", "project_id": "project-demo", "revision": 1, "logical_ref": "runtime:gate/finding-0001", "source_status": "active", "trust_level": "trusted"},
        )
        revision_bytes.update({"runtime:artifact/artifact-rejected": b"rejected", "operator:revision/revision-request-0001": b"request", "operator:instruction/instruction-0001": b"instruction", "runtime:gate/finding-0001": b"finding"})
        revision_preview = build_context_package(revision_specification, (*revision_sources, *revision_extra), revision_bytes, revision_registry, loaded_validator())
        context = validate_context_package(package, source_bytes, records_for(package), {"steps": [{"step_id": "0", "requires_released_predecessor": False}]}, (), (), loaded_validator(), registry, "2026-08-20T00:00:00Z")
        profile = json.loads((ROOT / "tests/fixtures/context_builder/positive-worker-profile.json").read_text(encoding="utf-8"))
        llm_request = build_llm_request(package, profile, {"llm_run_request_id": "llm-request-stage-d-0001", "correlation_id": "corr-stage-d-0001", "idempotency_key": "idem-stage-d-0001"}, "2026-08-20T00:00:00Z", loaded_validator(), context)
        stale = copy.deepcopy(package)
        stale["package_sha256"] = "0" * 64
        cross_tenant = copy.deepcopy(package)
        cross_tenant["tenant_id"] = "tenant-other"
        retry = command("retry_delivery")
        retry["target"] = {"service": "delivery_queue", "operation": "retry"}
        wait = command("wait_for_gate")
        wait["target"] = {"service": "workflow_api", "operation": "wait"}
        simulator_request = request(command(step_id="0"))
        source_plan = event("artifact.created", "event-demo-0003")
        source_plan["identity"]["step_id"] = "3"
        checkpoint_event = event("performance.checkpoint_due", "event-demo-0014")
        checkpoint_event["identity"]["step_id"] = "3b"
        metric_event = event("metric.recorded", "event-demo-0015")
        metric_event["identity"]["step_id"] = "3b"
        adjustment_event = event("adjustment.proposed", "event-demo-0016")
        adjustment_event["identity"]["step_id"] = "3b"
        source_plan_baseline = copy.deepcopy(source_plan)
        with _forbid_live_io():
            self.assertEqual(canonical_json_bytes(package), canonical_json_bytes(rebuilt))
            self.assertEqual("revision", revision_preview["trigger"])
            self.assertEqual(2, revision_preview["target_revision"])
            self.assertEqual(baseline, (specification, sources, source_bytes))
            self.assertFalse(validate_context_package(stale, source_bytes, records_for(package), {"steps": [{"step_id": "0", "requires_released_predecessor": False}]}, (), (), loaded_validator(), registry, "2026-08-20T00:00:00Z").valid)
            self.assertFalse(validate_context_package(cross_tenant, source_bytes, records_for(package), {"steps": [{"step_id": "0", "requires_released_predecessor": False}]}, (), (), loaded_validator(), registry, "2026-08-20T00:00:00Z").valid)
            first = simulate_n8n(request(retry), n8n_contracts())
            second = simulate_n8n(replace(request(retry), state=first.state), n8n_contracts())
            terminal = simulate_n8n(replace(request(retry), state=second.state), n8n_contracts())
            recovered = simulate_n8n(replace(request(retry), cache_record={"session_state": "lost"}), n8n_contracts())
            waiting = simulate_n8n(request(wait), n8n_contracts())
            simulator_dispatch = simulate_n8n(simulator_request, n8n_contracts())
            simulator_replay = simulate_n8n(request(command(step_id="0"), stored_commands=(command(step_id="0"),)), n8n_contracts())
            notion_snapshot = materialize_events([source_plan, checkpoint_event, metric_event, adjustment_event], notion_contracts())
            notion_once = materialize_events([source_plan], notion_contracts())
            notion_replay = materialize_events([source_plan, copy.deepcopy(source_plan)], notion_contracts())
            for day in (30, 60, 90):
                self.assertEqual("3b", simulate_n8n(request(command(step_id="3b"), checkpoint_day=day), n8n_contracts()).dispatch_intents[0]["step_id"])
            with self.assertRaisesRegex(N8nSimulationError, "N8N_SIMULATION_CHECKPOINT_INVALID"):
                simulate_n8n(request(command(step_id="3b"), checkpoint_day=120), n8n_contracts())
        self.assertEqual("recover_fresh", recovered.technical_session_decision)
        self.assertEqual("gate.approved", waiting.wait_subscriptions[0]["event_type"])
        self.assertEqual(simulator_request.context_package["context_package_id"], simulator_dispatch.dispatch_intents[0]["context_package_id"])
        self.assertEqual(simulator_request.context_package["package_sha256"], simulator_dispatch.dispatch_intents[0]["context_package_sha256"])
        self.assertTrue(simulator_replay.replay)
        self.assertEqual((), simulator_replay.dispatch_intents)
        self.assertEqual(source_plan_baseline, source_plan)
        self.assertEqual(notion_once, notion_replay)
        self.assertIn("performance-checkpoint-demo-0001", notion_snapshot["records"])
        self.assertIn("metric-demo-0001", notion_snapshot["records"])
        adjustment = notion_snapshot["records"]["adjustment-proposal-demo-0001"]
        self.assertEqual("adjustment_proposal", adjustment["record_type"])
        self.assertNotEqual(source_plan["payload"]["artifact_id"], adjustment["subject_id"])
        self.assertEqual({"artifact", "performance_checkpoint"}, {item["relation_type"] for item in adjustment["relations"] if item["relation_type"] in {"artifact", "performance_checkpoint"}})
        self.assertEqual(1, len(terminal.dlq_entries))
        self.assertEqual("2026-08-20T00:00:00Z", terminal.dlq_entries[0]["first_failed_at"])
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            _seed_transition_workspace(workspace)
            _write(workspace, "context-packages.json", _trace_projection(package, llm_request))
            _write(workspace, "llm-runs.json", [llm_request])
            api = TestClient(create_app(WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),)), ROOT))
            trace = api.get(f"/v1/tenants/{TENANT}/projects/{PROJECT}/context-packages").json()["data"][0]
            self.assertEqual(package["context_package_id"], trace["context_package_id"])
            self.assertEqual(package["package_sha256"], trace["package_sha256"])
            self.assertEqual(package["prompt"]["prompt_version"], trace["prompt_version"])
            self.assertEqual(llm_request["worker_profile_id"], trace["worker_profile_id"])
            self.assertEqual(llm_request["worker_profile_sha256"], trace["worker_profile_sha256"])
            self.assertEqual(llm_request["model_id"], trace["model_id"])
            self.assertEqual(llm_request["tool_policy_id"], trace["tool_policy_id"])
            self.assertEqual(llm_request["tool_policy_sha256"], trace["tool_policy_sha256"])
            self.assertEqual(hashlib.sha256(b'{"output":"neutral"}').hexdigest(), trace["output_hash"])
