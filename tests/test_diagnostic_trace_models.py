from __future__ import annotations

import unittest

from pydantic import ValidationError

from services.operator_api.diagnostic_trace_models import (
    DiagnosticTraceOperation,
    DiagnosticTraceStart,
    TraceEvidenceReference,
)


class DiagnosticTraceModelTests(unittest.TestCase):
    def start(self) -> DiagnosticTraceStart:
        return DiagnosticTraceStart(
            schema_version="1.0.0",
            tenant_id="tenant-contract",
            project_id="project-contract",
            run_id="run-contract-0001",
            scenario_id="manual-walkthrough-0001",
            source="manual",
            created_at="2026-08-22T10:15:30Z",
        )

    def operation(self) -> DiagnosticTraceOperation:
        return DiagnosticTraceOperation(
            operation_id="operation-contract-0001",
            occurred_at="2026-08-22T10:15:31Z",
            action="create_delivery",
            route="/v1/tenants/tenant-contract/projects/project-contract/delivery/exports",
            api_method="POST",
            api_status=201,
            error_code=None,
            remediation=None,
            expected_actions=("create_delivery",),
            rendered_actions=("create_delivery",),
            disabled_actions=(),
            evidence_references=(
                TraceEvidenceReference(
                    kind="screenshot",
                    relative_path="screenshots/delivery-created.png",
                ),
            ),
        )

    def test_start_binds_the_full_trace_identity_and_forbids_extra_fields(self) -> None:
        start = self.start()

        self.assertEqual("tenant-contract", start.tenant_id)
        self.assertEqual("project-contract", start.project_id)
        self.assertEqual("run-contract-0001", start.run_id)
        self.assertEqual("manual-walkthrough-0001", start.scenario_id)
        with self.assertRaises(ValidationError):
            DiagnosticTraceStart(**{**start.model_dump(), "authorization": "Bearer secret"})

    def test_operations_are_strict_frozen_and_allow_only_explicit_diagnostic_fields(self) -> None:
        operation = self.operation()

        with self.assertRaises(ValidationError):
            operation.action = "overwrite_delivery"
        for field, value in (
            ("api_status", "201"),
            ("metadata", {"unrestricted": "customer document"}),
            ("reasoning", "hidden chain of thought"),
            ("expected_actions", ("create_delivery", "create_delivery")),
            ("rendered_actions", ("operator notes",)),
            ("disabled_actions", tuple("create_delivery" for _ in range(33))),
            ("remediation", "Retry after the delivery recovery is repaired."),
        ):
            with self.subTest(field=field):
                payload = operation.model_dump()
                payload[field] = value
                with self.assertRaises(ValidationError):
                    DiagnosticTraceOperation(**payload)

    def test_route_and_screenshot_references_are_safe_relative_allowlisted_values(self) -> None:
        operation = self.operation()

        for route in (
            "https://operator.example.invalid/v1/delivery",
            "/v1/delivery?authorization=secret",
            "/v1/../secrets",
        ):
            with self.subTest(route=route):
                payload = operation.model_dump()
                payload["route"] = route
                with self.assertRaises(ValidationError):
                    DiagnosticTraceOperation(**payload)
        for path in ("/tmp/capture.png", "screenshots/../secret.png", "evidence/capture.txt"):
            with self.subTest(path=path), self.assertRaises(ValidationError):
                TraceEvidenceReference(kind="screenshot", relative_path=path)


if __name__ == "__main__":
    unittest.main()
