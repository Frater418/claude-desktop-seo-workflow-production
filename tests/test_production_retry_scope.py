"""Regression coverage for request-scoped production technical retries."""

from __future__ import annotations

import unittest

from services.operator_api.production_orchestrator import (
    ProductionOrchestrator,
    _artifact_blocks_technical_retry,
    _can_resteer_in_progress,
    _evidence_blocks_technical_retry,
    _technical_retry_runtime_request,
)


class ProductionRetryScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = {
            "created_at": "2026-08-25T17:47:13.119660Z",
            "dispatch": {
                "llm_request": {
                    "llm_run_request_id": "llm-request-current-0001",
                }
            },
        }

    def test_request_bound_evidence_only_blocks_the_same_llm_request(self) -> None:
        same_request = {
            "created_at": "2026-08-25T17:47:20Z",
            "operation_binding": {
                "schema_version": "1.2.0",
                "llm_run_request_id": "llm-request-current-0001",
            },
        }
        other_request = {
            "created_at": "2026-08-25T17:47:20Z",
            "operation_binding": {
                "schema_version": "1.2.0",
                "llm_run_request_id": "llm-request-previous-0001",
            },
        }

        self.assertTrue(_evidence_blocks_technical_retry(same_request, self.source))
        self.assertFalse(_evidence_blocks_technical_retry(other_request, self.source))

    def test_same_request_read_only_no_cost_evidence_is_replay_safe(self) -> None:
        replay_safe = {
            "created_at": "2026-08-25T17:47:20Z",
            "operation_binding": {
                "schema_version": "1.2.0",
                "llm_run_request_id": "llm-request-current-0001",
                "confirmation_scope": "none",
                "cost_mode": "none",
                "side_effect": "read_only",
            },
        }

        self.assertFalse(_evidence_blocks_technical_retry(replay_safe, self.source))

    def test_legacy_evidence_uses_the_source_execution_time_boundary(self) -> None:
        prior = {
            "created_at": "2026-08-25T17:21:15Z",
            "operation_binding": {"schema_version": "1.1.0"},
        }
        during_source = {
            "created_at": "2026-08-25T17:47:20Z",
            "operation_binding": {"schema_version": "1.1.0"},
        }
        malformed = {
            "created_at": "not-a-time",
            "operation_binding": {"schema_version": "1.1.0"},
        }

        self.assertFalse(_evidence_blocks_technical_retry(prior, self.source))
        self.assertTrue(_evidence_blocks_technical_retry(during_source, self.source))
        self.assertTrue(_evidence_blocks_technical_retry(malformed, self.source))

    def test_terminal_tool_failure_is_manually_retryable(self) -> None:
        self.assertIn("ERROR_STEP_AGENT_TOOL_FAILED", ProductionOrchestrator._TECHNICAL_RETRY_CODES)
        self.assertIn("ERROR_STEP_AGENT_OUTPUT_ENVELOPE_INVALID", ProductionOrchestrator._TECHNICAL_RETRY_CODES)
        self.assertIn("ERROR_LOCATION_BINDING_MISMATCH", ProductionOrchestrator._TECHNICAL_RETRY_CODES)
        self.assertIn("ERROR_SCHEMA_VALIDATION", ProductionOrchestrator._TECHNICAL_RETRY_CODES)

    def test_rejected_source_artifact_does_not_block_retry_but_new_output_does(self) -> None:
        source = {"run_id": "run-current-0001", "expected_revision": 2}
        rejected_source = {"run_id": "run-current-0001", "revision": 2}
        new_output = {"run_id": "run-current-0001", "revision": 3}

        self.assertFalse(_artifact_blocks_technical_retry(rejected_source, source))
        self.assertTrue(_artifact_blocks_technical_retry(new_output, source))

    def test_failed_revision_without_new_artifact_can_be_resteered(self) -> None:
        run = {"status": "in_progress", "revision": 2}
        artifacts = [{"revision": 2}]
        failed = [{"status": "failed", "dispatch": {"steered_rerun": {"steering_id": "steering-old"}, "technical_retry": None}}]

        self.assertTrue(_can_resteer_in_progress(run, artifacts, failed))
        self.assertFalse(_can_resteer_in_progress(run, [{"revision": 3}], failed))
        self.assertFalse(_can_resteer_in_progress(run, artifacts, [{"status": "running", "dispatch": {"steered_rerun": {"steering_id": "steering-old"}, "technical_retry": None}}]))

    def test_technical_retry_creates_a_fresh_llm_execution_identity(self) -> None:
        source_request = {
            "tenant_id": "tenant-heartweb",
            "project_id": "project-neutral-live",
            "run_id": "run-neutral-0001",
            "step_id": "0",
            "context_package_id": "context-source-0001",
            "llm_run_request_id": "llm-request-source-0001",
            "llm_run_result_id": "llm-result-source-0001",
            "correlation_id": "correlation-source-0001",
            "idempotency_key": "idempotency-source-0001",
            "actor_id": "operator-heartweb-admin",
            "requested_at": "2026-08-25T17:47:13Z",
        }

        retry = _technical_retry_runtime_request(
            source_request,
            retry_key="idem-live-retry-0002",
            requested_at="2026-08-25T18:30:00Z",
        )

        for field in ("tenant_id", "project_id", "run_id", "step_id", "actor_id", "context_package_id"):
            self.assertEqual(source_request[field], retry[field])
        for field in (
            "llm_run_request_id",
            "llm_run_result_id",
            "correlation_id",
            "idempotency_key",
        ):
            self.assertNotEqual(source_request[field], retry[field])
        self.assertEqual("retry", retry["trigger"])
        self.assertEqual("2026-08-25T18:30:00Z", retry["requested_at"])


if __name__ == "__main__":
    unittest.main()
