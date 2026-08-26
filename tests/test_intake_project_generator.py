from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from services.operator_api.hermes_runs_client import HermesRunResult, HermesRunUsage, HermesRunsError
from services.operator_api.intake_project_generator import (
    HermesIntakeProjectGenerator,
    IntakeProjectGenerationError,
)


ROOT = Path(__file__).resolve().parents[1]


class StaticRunsClient:
    def __init__(self, result: HermesRunResult | HermesRunsError) -> None:
        self.result = result
        self.calls: list[dict[str, str]] = []

    def execute(self, *, input_text: str, instructions: str, session_id: str) -> HermesRunResult:
        self.calls.append({"input_text": input_text, "instructions": instructions, "session_id": session_id})
        if isinstance(self.result, HermesRunsError):
            raise self.result
        return self.result


class IntakeProjectGeneratorTests(unittest.TestCase):
    def test_valid_provider_draft_is_identity_bound_and_domain_validated(self) -> None:
        markdown = "# National B2B\n\nWebsite: national-b2b.example\n\nZielmarkt: Deutschland"
        source_sha256 = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
        project = json.loads((ROOT / "tests/fixtures/domain/real-customer-matrix/national-b2b.json").read_text(encoding="utf-8"))
        project["market_deployments"][0]["provider_location_verification"]["target_id"] = "agentseo-de-country"
        project["planning_capacity"] = {"min": 10, "max": 10, "source": "briefing_confirmed"}
        client = StaticRunsClient(_result(json.dumps({"project_name": "National B2B", "project_v2": project, "missing_fields": []})))
        generator = HermesIntakeProjectGenerator(client=client, repository_root=ROOT)

        outcome = generator.generate(markdown, "tenant-generated", "operator-heartweb-admin", "2026-08-24T20:30:00Z")

        self.assertEqual("project-national-b2b", outcome.reviewed.project_id)
        self.assertEqual("tenant-generated", outcome.reviewed.tenant_id)
        self.assertEqual([], list(outcome.missing_fields))
        generated = outcome.reviewed.project_v2
        self.assertIsNotNone(generated)
        assert generated is not None
        self.assertEqual("Raphael Rechberger", generated["author"])
        self.assertEqual("2026-08-24T20:30:00Z", generated["created_at"])
        self.assertEqual({"tenant_id": "tenant-generated", "name": "Heartweb"}, generated["tenant"])
        self.assertEqual({"source": "operator-intake/briefing.md", "sha256": source_sha256}, generated["source_legacy_manifest"])
        self.assertEqual("brand-national-b2b", generated["market_deployments"][0]["brand_id"])
        self.assertEqual("1.3.0", generated["schema_version"])
        self.assertEqual(
            {
                "status": "verified",
                "provider_id": "agentseo",
                "target_id": "agentseo-de-country",
                "target_type": "country",
                "location_name": "Germany",
                "provider_location_code": 2276,
                "verified_at": "2026-08-17T00:00:00Z",
                "verification_source": "provider_response",
            },
            generated["market_deployments"][0]["provider_location_verification"],
        )
        self.assertEqual(
            {
                "min": 10,
                "max": 10,
                "source": "briefing_confirmed",
                "provisional": False,
                "confirmed_by": "operator-heartweb-admin",
                "confirmed_at": "2026-08-24T20:30:00Z",
            },
            generated["planning_capacity"],
        )
        self.assertEqual(source_sha256, outcome.generation.source_sha256)
        self.assertEqual("run_gateway_intake_0001", outcome.generation.provider_run_id)
        self.assertEqual(1, len(client.calls))
        request = json.loads(client.calls[0]["input_text"])
        self.assertEqual(markdown, request["briefing_markdown"])
        self.assertEqual("tenant-generated", request["tenant_id"])
        self.assertEqual("v1.0.0", request["provider_location_registry"]["registry_version"])
        self.assertEqual(
            "agentseo-de-country",
            request["provider_location_registry"]["targets"][0]["target_id"],
        )
        self.assertEqual(f"intake-{source_sha256[:24]}", client.calls[0]["session_id"])
        self.assertIn("<prompt_id>heartweb.intake.project-v2</prompt_id>", client.calls[0]["instructions"])

    def test_missing_customer_fact_returns_ineligible_draft_without_invention(self) -> None:
        client = StaticRunsClient(
            _result(json.dumps({"project_name": None, "project_v2": None, "missing_fields": ["Kundenname", "Website-Host"]}))
        )
        outcome = HermesIntakeProjectGenerator(client=client, repository_root=ROOT).generate(
            "# Unvollstaendiges Briefing", "tenant-generated", "operator-heartweb-admin", "2026-08-24T20:30:00Z"
        )

        self.assertIsNone(outcome.reviewed.project_v2)
        self.assertIsNone(outcome.reviewed.project_id)
        self.assertEqual(("Kundenname", "Website-Host"), outcome.missing_fields)

    def test_missing_capacity_is_converted_to_operator_question(self) -> None:
        project = json.loads((ROOT / "tests/fixtures/domain/real-customer-matrix/national-b2b.json").read_text(encoding="utf-8"))
        project["market_deployments"][0]["provider_location_verification"]["target_id"] = "agentseo-de-country"
        client = StaticRunsClient(
            _result(json.dumps({"project_name": "National B2B", "project_v2": project, "missing_fields": []}))
        )

        outcome = HermesIntakeProjectGenerator(client=client, repository_root=ROOT).generate(
            "# National B2B", "tenant-generated", "operator-heartweb-admin", "2026-08-24T20:30:00Z"
        )

        self.assertIsNone(outcome.reviewed.project_v2)
        self.assertTrue(any("Planungskapazität" in question for question in outcome.missing_fields))

    def test_wrong_model_and_backend_failure_are_rejected_with_stable_codes(self) -> None:
        valid_output = json.dumps({"project_name": None, "project_v2": None, "missing_fields": ["Kundenname"]})
        cases = (
            (StaticRunsClient(_result(valid_output, model="unexpected-model")), "ERROR_LLM_BACKEND_RESPONSE_INVALID"),
            (StaticRunsClient(HermesRunsError("ERROR_LLM_BACKEND_UNAVAILABLE")), "ERROR_LLM_BACKEND_UNAVAILABLE"),
        )
        for client, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(IntakeProjectGenerationError) as raised:
                    HermesIntakeProjectGenerator(client=client, repository_root=ROOT).generate(
                        "# Briefing", "tenant-generated", "operator-heartweb-admin", "2026-08-24T20:30:00Z"
                    )
                self.assertEqual(expected_code, raised.exception.code)


def _result(output: str, *, model: str = "gpt-5.6-sol") -> HermesRunResult:
    return HermesRunResult(
        run_id="run_gateway_intake_0001",
        session_id="session-placeholder",
        model=model,
        last_event="run.completed",
        output=output,
        usage=HermesRunUsage(input_tokens=10, output_tokens=20, total_tokens=30),
        created_at=1787601600,
        updated_at=1787601601,
    )


if __name__ == "__main__":
    unittest.main()
