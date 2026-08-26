from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from services.operator_api.step_agent_results import (
    StepAgentResultError,
    _raise_agent_failure,
)


ROOT = Path(__file__).resolve().parents[1]


class StepAgentFailureEnvelopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.envelope = {
            "schema_version": "1.1.0",
            "agent_contract_id": "heartweb-step-0-agent",
            "agent_contract_version": "1.2.0",
            "llm_run_request_id": "llm-request-neutral0001",
            "tenant_id": "tenant-neutral",
            "project_id": "project-neutral",
            "run_id": "run-neutral0001",
            "step_id": "0",
            "target_revision": 1,
            "context_package_id": "context-neutral0001",
            "context_package_sha256": "a" * 64,
            "outputs": [],
            "evidence_refs": [],
            "failure": {
                "code": "ERROR_BRIEFING_INCOMPLETE",
                "message": "The accepted briefing lacks required fields.",
                "remediation": "Complete the missing fields and start a fresh Step run.",
                "details": {"missing_fields": ["business_goal"]},
            },
        }

    def test_schema_accepts_structured_fail_closed_result(self) -> None:
        schema = json.loads(
            (ROOT / "standards/runtime/step-agent-output-envelope.schema.json").read_text(encoding="utf-8")
        )

        errors = list(Draft202012Validator(schema).iter_errors(self.envelope))

        self.assertEqual([], errors)

    def test_runtime_preserves_agent_failure_code_and_remediation(self) -> None:
        with self.assertRaises(StepAgentResultError) as raised:
            _raise_agent_failure(self.envelope)

        self.assertEqual("ERROR_BRIEFING_INCOMPLETE", raised.exception.code)
        self.assertEqual("/failure", raised.exception.path)
        self.assertEqual(
            "Complete the missing fields and start a fresh Step run.",
            raised.exception.remediation,
        )


if __name__ == "__main__":
    unittest.main()
