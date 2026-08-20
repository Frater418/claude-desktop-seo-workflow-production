from __future__ import annotations

import copy
import hashlib
import json
import unittest
from dataclasses import replace
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from services.context_builder import ContextValidationResult, build_context_package, build_llm_request, sha256
from services.context_builder.session_policy import _cache_projection
from services.integrations.n8n_simulator import INITIAL_PATH, N8nContracts, N8nSimulationError, N8nSimulationRequest, simulate_n8n
from services.runtime_contracts.llm_records import RuntimeContractValidator


ROOT = Path(__file__).resolve().parents[1]
INTEGRATIONS = ROOT / "standards" / "integrations"
RUNTIME = ROOT / "standards" / "runtime"
DOMAINS = ROOT / "tests" / "fixtures" / "domain" / "real-customer-matrix"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def runtime_validator() -> RuntimeContractValidator:
    names = ("logical-project-session", "worker-profile", "context-package", "llm-run-request", "llm-run-result")
    return RuntimeContractValidator({name: load_json(RUNTIME / f"{name}.schema.json") for name in names}, load_json(RUNTIME / "official-prompt-registry.json"))


def command(command_type: str = "dispatch_tool_run", step_id: str = "1") -> dict:
    return {
        "command_id": "command-demo-0001", "schema_version": "1.0.0", "tenant_id": "tenant-demo", "project_id": "project-demo",
        "run_id": "run-demo-step0" if step_id == "0" else "run-demo-step1", "step_id": step_id, "correlation_id": "corr-demo-0001", "idempotency_key": "idem-demo-0001",
        "expected_revision": 1, "integration_mode": "simulated", "simulation_id": "sim-demo-0001", "requested_at": "2026-08-20T00:00:00Z",
        "command_type": command_type, "target": {"service": "tool_runner", "operation": "dispatch"},
    }


def state() -> dict:
    return {
        "simulation_state_id": "n8n-state-demo-0001", "schema_version": "2.0.0", "integration_mode": "simulated", "simulation_id": "sim-demo-0001",
        "tenant_id": "tenant-demo", "project_id": "project-demo",
        "clock": {"clock_type": "deterministic", "current_time": "2026-08-20T00:00:00Z"},
        "retry_policy": {"max_attempts": 3, "backoff_seconds": 0}, "command_queue": [], "confirmed_checkpoint_days": [30, 60, 90],
    }


def contracts() -> N8nContracts:
    return N8nContracts(
        command_schema=load_json(INTEGRATIONS / "n8n-command.schema.json"), state_schema=load_json(INTEGRATIONS / "n8n-simulation-state.schema.json"),
        wait_schema=load_json(INTEGRATIONS / "n8n-wait-subscription.schema.json"), retry_schema=load_json(INTEGRATIONS / "n8n-retry-entry.schema.json"),
        dlq_schema=load_json(INTEGRATIONS / "n8n-dlq-entry.schema.json"), workflow_graph=load_json(ROOT / "standards" / "workflow" / "workflow-graph.json"),
        runtime_validator=runtime_validator(), worker_profile=load_json(ROOT / "tests" / "fixtures" / "context_builder" / "positive-worker-profile.json"),
    )


