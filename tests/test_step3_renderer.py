from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from services.step3_preflight.render import RendererError, render_step3, write_step3
from services.step3_preflight.validator import step2_solver_projection
from tests.test_preflight_common import _bind_candidate, _predecessor, _project


def _canonical(value: dict[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _operational_bundle() -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    step2 = _bind_candidate(json.loads((root / "tests/fixtures/step2/non-ahd-solar-fr-ca.json").read_text(encoding="utf-8"))["candidate"])
    step2["evidence_ids"] = [row["evidence_id"] for pillar in step2["pillars"] for row in pillar["rows"]]
    step2["language"] = "de"
    step2["geo"] = {"country_code": "DE", "provider_location_code": 276}
    candidate = _bind_candidate(json.loads((root / "tests/fixtures/step3/non-ahd-solar-fr-ca.json").read_text(encoding="utf-8"))["candidate"])
    candidate.pop("input_sha256", None)
    candidate.pop("output_sha256", None)
    candidate["solver_input"] = _canonical(step2_solver_projection(step2))
    candidate["solver_output"] = _canonical({key: candidate[key] for key in ("weeks", "mandatory_item_ids", "backlog_item_ids", "vertical_links", "horizontal_links")})
    candidate["solver_input_sha256"] = hashlib.sha256(candidate["solver_input"].encode("utf-8")).hexdigest()
    candidate["solver_output_sha256"] = hashlib.sha256(candidate["solver_output"].encode("utf-8")).hexdigest()
    artifact, release = _predecessor("2", "GATE-2")
    predecessor_content = _canonical(step2)
    artifact["content_sha256"] = hashlib.sha256(predecessor_content.encode("utf-8")).hexdigest()
    release["artifact_sha256"] = artifact["content_sha256"]
    return {
        "candidate": candidate,
        "project": _project(),
        "predecessor_artifact": artifact,
        "predecessor_release": release,
        "predecessor_content": predecessor_content,
    }


class Step3RendererTests(unittest.TestCase):
    def test_plan_is_deterministic_and_contains_weeks_backlog_and_link_graphs(self) -> None:
        bundle = _operational_bundle()
        first = render_step3(bundle)
        self.assertEqual(first, render_step3(bundle))
        self.assertEqual(17, first.count("## Week "))
        candidate = bundle["candidate"]
        self.assertIn(candidate["backlog_item_ids"][0], first)
        self.assertIn(candidate["vertical_links"][0]["target_pillar_id"], first)
        self.assertIn(candidate["horizontal_links"][0]["target_item_id"], first)

    def test_rejects_candidate_only_rendering_before_markdown_emission(self) -> None:
        # Given: a closed awaiting-gate plan candidate without released Step 2 lineage
        candidate = _operational_bundle()["candidate"]
        # When: public rendering receives candidate-only input
        with self.assertRaises(RendererError):
            render_step3({"candidate": candidate})

    def test_rejects_candidate_only_writing_before_output_creation(self) -> None:
        # Given: a closed awaiting-gate plan candidate and an empty workspace
        candidate = _operational_bundle()["candidate"]
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            # When: public writing receives candidate-only input
            with self.assertRaises(RendererError):
                write_step3({"candidate": candidate}, workspace)
            # Then: validation prevented controlled output creation
            self.assertFalse((workspace / "v2").exists())
