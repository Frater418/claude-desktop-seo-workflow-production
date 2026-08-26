"""Regression coverage for per-LLM-request Heartweb tool call budgets."""

from __future__ import annotations

import unittest

from services.agent_gateway.evidence_store import AgentGatewayStoreError, scope_operation_binding


def _base_binding() -> dict[str, object]:
    return {
        "schema_version": "1.1.0",
        "registry_id": "registry-step-agent",
        "registry_version": "1.0.0",
        "registry_sha256": "a" * 64,
        "step_id": "0",
        "target_revision": 2,
        "agent_contract_id": "heartweb-step-0-agent",
        "agent_contract_version": "1.0.0",
        "worker_profile_id": "worker-step-0",
        "worker_profile_version": "1.0.0",
        "worker_profile_sha256": "b" * 64,
        "tool_policy_id": "policy-step-0",
        "tool_policy_version": "1.0.0",
        "tool_policy_sha256": "c" * 64,
        "operation_id": "prepare_kickoff_preflight",
        "tool_name": "mcp__heartweb__prepare_kickoff_preflight",
        "phase": "analysis",
        "side_effect": "read_only",
        "confirmation_scope": "none",
        "cost_mode": "none",
        "max_calls": 1,
        "timeout_seconds": 30,
        "evidence_required": True,
    }


def _completed_evidence(llm_run_request_id: str) -> dict[str, object]:
    return {
        "operation_id": "prepare_kickoff_preflight",
        "operation_binding": {
            "target_revision": 2,
            "llm_run_request_id": llm_run_request_id,
        },
    }


class AgentToolCallScopeTests(unittest.TestCase):
    def test_new_llm_request_gets_its_own_call_budget_for_same_core_run(self) -> None:
        result = scope_operation_binding(
            _base_binding(),
            llm_run_request_id="llm-request-second-0001",
            evidence_records=(_completed_evidence("llm-request-first-0001"),),
        )

        self.assertEqual("1.2.0", result["schema_version"])
        self.assertEqual("llm-request-second-0001", result["llm_run_request_id"])

    def test_same_llm_request_cannot_exceed_policy_call_budget(self) -> None:
        with self.assertRaises(AgentGatewayStoreError) as caught:
            scope_operation_binding(
                _base_binding(),
                llm_run_request_id="llm-request-first-0001",
                evidence_records=(_completed_evidence("llm-request-first-0001"),),
            )

        self.assertEqual("ERROR_AGENT_TOOL_CALL_LIMIT", caught.exception.code)


if __name__ == "__main__":
    unittest.main()
