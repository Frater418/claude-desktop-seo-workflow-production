"""Contract tests for the Heartweb quality gate registry.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


class QualityGateRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[2]
        cls.schema = json.loads((root / "standards" / "quality" / "quality-gate-registry.schema.json").read_text(encoding="utf-8"))
        cls.registry = json.loads((root / "standards" / "quality" / "quality-gate-registry.json").read_text(encoding="utf-8"))

    def test_registry_validates(self):
        errors = list(Draft202012Validator(self.schema, format_checker=FormatChecker()).iter_errors(self.registry))
        self.assertEqual([], errors)

    def test_gate_ids_are_unique(self):
        gate_ids = [gate["gate_id"] for gate in self.registry["gates"]]
        self.assertEqual(len(gate_ids), len(set(gate_ids)))
        self.assertTrue(all(gate_id.startswith("qg-") for gate_id in gate_ids))

    def test_gate_identity_namespaces_are_distinct(self):
        root = Path(__file__).resolve().parents[2]
        graph = json.loads((root / "standards" / "workflow" / "workflow-graph.json").read_text(encoding="utf-8"))
        quality_run_schema = json.loads((root / "standards" / "runtime" / "quality-gate-run.schema.json").read_text(encoding="utf-8"))
        self.assertTrue(all(step["gate_id"].startswith("GATE-") for step in graph["steps"]))
        self.assertEqual("^qgr-[a-z0-9][a-z0-9-]{7,63}$", quality_run_schema["properties"]["quality_gate_run_id"]["pattern"])
        self.assertTrue(quality_run_schema["properties"]["quality_gate_id"]["pattern"].startswith("^qg-"))
        self.assertTrue(quality_run_schema["properties"]["human_gate_id"]["pattern"].startswith("^GATE-"))

    def test_every_blocking_gate_has_actionable_failure_contract(self):
        for gate in self.registry["gates"]:
            if gate["enforcement"] != "blocking":
                continue
            self.assertTrue(gate["failure_code"].startswith("ERROR_"), gate["gate_id"])
            self.assertGreaterEqual(len(gate["remediation"]), 10, gate["gate_id"])
            self.assertTrue(gate["evidence_required"], gate["gate_id"])
            self.assertIn(gate["gate_type"], {"preflight", "revision", "escalation", "abort"})
            self.assertTrue(gate["blocks_operations"], gate["gate_id"])

    def test_every_workflow_step_has_machine_and_human_gate_coverage(self):
        root = Path(__file__).resolve().parents[2]
        graph = json.loads((root / "standards" / "workflow" / "workflow-graph.json").read_text(encoding="utf-8"))
        graph_steps = {step["step_id"]: step["gate_id"] for step in graph["steps"]}
        graph_steps["3b"] = "GATE-3B"
        for step_id, human_gate_id in graph_steps.items():
            machine = [
                gate for gate in self.registry["gates"]
                if step_id in gate["steps"] and gate["stage"] != "human_approval" and gate["enforcement"] == "blocking"
            ]
            human = [
                gate for gate in self.registry["gates"]
                if step_id in gate["steps"] and gate.get("human_gate_id") == human_gate_id
            ]
            self.assertTrue(machine, f"missing machine gate for {step_id}")
            self.assertEqual(1, len(human), f"missing or duplicate human gate for {step_id}")
            self.assertIn("approve", human[0]["blocks_operations"])
            self.assertIn("complete", human[0]["blocks_operations"])

    def test_crawl_gate_uses_explicit_waiver_policy(self):
        root = Path(__file__).resolve().parents[2]
        crawl = next(gate for gate in self.registry["gates"] if gate["gate_id"] == "qg-step1-crawl-snapshot")
        self.assertTrue(crawl["waiver_allowed"])
        self.assertTrue((root / "standards" / "quality" / "crawl-disposition-policy.json").exists())
        self.assertTrue((root / "standards" / "runtime" / "waiver-record.schema.json").exists())

    def test_step1_requires_crawl_and_revision_bound_approval(self):
        by_id = {gate["gate_id"]: gate for gate in self.registry["gates"]}
        crawl = by_id["qg-step1-crawl-snapshot"]
        approval = by_id["qg-gate1-artifact-approval"]
        self.assertEqual("blocking", crawl["enforcement"])
        self.assertIn({"tool_id": "screaming-frog-cli", "mode": "required"}, crawl["tools"])
        self.assertIn("artifact_sha256", approval["evidence_required"])
        self.assertIn("approval_id", approval["evidence_required"])

    def test_external_tools_have_explicit_enforcement_and_never_silent_fallbacks(self):
        external = {"ahrefs", "google-search-console", "ga4", "google-business-profile", "google-rich-results-test"}
        for gate in self.registry["gates"]:
            for tool in gate["tools"]:
                if tool["tool_id"] in external:
                    self.assertIn(tool["mode"], {"required", "conditional", "independent_verification"})
                    self.assertTrue(gate["failure_code"].startswith("ERROR_"))
                    if tool["mode"] == "required":
                        self.assertEqual("blocking", gate["enforcement"])


if __name__ == "__main__":
    unittest.main()
