#!/usr/bin/env python3
"""Regressionstests fuer Prompt 0 und den Step-0-Vertrag.

Autor: Raphael Rechberger
"""

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = REPO_ROOT / "prompts" / "0-kickoff.xml.md"
SCHEMA_PATH = REPO_ROOT / "standards" / "manifest.schema.json"


class PromptZeroContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prompt = PROMPT_PATH.read_text(encoding="utf-8")
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_prompt_defines_http_only_as_warning_not_blocker(self):
        self.assertIn("WARN_COMPETITOR_HTTPS_UNAVAILABLE", self.prompt)
        self.assertIn("reachable_http_only", self.prompt)
        self.assertIn("kein Blocker", self.prompt)

    def test_prompt_documents_unavailable_competitor_without_blocking(self):
        self.assertIn("WARN_COMPETITOR_UNAVAILABLE", self.prompt)
        self.assertIn("weder ueber HTTPS noch ueber HTTP", self.prompt)
        self.assertIn("kein automatischer Blocker", self.prompt)

    def test_prompt_emits_one_consolidated_operator_message(self):
        self.assertIn("genau eine konsolidierte Operator-Nachricht", self.prompt)

    def test_prompt_separates_services_regions_and_workstreams(self):
        self.assertIn("Kernleistungen sind ausschliesslich kundenbezogene Leistungen", self.prompt)
        self.assertIn("Regionen und Standortvarianten gehoeren nicht in core_services", self.prompt)
        self.assertIn("Recruiting gehoert in workstreams", self.prompt)

    def test_prompt_treats_declared_competitors_as_seed_list(self):
        self.assertIn("nicht als vollstaendige", self.prompt)
        self.assertIn("Wettbewerberliste zu behandeln", self.prompt)
        self.assertIn("Schritt 1 entdeckt zusaetzliche organische Suchwettbewerber", self.prompt)

    def test_prompt_cannot_complete_before_human_gate(self):
        self.assertIn("step_0_kickoff` auf `pending`", self.prompt)
        self.assertIn(
            "Approval, Release und Folgeschrittfreigabe sind separate hashgebundene Core-Records",
            self.prompt,
        )
        self.assertIn(
            "Nur Heartweb Core verarbeitet die explizite Operator-Freigabe",
            self.prompt,
        )
        generation_section = self.prompt.split("<human_review_gate>", 1)[0]
        self.assertNotIn(
            "markiere Phase `step_0_kickoff` als `completed`",
            generation_section,
        )

    def test_schema_defines_operational_step_zero_fields(self):
        properties = self.schema["properties"]
        for field in (
            "competitor_preflight",
            "workstreams",
            "primary_region",
            "secondary_regions",
            "missing_accesses",
            "gate_0",
        ):
            self.assertIn(field, properties)

    def test_core_services_description_excludes_workstreams(self):
        description = (
            self.schema["properties"]["entities"]["properties"]["core_services"][
                "description"
            ]
        )
        self.assertIn("keine Regionen", description)
        self.assertIn("keine Recruiting-Workstreams", description)

    def test_prompt_contains_no_forbidden_dash_characters(self):
        self.assertNotIn(chr(0x2014), self.prompt)
        self.assertNotIn(chr(0x2013), self.prompt)


if __name__ == "__main__":
    unittest.main()
