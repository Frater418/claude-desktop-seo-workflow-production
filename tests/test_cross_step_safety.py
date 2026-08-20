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
from services.step4b_preflight.validator import validate_step4b_preflight
from tests.test_preflight_common import _bind_candidate, _predecessor, _project


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class CrossStepSafetyTests(unittest.TestCase):
    def test_step2_rejects_empty_evidence(self) -> None:
        # Given: an empty Step 2 submission
        bundle: dict = {}
        # When: preflight evaluates it
        result = validate_step2_preflight(bundle)
        # Then: it cannot create a false green
        self.assertFalse(result["valid"])

    def test_step3_rejects_forged_hashes(self) -> None:
        # Given: a complete valid lineage bundle with forged current solver hashes.
        step2 = _bind_candidate(copy.deepcopy(load_json("tests/fixtures/step2/non-ahd-solar-fr-ca.json")["candidate"]))
        step2["evidence_ids"] = [row["evidence_id"] for pillar in step2["pillars"] for row in pillar["rows"]]
        step2["language"] = "de"
        step2["geo"] = {"country_code": "DE", "provider_location_code": 276}
        candidate = _bind_candidate(copy.deepcopy(load_json("tests/fixtures/step3/non-ahd-solar-fr-ca.json")["candidate"]))
        candidate.pop("input_sha256", None)
        candidate.pop("output_sha256", None)
        projection = {"rows": [{"evidence_id": row["evidence_id"], "keyword": row["keyword"], "pillar_id": pillar["pillar_id"], "provider": row["provider"], "raw_response_sha256": row["raw_response_sha256"]} for pillar in step2["pillars"] for row in pillar["rows"]]}
        candidate["solver_input"] = json.dumps(projection, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        candidate["solver_output"] = json.dumps({key: candidate[key] for key in ("weeks", "mandatory_item_ids", "backlog_item_ids", "vertical_links", "horizontal_links")}, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        candidate["solver_input_sha256"] = hashlib.sha256(candidate["solver_input"].encode("utf-8")).hexdigest()
        candidate["solver_output_sha256"] = hashlib.sha256(candidate["solver_output"].encode("utf-8")).hexdigest()
        predecessor_content = json.dumps(step2, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        artifact, release = _predecessor("2", "GATE-2")
        artifact["content_sha256"] = hashlib.sha256(predecessor_content.encode("utf-8")).hexdigest()
        release["artifact_sha256"] = artifact["content_sha256"]
        bundle = {"candidate": candidate, "project": _project(), "predecessor_artifact": artifact, "predecessor_release": release, "predecessor_content": predecessor_content}
        bundle["candidate"]["solver_input_sha256"] = "z" * 64
        bundle["candidate"]["solver_output_sha256"] = "z" * 64
        # When: preflight evaluates it
        result = validate_step3_preflight(bundle)
        # Then: hashes are rejected
        self.assertFalse(result["valid"])

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

    def test_step4b_rejects_invalid_url_and_script_markup(self) -> None:
        # Given: a valid generic page with hostile markup and a malformed URL
        bundle = load_json("tests/fixtures/step4b/positive-bundle.json")
        bundle = copy.deepcopy(bundle)
        bundle["page_spec"]["html"] = "<script>window.audit_marker=1</script>"
        bundle["page_spec"]["canonical_url"] = "not-a-uri"
        # When: preflight evaluates the page
        result = validate_step4b_preflight(bundle)
        # Then: neither unsafe markup nor an invalid URL is accepted
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
