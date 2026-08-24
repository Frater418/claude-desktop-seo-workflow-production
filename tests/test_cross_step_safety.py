from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from services.step1c_preflight.render import render_step1c
from services.step2_preflight.validator import validate_step2_preflight
from services.step3_preflight.validator import validate_step3_preflight
from services.step3b_preflight.validator import validate_step3b_preflight
from services.step4b_preflight.render import RendererError, render_step4b
from services.step4b_preflight.validator import (
    page_content_sha256,
    staging_evidence_sha256,
    validate_step4b_candidate,
)
from tests.test_step3_renderer import _operational_bundle


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def bind_step4b_hashes(bundle: dict) -> None:
    page = bundle["page_spec"]
    graph = page["jsonld"]["graph"]
    graph_json = json.dumps(graph, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    page["jsonld"]["graph_hash"] = hashlib.sha256(graph_json.encode("utf-8")).hexdigest()
    content_hash = page_content_sha256(page)
    page["content_sha256"] = content_hash
    staging = bundle["staging_evidence"]
    staging["content_sha256"] = content_hash
    for check in staging["checks"]:
        check["content_sha256"] = content_hash
    staging["staging_sha256"] = staging_evidence_sha256(staging)


class CrossStepSafetyTests(unittest.TestCase):
    def test_step2_rejects_empty_evidence(self) -> None:
        # Given: an empty Step 2 submission
        bundle: dict = {}
        # When: preflight evaluates it
        result = validate_step2_preflight(bundle)
        # Then: it cannot create a false green
        self.assertFalse(result["valid"])

    def test_step3_rejects_forged_hashes(self) -> None:
        # Given: a valid operational Step 3 bundle with complete lineage and identity
        bundle = _operational_bundle()
        baseline = validate_step3_preflight(bundle)
        self.assertTrue(baseline["valid"], baseline["errors"])

        # When: valid-format hashes differ from their canonical solver payloads
        self.assertNotEqual("0" * 64, bundle["candidate"]["solver_input_sha256"])
        self.assertNotEqual("0" * 64, bundle["candidate"]["solver_output_sha256"])
        bundle["candidate"]["solver_input_sha256"] = "0" * 64
        bundle["candidate"]["solver_output_sha256"] = "0" * 64
        result = validate_step3_preflight(bundle)
        # Then: hash integrity, rather than schema shape, rejects the candidate
        self.assertFalse(result["valid"])
        self.assertEqual("ERROR_STEP3_PREFLIGHT", result["errors"][0]["code"])
        self.assertIn("matching SHA-256 values", result["errors"][0]["message"])

    def test_step1c_renders_every_template(self) -> None:
        # Given: two valid templates
        bundle = {
            "design": load_json("tests/fixtures/step1c/non-ahd-outdoor-design-system.json"),
            "templates": [load_json("tests/fixtures/step1c/non-ahd-outdoor-template.json")],
        }
        bundle["templates"].append(copy.deepcopy(bundle["templates"][0]))
        bundle["templates"][1]["content_id"] = "pillar-outdoor-secondary-001"
        # When: canonical views are rendered
        rendered = render_step1c(bundle)
        # Then: both template identities are present
        self.assertIn("pillar-outdoor-secondary-001", "\n".join(rendered.values()))

    def test_step3b_rejects_reused_revision_and_hash(self) -> None:
        # Given: a proposal that reuses its released plan revision and hash
        bundle = copy.deepcopy(load_json("tests/fixtures/step3b/positive-bundle.json"))
        candidate = bundle["adjustment"]
        candidate["candidate_status"] = "awaiting_gate"
        candidate["proposed_plan"]["revision"] = candidate["source_plan"]["revision"]
        candidate["proposed_plan"]["content_sha256"] = candidate["source_plan"]["content_sha256"]
        # When: Step 3B validates the proposal
        result = validate_step3b_preflight(bundle)
        # Then: immutable lineage remains protected
        self.assertFalse(result["valid"])

    def test_step4b_escapes_hostile_reachable_text_and_jsonld(self) -> None:
        # Given: a genuinely valid typed baseline with hostile reachable content.
        bundle = copy.deepcopy(load_json("tests/fixtures/step4b/pq0-4b-001-positive.json"))
        self.assertTrue(validate_step4b_candidate(bundle)["valid"])
        page = bundle["page_spec"]
        direct_answer = next(section for section in page["sections"] if section["role"] == "direct_answer")
        direct_answer["content"]["paragraphs"][0] = '<img src=x onerror="window.audit_marker=1">'
        page["jsonld"]["graph"]["@graph"][0]["name"] = "<script>window.audit_marker=1"
        bind_step4b_hashes(bundle)
        self.assertTrue(validate_step4b_candidate(bundle)["valid"])

        # When: the candidate-only renderer emits the typed document.
        rendered = render_step4b(bundle)

        # Then: the hostile text is escaped and JSON-LD cannot contain executable markup.
        self.assertIn("&lt;img src=x onerror=&quot;window.audit_marker=1&quot;&gt;", rendered)
        self.assertIn("\\u003cscript\\u003ewindow.audit_marker=1", rendered)
        self.assertEqual(1, rendered.count('<script type="application/ld+json">'))

    def test_step4b_rejects_hostile_url_and_jsonld_script_breakout(self) -> None:
        # Given: a genuinely valid typed baseline and two independently hostile mutations.
        baseline = load_json("tests/fixtures/step4b/pq0-4b-001-positive.json")
        self.assertTrue(validate_step4b_candidate(baseline)["valid"])
        hostile_url = copy.deepcopy(baseline)
        hostile_url["page_spec"]["sibling_links"][0]["url"] = "javascript:window.audit_marker=1"
        bind_step4b_hashes(hostile_url)
        hostile_jsonld = copy.deepcopy(baseline)
        hostile_jsonld["page_spec"]["jsonld"]["graph"]["@graph"][0]["name"] = "</script><script>window.audit_marker=1</script>"
        bind_step4b_hashes(hostile_jsonld)

        # When: each mutated Page Spec crosses the renderer boundary.
        url_result = validate_step4b_candidate(hostile_url)
        jsonld_result = validate_step4b_candidate(hostile_jsonld)

        # Then: invalid schemes and script-block termination are rejected before rendering.
        self.assertFalse(url_result["valid"])
        self.assertFalse(jsonld_result["valid"])
        with self.assertRaises(RendererError):
            render_step4b(hostile_url)
        with self.assertRaises(RendererError):
            render_step4b(hostile_jsonld)


if __name__ == "__main__":
    unittest.main()
