from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from services.jsonld_validation import validate_local_jsonld_text
from services.step2_preflight.validator import validate_step2_candidate
from services.step3_preflight.render import RendererError as Step3RendererError
from services.step3_preflight.render import render_step3
from services.step3_preflight.validator import validate_step3_candidate
from services.step3b_preflight.validator import validate_step3b_preflight
from services.step4a_preflight.validator import validate_step4a_candidate
from services.step4b_preflight.render import render_step4b
from services.step4b_preflight.validator import validate_step4b_candidate
from tests.test_preflight_common import _bind_candidate, _predecessor, _project
from tests.test_step4b_contract import load_fixture as _page_fixture


ROOT = Path(__file__).resolve().parents[1]


def _fixture(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _graph(name: str) -> dict[str, object]:
    return {
        "@context": "https://schema.org",
        "@graph": [{"@id": "https://example.invalid/page#product", "@type": "Product", "name": name}],
    }


def _page_content_hash(page: dict[str, object]) -> str:
    payload = dict(page)
    payload.pop("content_sha256")
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


class FinalReviewFixRegressionTests(unittest.TestCase):
    def test_step2_rejects_row_evidence_not_declared_by_candidate(self) -> None:
        # Given: a candidate with verified rows but an unrelated declared evidence set.
        candidate = _fixture("tests/fixtures/step2/non-ahd-solar-fr-ca.json")["candidate"]
        candidate["candidate_status"] = "awaiting_gate"
        candidate["language"] = "fr"
        candidate["geo"] = {"country_code": "CA", "provider_location_code": 1001}
        candidate["evidence_ids"] = ["evidence-source-solar-001"]
        # When: candidate validation examines row evidence declarations.
        result = validate_step2_candidate({"candidate": candidate})
        # Then: undeclared provider row evidence cannot enter the workflow.
        self.assertFalse(result["valid"])

    def test_step3_rejects_arbitrary_solver_input_and_schema_extra_field(self) -> None:
        # Given: a syntactically hashed arbitrary solver payload and an extra candidate field.
        candidate = _fixture("tests/fixtures/step3/non-ahd-solar-fr-ca.json")["candidate"]
        candidate["candidate_status"] = "awaiting_gate"
        candidate["solver_input"] = "{}"
        candidate["solver_input_sha256"] = hashlib.sha256(b"{}").hexdigest()
        output = {key: candidate[key] for key in ("weeks", "mandatory_item_ids", "backlog_item_ids", "vertical_links", "horizontal_links")}
        candidate["solver_output"] = _canonical(output)
        candidate["solver_output_sha256"] = hashlib.sha256(candidate["solver_output"].encode("utf-8")).hexdigest()
        candidate["unexpected"] = True
        # When: the candidate-only validation path is used by the renderer.
        result = validate_step3_candidate(candidate)
        # Then: neither arbitrary input nor an open candidate contract is accepted.
        self.assertFalse(result["valid"])

    def test_step3_renderer_rejects_completed_candidate(self) -> None:
        # Given: an otherwise valid rendered plan marked completed.
        candidate = _fixture("tests/fixtures/step3/non-ahd-solar-fr-ca.json")["candidate"]
        candidate["candidate_status"] = "completed"
        output = {key: candidate[key] for key in ("weeks", "mandatory_item_ids", "backlog_item_ids", "vertical_links", "horizontal_links")}
        candidate["solver_input"] = _canonical({"rows": []})
        candidate["solver_output"] = _canonical(output)
        candidate["solver_input_sha256"] = hashlib.sha256(candidate["solver_input"].encode("utf-8")).hexdigest()
        candidate["solver_output_sha256"] = hashlib.sha256(candidate["solver_output"].encode("utf-8")).hexdigest()
        # When: candidate-only rendering is requested.
        # Then: completion before the external gate is blocked.
        with self.assertRaises(Step3RendererError):
            render_step3(candidate)

    def test_step3b_rejects_source_plan_not_equal_to_released_predecessor(self) -> None:
        # Given: a complete adjustment bundle describing a different released-plan hash.
        bundle = copy.deepcopy(_fixture("tests/fixtures/step3b/non-ahd-product-bundle.json"))
        adjustment = _bind_candidate(bundle["adjustment"])
        adjustment.pop("deployment_id", None)
        adjustment["source_artifact_ids"] = ["artifact-predecessor-0001"]
        adjustment["source_plan"].update({"artifact_id": "artifact-predecessor-0001", "revision": 1, "content_sha256": "c" * 64})
        artifact, release = _predecessor("3", "GATE-3")
        bundle.update({"project": _project(), "predecessor_artifact": artifact, "predecessor_release": release})
        # When: operational Step 3B preflight compares source-plan lineage.
        result = validate_step3b_preflight(bundle)
        # Then: the exact released artifact record remains immutable.
        self.assertFalse(result["valid"])

    def test_step4a_rejects_valid_but_unlinked_graph(self) -> None:
        # Given: a valid graph unrelated to every claim in the linked ledger.
        bundle = _fixture("tests/fixtures/step4a/positive-bundle.json")
        graph = _graph("Unlinked graph")
        bundle["briefing"]["jsonld"] = {"level": "basic", "graph": graph, "graph_hash": hashlib.sha256(_canonical(graph).encode("utf-8")).hexdigest()}
        # When: the briefing binds its claims to graph nodes.
        result = validate_step4a_candidate(bundle)
        # Then: independent valid artifacts are not sufficient evidence.
        self.assertFalse(result["valid"])

    def test_step4b_rejects_data_urls_and_stale_safe_content_hashes(self) -> None:
        # Given: safe changed HTML that contains a data URL but retains old asserted hashes.
        bundle = _page_fixture("positive-bundle.json")
        bundle["page_spec"]["html"] = '<a href="DATA:text/plain,probe">probe</a>'
        # When: the page boundary validates untrusted markup and content evidence.
        result = validate_step4b_candidate(bundle)
        # Then: every data scheme and stale content binding is rejected.
        self.assertFalse(result["valid"])

    def test_step4b_renders_and_locally_validates_the_actual_graph(self) -> None:
        # Given: a page specification with a canonical actual graph and matching content hash.
        bundle = _page_fixture("positive-bundle.json")
        graph = _graph("Verified product")
        bundle["page_spec"]["jsonld"] = {"level": "basic", "graph": graph, "graph_hash": hashlib.sha256(_canonical(graph).encode("utf-8")).hexdigest()}
        bundle["page_spec"]["content_sha256"] = _page_content_hash(bundle["page_spec"])
        bundle["staging_evidence"]["content_sha256"] = bundle["page_spec"]["content_sha256"]
        # When: the page is rendered through the candidate-only boundary.
        rendered = render_step4b(bundle)
        validation = validate_local_jsonld_text(rendered, root=ROOT)
        # Then: the emitted block is the validated graph, not metadata.
        self.assertGreater(validation["blocks_found"], 0)
        self.assertTrue(validation["valid"], validation["issues"])


if __name__ == "__main__":
    unittest.main()
