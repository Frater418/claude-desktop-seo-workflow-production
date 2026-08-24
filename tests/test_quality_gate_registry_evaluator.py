"""Tests for Quality Gate Registry applicability and bindings.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import unittest

from services.quality_gate_registry import evaluate_gate_runs, load_registry, resolve_required_gates


class QualityGateRegistryEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.registry = load_registry()
        self.context = {
            "site_status": "existing_site",
            "multilingual": False,
            "ymyl": True,
            "local": True,
            "production": False,
            "configured_tools": [],
            "available_tools": [],
            "not_applicable_decisions": {
                "qg-step1-independent-search-verification": {
                    "reason": "No independent source is configured for this controlled staging run."
                }
            },
        }
        self.current = {
            "artifact_id": "artifact-topic-0001",
            "content_sha256": "a" * 64,
            "run_id": "run-step1-0001",
        }
        self.crawl = {
            "artifact_id": "artifact-crawl-0001",
            "content_sha256": "b" * 64,
            "run_id": "run-crawl-0001",
        }

    def _record(self, gate_id: str, artifact: dict) -> dict:
        return {
            "quality_gate_id": gate_id,
            "tenant_id": "tenant-heartweb",
            "run_id": artifact["run_id"],
            "step_id": "1",
            "human_gate_id": "GATE-1",
            "artifact_id": artifact["artifact_id"],
            "artifact_sha256": artifact["content_sha256"],
            "registry_version": "1.1.0",
            "result": "passed",
            "evidence": {
                "schema_id": "step1",
                "schema_version": "1.0.0",
                "artifact_sha256": artifact["content_sha256"],
                "validator_result": "passed",
                "crawl_manifest": "crawl",
                "start_url": "https://example.test/",
                "tool_version": "1.0.0",
                "export_hashes": "a" * 64,
                "url_count": "1",
                "issues_overview": "none",
            },
        }

    def test_step1_submit_resolves_domain_and_crawl(self):
        result = resolve_required_gates(self.registry, "1", "submit_for_gate", self.context)
        self.assertTrue(result["valid"])
        self.assertIn("qg-domain-contract", result["required_gate_ids"])
        self.assertIn("qg-step1-crawl-snapshot", result["required_gate_ids"])
        self.assertIn("qg-step1-independent-search-verification", result["not_applicable_gate_ids"])

    def test_configured_gate_requires_explicit_not_applicable_decision(self):
        context = dict(self.context, not_applicable_decisions={})
        result = resolve_required_gates(self.registry, "1", "submit_for_gate", context)
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_GATE_APPLICABILITY_UNDECIDED", {error["code"] for error in result["errors"]})

    def test_configured_but_unavailable_tool_blocks(self):
        context = dict(self.context, configured_tools=["ahrefs"], available_tools=[])
        result = resolve_required_gates(self.registry, "1", "submit_for_gate", context)
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_CONFIGURED_GATE_TOOL_UNAVAILABLE", {error["code"] for error in result["errors"]})

    def test_current_and_supporting_gate_runs_are_accepted(self):
        result = evaluate_gate_runs(
            self.registry,
            "1",
            "submit_for_gate",
            self.context,
            "tenant-heartweb",
            "run-step1-0001",
            "GATE-1",
            self.current,
            [self.crawl],
            [self._record("qg-domain-contract", self.current), self._record("qg-step1-crawl-snapshot", self.crawl)],
        )
        self.assertTrue(result["valid"], result["errors"])

    def test_stale_current_artifact_gate_run_is_rejected(self):
        stale = dict(self.current, content_sha256="c" * 64)
        result = evaluate_gate_runs(
            self.registry,
            "1",
            "submit_for_gate",
            self.context,
            "tenant-heartweb",
            "run-step1-0001",
            "GATE-1",
            self.current,
            [self.crawl],
            [self._record("qg-domain-contract", stale), self._record("qg-step1-crawl-snapshot", self.crawl)],
        )
        self.assertFalse(result["valid"])
        self.assertIn("ERROR_REQUIRED_QUALITY_GATE_MISSING", {error["code"] for error in result["errors"]})

    def test_missing_required_evidence_and_stale_registry_are_rejected(self):
        domain = self._record("qg-domain-contract", self.current)
        crawl = self._record("qg-step1-crawl-snapshot", self.crawl)
        domain["evidence"].pop("schema_id")
        crawl["registry_version"] = "1.0.0"

        result = evaluate_gate_runs(
            self.registry, "1", "submit_for_gate", self.context, "tenant-heartweb", "run-step1-0001",
            "GATE-1", self.current, [self.crawl], [domain, crawl],
        )

        self.assertFalse(result["valid"])
        self.assertIn("ERROR_REQUIRED_QUALITY_GATE_EVIDENCE", {error["code"] for error in result["errors"]})
        self.assertIn("ERROR_REQUIRED_QUALITY_GATE_REGISTRY_VERSION", {error["code"] for error in result["errors"]})

    def test_human_gate_definition_is_resolved_for_approve(self):
        result = evaluate_gate_runs(
            self.registry,
            "1",
            "approve",
            self.context,
            "tenant-heartweb",
            "run-step1-0001",
            "GATE-1",
            self.current,
            [self.crawl],
            [],
        )
        self.assertTrue(result["valid"])
        self.assertEqual("GATE-1", result["human_gate_definitions"][0]["human_gate_id"])

    def test_step4a_submit_resolves_only_local_claims_and_schema_gate(self):
        result = resolve_required_gates(self.registry, "4a", "submit_for_gate", self.context)

        self.assertTrue(result["valid"])
        self.assertIn("qg-step4a-claims-and-schema", result["required_gate_ids"])
        self.assertNotIn("qg-step4a-external-rich-results", result["required_gate_ids"])

    def test_step4a_publish_without_production_does_not_require_external_rich_results(self):
        result = resolve_required_gates(self.registry, "4a", "publish", self.context)

        self.assertTrue(result["valid"])
        self.assertNotIn("qg-step4a-external-rich-results", result["required_gate_ids"])

    def test_step4a_production_publish_requires_only_external_rich_results_gate(self):
        context = dict(self.context, production=True)

        result = resolve_required_gates(self.registry, "4a", "publish", context)

        self.assertTrue(result["valid"])
        self.assertEqual(["qg-step4a-external-rich-results"], result["required_gate_ids"])

    def test_step4b_submit_does_not_resolve_staging_production_gate(self):
        result = resolve_required_gates(self.registry, "4b", "submit_for_gate", self.context)

        self.assertTrue(result["valid"])
        self.assertNotIn("qg-step4b-staging-technical", result["required_gate_ids"])

    def test_step4b_publish_without_production_excludes_staging_gate(self):
        result = resolve_required_gates(self.registry, "4b", "publish", self.context)

        self.assertTrue(result["valid"])
        self.assertNotIn("qg-step4b-staging-technical", result["required_gate_ids"])

    def test_step4b_production_publish_requires_only_staging_gate(self):
        result = resolve_required_gates(self.registry, "4b", "publish", dict(self.context, production=True))

        self.assertTrue(result["valid"])
        machine_gate_ids = [gate["gate_id"] for gate in result["required_gates"] if gate["stage"] != "human_approval"]
        self.assertEqual(["qg-step4b-staging-technical"], machine_gate_ids)

    def _step4b_record(self, provenance_classification: str) -> tuple[dict, dict]:
        artifact = {"artifact_id": "artifact-step4b-0001", "content_sha256": "d" * 64, "run_id": "run-step4b-0001"}
        evidence = {
            "staging_url": "https://staging.example.test/page",
            "crawl_report_sha256": "a" * 64,
            "lighthouse_report_sha256": "b" * 64,
            "axe_report_sha256": "c" * 64,
            "visual_report_sha256": "d" * 64,
            "content_sha256": artifact["content_sha256"],
            "staging_evidence_sha256": "e" * 64,
            "provenance_classification": provenance_classification,
            "verified_at": "2026-08-23T12:00:00Z",
            "raw_evidence_artifact_sha256": artifact["content_sha256"],
        }
        return artifact, {"quality_gate_id": "qg-step4b-staging-technical", "tenant_id": "tenant-heartweb", "run_id": artifact["run_id"], "step_id": "4b", "human_gate_id": "GATE-4B", "artifact_id": artifact["artifact_id"], "artifact_sha256": artifact["content_sha256"], "registry_version": "1.1.0", "result": "passed", "evidence": evidence}

    def test_step4b_production_publish_rejects_local_simulated_evidence(self):
        artifact, record = self._step4b_record("local_simulated")

        result = evaluate_gate_runs(self.registry, "4b", "publish", dict(self.context, production=True), "tenant-heartweb", artifact["run_id"], "GATE-4B", artifact, [], [record])

        self.assertFalse(result["valid"])
        self.assertIn("ERROR_REQUIRED_QUALITY_GATE_PROVENANCE", {error["code"] for error in result["errors"]})

    def test_step4b_production_publish_accepts_external_report_for_normal_validation(self):
        artifact, record = self._step4b_record("external_report")

        result = evaluate_gate_runs(self.registry, "4b", "publish", dict(self.context, production=True), "tenant-heartweb", artifact["run_id"], "GATE-4B", artifact, [], [record])

        self.assertTrue(result["valid"], result["errors"])


if __name__ == "__main__":
    unittest.main()
