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


if __name__ == "__main__":
    unittest.main()
