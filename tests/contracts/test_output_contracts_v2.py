#!/usr/bin/env python3
import json
import re
import unittest
import xml.etree.ElementTree as ElementTree
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = REPO_ROOT / "standards" / "outputs"
COMMON_FIELDS = {
    "schema_version",
    "artifact_id",
    "run_id",
    "project_id",
    "step_id",
    "revision",
    "source_artifact_ids",
    "evidence_ids",
    "decision_records",
    "candidate_status",
}
SCHEMA_STEPS = {
    "step-1-topic-inventory.schema.json": "1",
    "step-1b-architecture.schema.json": "1b",
    "step-1c-design-system.schema.json": "1c",
    "step-1c-template.schema.json": "1c",
    "step-2-keyword-evidence.schema.json": "2",
    "step-3-plan.schema.json": "3",
    "step-3b-adjustment.schema.json": "3b",
    "step-4a-briefing.schema.json": "4a",
    "claim-ledger.schema.json": "4a",
    "step-4b-page-spec.schema.json": "4b",
    "staging-evidence.schema.json": "4b",
}
PROMPTS = {
    "1": "1-pillar-identifikation.xml.md",
    "1b": "1b-seitenarchitektur.xml.md",
    "1c": "1c-pillar-template.xml.md",
    "2": "2-cluster-recherche.xml.md",
    "3": "3-120-tage-plan.xml.md",
    "3b": "3b-performance-check.xml.md",
    "4a": "4a-content-briefing-und-schema.xml.md",
    "4b": "4b-landingpage-html.xml.md",
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_prompt(path: Path) -> ElementTree.Element:
    content = path.read_text(encoding="utf-8")
    match = re.search(r"```xml\s*(.*?)\s*```", content, re.DOTALL)
    if match is None:
        raise AssertionError(f"missing XML prompt body: {path}")
    xml_body = match.group(1).replace("&", "&amp;")
    return ElementTree.fromstring(f"<prompt>{xml_body}</prompt>")


class OutputContractsV2Tests(unittest.TestCase):
    def test_authorized_output_schemas_share_the_v2_meta_contract(self) -> None:
        schema_ids: set[str] = set()

        for filename, expected_step in SCHEMA_STEPS.items():
            schema = load_json(OUTPUTS_DIR / filename)
            with self.subTest(schema=filename):
                self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
                self.assertEqual("object", schema["type"])
                self.assertFalse(schema.get("additionalProperties", True))
                self.assertTrue(COMMON_FIELDS.issubset(set(schema["required"])))
                self.assertEqual(expected_step, schema["properties"]["step_id"]["const"])
                self.assertEqual("awaiting_gate", schema["properties"]["candidate_status"]["const"])
                self.assertNotRegex(json.dumps(schema), r"(?i)\b(?:ahd|client)\b")
                schema_id = schema["$id"]
                self.assertNotIn(schema_id, schema_ids)
                schema_ids.add(schema_id)

    def test_v2_prompts_preserve_the_canonical_candidate_gate_boundary(self) -> None:
        for expected_step, filename in PROMPTS.items():
            prompt = parse_prompt(REPO_ROOT / "prompts" / filename)
            metadata = prompt.find("prompt_metadata")
            self.assertIsNotNone(metadata, filename)
            assert metadata is not None

            with self.subTest(prompt=filename):
                self.assertEqual(expected_step, metadata.findtext("step"))
                self.assertEqual("2.0.0", metadata.findtext("version"))
                self.assertTrue("released" in " ".join(prompt.itertext()).lower())
                self.assertTrue("canonical" in " ".join(prompt.itertext()).lower())
                self.assertTrue("derived" in " ".join(prompt.itertext()).lower())
                self.assertTrue("awaiting_gate" in " ".join(prompt.itertext()))
                self.assertTrue("external" in " ".join(prompt.itertext()).lower())

                prohibitions = " ".join(
                    text.strip() for section in prompt.findall("prohibitions") for text in section.itertext()
                ).lower()
                self.assertIn("legacy-manifest", prohibitions)
                self.assertIn("folgeschritt", prohibitions)
                self.assertTrue("provider" in prohibitions and ("direkt" in prohibitions or "keine" in prohibitions))


if __name__ == "__main__":
    unittest.main()