def context_evidence(command_value: dict) -> tuple[dict, dict[str, bytes], dict[str, dict], dict, tuple[dict, ...]]:
    registry = load_json(RUNTIME / "official-prompt-registry.json")
    if command_value["step_id"] == "3b" and not any(item["step_id"] == "3b" for item in registry["entries"]):
        plan_entry = next(item for item in registry["entries"] if item["step_id"] == "3")
        prompt_path = ROOT / "prompts" / "3b-performance-check.xml.md"
        registry["entries"].append({"step_id": "3b", "prompt_id": "heartweb.step.3b", "prompt_version": "1.0.0", "prompt_path": "prompts/3b-performance-check.xml.md", "prompt_sha256": hashlib.sha256(prompt_path.read_bytes()).hexdigest(), "output_contracts": plan_entry["output_contracts"], "active": True})
    entry = next(item for item in registry["entries"] if item["step_id"] == command_value["step_id"])
    source_bytes = {f"prompt:{command_value['step_id']}": (ROOT / entry["prompt_path"]).read_bytes()}
    for index, contract in enumerate(entry["output_contracts"], start=1):
        source_bytes[f"output-contract:{command_value['step_id']}/{index}"] = (ROOT / contract["contract_path"]).read_bytes()
    specification = {
        "context_package_id": f"context-demo-step-{command_value['step_id']}", "tenant_id": command_value["tenant_id"], "project_id": command_value["project_id"], "run_id": command_value["run_id"], "step_id": command_value["step_id"],
        "logical_session_id": "logical-session-demo-0001", "logical_session_revision": 1, "trigger": "initial_step" if command_value["step_id"] == "0" else "next_step", "target_revision": command_value["expected_revision"],
        "created_at": "2026-08-20T00:00:00Z", "created_by": "operator-demo", "worker_profile_ref": {"worker_profile_id": "worker-profile-demo", "profile_version": "1.0.0", "profile_sha256": "a" * 64},
    }
    sources: tuple[dict, ...]
    releases: tuple[dict, ...]
    if command_value["step_id"] == "0":
        source_bytes["runtime:intake/intake-demo"] = b'{"project":"intake"}'
        sources = ({"source_kind": "project_intake", "source_id": "intake-demo", "tenant_id": command_value["tenant_id"], "project_id": command_value["project_id"], "revision": 1, "logical_ref": "runtime:intake/intake-demo", "source_status": "active", "trust_level": "trusted"},)
        releases = ()
    else:
        predecessor = "4b" if command_value["step_id"] == "3b" else next(edge["from_step_id"] for edge in contracts().workflow_graph["initial_edges"] if edge["to_step_id"] == command_value["step_id"])
        source_bytes["runtime:project/project-demo"] = b'{"project":"v2"}'
        artifact_ref = f"runtime:artifact/artifact-{predecessor}"
        source_bytes[artifact_ref] = f'{{"artifact":"{predecessor}"}}'.encode("ascii")
        sources = (
            {"source_kind": "project_v2", "source_id": command_value["project_id"], "tenant_id": command_value["tenant_id"], "project_id": command_value["project_id"], "revision": 1, "logical_ref": "runtime:project/project-demo", "source_status": "released", "trust_level": "trusted"},
            {"source_kind": "released_predecessor", "source_id": f"artifact-{predecessor}", "tenant_id": command_value["tenant_id"], "project_id": command_value["project_id"], "revision": 1, "logical_ref": artifact_ref, "source_status": "released", "trust_level": "trusted"},
        )
        releases = ({"tenant_id": command_value["tenant_id"], "project_id": command_value["project_id"], "run_id": command_value["run_id"], "step_id": predecessor, "artifact_id": f"artifact-{predecessor}", "artifact_sha256": hashlib.sha256(source_bytes[artifact_ref]).hexdigest(), "artifact_revision": 1, "gate_id": next(step["gate_id"] for step in contracts().workflow_graph["steps"] if step["step_id"] == predecessor), "status": "released"},)
        if command_value["step_id"] == "3b":
            plan_ref = "runtime:artifact/artifact-3"
            source_bytes[plan_ref] = b'{"artifact":"3"}'
            sources = (*sources, {"source_kind": "evidence", "source_id": "artifact-3", "tenant_id": command_value["tenant_id"], "project_id": command_value["project_id"], "revision": 1, "logical_ref": plan_ref, "source_status": "released", "trust_level": "trusted"})
            releases = (*releases, {"tenant_id": command_value["tenant_id"], "project_id": command_value["project_id"], "run_id": command_value["run_id"], "step_id": "3", "artifact_id": "artifact-3", "artifact_sha256": hashlib.sha256(source_bytes[plan_ref]).hexdigest(), "artifact_revision": 1, "gate_id": "GATE-3", "status": "released"})
    package = build_context_package(specification, sources, source_bytes, registry, contracts().runtime_validator)
    records = {source["logical_ref"]: {**source, **({"run_id": command_value["run_id"], "step_id": source["source_id"].removeprefix("artifact-")} if source["source_kind"] == "released_predecessor" or source["source_id"] == "artifact-3" else {})} for source in package["sources"]}
    return package, source_bytes, records, registry, releases


def request(command_value: dict, *, releases: tuple[dict, ...] | None = None, cache_record: dict | None = None, package_current: bool = True, stored_commands: tuple[dict, ...] = (), checkpoint_day: int | None = None) -> N8nSimulationRequest:
    package, source_bytes, records, registry, default_releases = context_evidence(command_value)
    if command_value["command_type"] == "retry_delivery":
        package["trigger"] = "retry"
        package["package_sha256"] = sha256({key: value for key, value in package.items() if key != "package_sha256"})
    llm_request = build_llm_request(package, contracts().worker_profile, {"llm_run_request_id": "llm-request-demo-0001", "correlation_id": command_value["correlation_id"], "idempotency_key": command_value["idempotency_key"]}, "2026-08-20T00:00:00Z", contracts().runtime_validator, ContextValidationResult(()))
    return N8nSimulationRequest(command_value, state(), package, llm_request, default_releases if releases is None else releases, (), cache_record, package_current, stored_commands, checkpoint_day, source_bytes, records, registry)


class N8nSimulatorTests(unittest.TestCase):
    def test_rejects_live_and_forbidden_command_before_dispatch(self) -> None:
        live = command()
        live["integration_mode"] = "live"
        with self.assertRaisesRegex(N8nSimulationError, "N8N_SIMULATION_COMMAND_INVALID"):
            simulate_n8n(request(live), contracts())
        forbidden = command()
        forbidden["command_type"] = "approve_gate"
        with self.assertRaisesRegex(N8nSimulationError, "N8N_SIMULATION_COMMAND_INVALID"):
            simulate_n8n(request(forbidden), contracts())

    def test_dispatch_requires_valid_stored_package_and_released_predecessor(self) -> None:
        with self.assertRaisesRegex(N8nSimulationError, "N8N_SIMULATION_CONTEXT_INVALID"):
            simulate_n8n(request(command(), releases=()), contracts())
        simulation_request = request(command())
        baseline = copy.deepcopy(simulation_request)
        result = simulate_n8n(simulation_request, contracts())
        self.assertEqual("fresh_required", result.dispatch_intents[0]["technical_session_decision"])
        self.assertEqual("context-demo-step-1", result.dispatch_intents[0]["context_package_id"])
        self.assertEqual("llm-request-demo-0001", result.dispatch_intents[0]["llm_run_request_id"])
        self.assertEqual(baseline, simulation_request)
        self.assertEqual(state(), simulation_request.state)

    def test_dispatches_the_complete_initial_golden_path_only_after_each_release(self) -> None:
        self.assertEqual(("0", "1", "1b", "1c", "2", "3", "4a", "4b"), INITIAL_PATH)
        predecessor: str | None = None
        for step_id in INITIAL_PATH:
            outcome = simulate_n8n(request(command(step_id=step_id)), contracts())
            self.assertEqual(step_id, outcome.dispatch_intents[0]["step_id"])
            predecessor = step_id

    def test_wait_resume_and_cache_loss_are_non_authoritative(self) -> None:
        wait = command("wait_for_gate")
        wait["target"] = {"service": "workflow_api", "operation": "wait"}
        result = simulate_n8n(request(wait), contracts())
        Draft202012Validator(contracts().wait_schema, format_checker=FormatChecker()).validate(result.wait_subscriptions[0])
        task_wait = simulate_n8n(replace(request(wait), wait_event_type="task.resolved"), contracts())
        self.assertEqual("task.resolved", task_wait.wait_subscriptions[0]["event_type"])
        resume = command("resume_run")
        resume["target"] = {"service": "workflow_api", "operation": "resume"}
        resumed = simulate_n8n(request(resume), contracts())
        self.assertEqual("core_command_request", resumed.resume_commands[0]["request_kind"])
        retry = command("retry_delivery")
        retry["target"] = {"service": "delivery_queue", "operation": "retry"}
        retry_request = request(retry)
        assert retry_request.context_package is not None
        cache = _cache_projection(retry_request.context_package, contracts().worker_profile) | {"session_state": "available", "expires_at": "2026-08-21T00:00:00Z"}
        self.assertEqual("fresh_required", simulate_n8n(request(command()), contracts()).technical_session_decision)
        self.assertEqual("reuse_permitted", simulate_n8n(replace(retry_request, cache_record=cache), contracts()).technical_session_decision)
        recovered = simulate_n8n(replace(retry_request, cache_record={"session_state": "lost"}), contracts())
        self.assertEqual("recover_fresh", recovered.technical_session_decision)
        self.assertEqual("denied", simulate_n8n(replace(retry_request, package_is_current=False), contracts()).technical_session_decision)

    def test_replay_conflict_retry_dlq_and_checkpoint_cadence(self) -> None:
        replay = simulate_n8n(request(command(), stored_commands=(command(),)), contracts())
        self.assertTrue(replay.replay)
        changed = command()
        changed["expected_revision"] = 2
        with self.assertRaisesRegex(N8nSimulationError, "N8N_SIMULATION_IDEMPOTENCY_CONFLICT"):
            simulate_n8n(request(changed, stored_commands=(command(),)), contracts())
        retry = command("retry_delivery")
        retry["target"] = {"service": "delivery_queue", "operation": "retry"}
        first = simulate_n8n(request(retry), contracts())
        second_request = request(retry)
        second = simulate_n8n(replace(second_request, state=first.state), contracts())
        third_request = request(retry)
        result = simulate_n8n(replace(third_request, state=second.state), contracts())
        self.assertEqual(1, len(first.retry_entries))
        self.assertEqual(1, len(second.retry_entries))
        self.assertEqual(1, len(result.dlq_entries))
        for day in (30, 60, 90):
            sideflow = command(step_id="3b")
            sideflow["command_id"] = f"command-demo-00{day}"
            sideflow["idempotency_key"] = f"idem-demo-00{day}"
            outcome = simulate_n8n(request(sideflow, checkpoint_day=day), contracts())
            self.assertEqual("3b", outcome.dispatch_intents[0]["step_id"])
        with self.assertRaisesRegex(N8nSimulationError, "N8N_SIMULATION_CHECKPOINT_INVALID"):
            simulate_n8n(request(command(step_id="3b"), checkpoint_day=29), contracts())
        with self.assertRaisesRegex(N8nSimulationError, "N8N_SIMULATION_CHECKPOINT_INVALID"):
            simulate_n8n(request(command(step_id="3b"), checkpoint_day=120), contracts())

    def test_rejects_step_three_plan_hash_and_revision_drift(self) -> None:
        given_request = request(command(step_id="3b"), checkpoint_day=30)
        given_records = copy.deepcopy(given_request.current_records)
        given_records["runtime:artifact/artifact-3"]["content_sha256"] = "0" * 64

        with self.assertRaisesRegex(N8nSimulationError, "N8N_SIMULATION_CONTEXT_INVALID"):
            simulate_n8n(replace(given_request, current_records=given_records), contracts())
        given_releases = list(given_request.releases)
        given_releases[1]["artifact_revision"] = 2
        with self.assertRaisesRegex(N8nSimulationError, "N8N_SIMULATION_PREDECESSOR_REQUIRED"):
            simulate_n8n(replace(given_request, releases=tuple(given_releases)), contracts())

    def test_rejects_context_package_with_missing_current_record(self) -> None:
        given_request = request(command())
        given_records = copy.deepcopy(given_request.current_records)
        del given_records["runtime:artifact/artifact-0"]

        with self.assertRaisesRegex(N8nSimulationError, "N8N_SIMULATION_CONTEXT_INVALID"):
            simulate_n8n(replace(given_request, current_records=given_records), contracts())

    def test_executes_all_n8n_operations_for_each_neutral_archetype(self) -> None:
        for path in sorted(DOMAINS.glob("*.json")):
            domain = load_json(path)
            scoped = {"tenant_id": domain["tenant"]["tenant_id"], "project_id": domain["project_id"]}
            scoped_state = {**state(), **scoped}
            dispatched = simulate_n8n(replace(request({**command(), **scoped}), state=scoped_state), contracts())
            waiting_command = {**command("wait_for_gate"), **scoped, "target": {"service": "workflow_api", "operation": "wait"}}
            self.assertEqual(1, len(simulate_n8n(replace(request(waiting_command), state=scoped_state), contracts()).wait_subscriptions), path.name)
            retry_command = {**command("retry_delivery"), **scoped, "target": {"service": "delivery_queue", "operation": "retry"}}
            first = simulate_n8n(replace(request(retry_command), state=scoped_state), contracts())
            second = simulate_n8n(replace(request(retry_command), state=first.state), contracts())
            self.assertEqual(1, len(simulate_n8n(replace(request(retry_command), state=second.state), contracts()).dlq_entries), path.name)
            resume_command = {**command("resume_run"), **scoped, "target": {"service": "workflow_api", "operation": "resume"}}
            self.assertEqual(1, len(simulate_n8n(replace(request(resume_command), state=scoped_state), contracts()).resume_commands), path.name)
            sideflow = {**command(step_id="3b"), **scoped}
            self.assertEqual("3b", simulate_n8n(replace(request(sideflow, checkpoint_day=30), state=scoped_state), contracts()).dispatch_intents[0]["step_id"])
            self.assertEqual("1", dispatched.dispatch_intents[0]["step_id"], path.name)

    def test_source_has_no_live_io_or_client_constants(self) -> None:
        source = (ROOT / "services" / "integrations" / "n8n_simulator.py").read_text(encoding="utf-8")
        for forbidden in ("open(", "Path(", "os.", "socket", "subprocess", "http", "requests", "urllib", "datetime.now", "agentseo", "ahd"):
            self.assertNotIn(forbidden, source)

    def test_rejects_cross_scope_wait_before_state_queueing(self) -> None:
        given_command = command("wait_for_gate")
        given_command["target"] = {"service": "workflow_api", "operation": "wait"}
        given_command["tenant_id"] = "tenant-other"
        given_command["project_id"] = "project-other"

        with self.assertRaisesRegex(N8nSimulationError, "N8N_SIMULATION_SCOPE_INVALID"):
            simulate_n8n(request(given_command), contracts())

    def test_rejects_forged_context_hash_before_dispatch(self) -> None:
        given_request = request(command())
        given_package = copy.deepcopy(given_request.context_package)
        given_llm_request = copy.deepcopy(given_request.llm_request)
        assert given_package is not None
        assert given_llm_request is not None
        given_package["package_sha256"] = "0" * 64
        given_llm_request["context_package_sha256"] = "0" * 64
        given_llm_request["input_sha256"] = "0" * 64

        with self.assertRaisesRegex(N8nSimulationError, "N8N_SIMULATION_CONTEXT_INVALID"):
            simulate_n8n(replace(given_request, context_package=given_package, llm_request=given_llm_request), contracts())

    def test_rejects_forged_cross_tenant_predecessor_before_dispatch(self) -> None:
        given_release = {
            "step_id": "0", "status": "released", "tenant_id": "tenant-other", "project_id": "project-other",
            "run_id": "run-other-0001", "artifact_id": "artifact-other-0001", "artifact_sha256": "0" * 64,
            "artifact_revision": 999, "gate_id": "GATE-0",
        }

        with self.assertRaisesRegex(N8nSimulationError, "N8N_SIMULATION_CONTEXT_INVALID"):
            simulate_n8n(request(command(), releases=(given_release,)), contracts())

    def test_preserves_first_failure_timestamp_in_terminal_dlq(self) -> None:
        given_command = command("retry_delivery")
        given_command["target"] = {"service": "delivery_queue", "operation": "retry"}
        first = simulate_n8n(request(given_command), contracts())
        second_request = request(given_command)
        second_state = copy.deepcopy(first.state)
        second_state["clock"]["current_time"] = "2026-08-20T00:01:00Z"
        second = simulate_n8n(replace(second_request, state=second_state), contracts())
        third_request = request(given_command)
        third_state = copy.deepcopy(second.state)
        third_state["clock"]["current_time"] = "2026-08-20T00:02:00Z"

        when_result = simulate_n8n(replace(third_request, state=third_state), contracts())

        self.assertEqual("2026-08-20T00:00:00Z", when_result.dlq_entries[0]["first_failed_at"])
        self.assertEqual("2026-08-20T00:02:00Z", when_result.dlq_entries[0]["failed_at"])


if __name__ == "__main__":
    unittest.main()
