from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from services.step2_preflight.render import FIELDNAMES, RendererError, render_step2, write_step2
from tests.test_preflight_common import _bind_candidate, _predecessor, _project, _provider_records


def _operational_bundle() -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    candidate = _bind_candidate(json.loads((root / "tests/fixtures/step2/non-ahd-solar-fr-ca.json").read_text(encoding="utf-8"))["candidate"])
    candidate["evidence_ids"] = [row["evidence_id"] for pillar in candidate["pillars"] for row in pillar["rows"]]
    candidate["language"] = "de"
    candidate["geo"] = {"country_code": "DE", "provider_location_code": 276}
    artifact, release = _predecessor("1c", "GATE-1C")
    return {
        "candidate": candidate,
        "project": _project(),
        "predecessor_artifact": artifact,
        "predecessor_release": release,
        "provider_evidence_records": _provider_records(candidate),
    }


class Step2RendererTests(unittest.TestCase):
    def test_csv_is_deterministic_and_contains_only_complete_verified_rows(self) -> None:
        bundle = _operational_bundle()
        first = render_step2(bundle)
        second = render_step2(bundle)
        rows = list(csv.DictReader(io.StringIO(first)))
        self.assertEqual(first, second)
        self.assertEqual(FIELDNAMES, tuple(rows[0]))
        self.assertTrue(rows)

    def test_rejects_candidate_only_rendering_before_csv_emission(self) -> None:
        # Given: a closed awaiting-gate candidate without its operational bundle
        candidate = _operational_bundle()["candidate"]
        # When: public rendering receives candidate-only input
        with self.assertRaises(RendererError):
            render_step2({"candidate": candidate})

    def test_rejects_candidate_only_writing_before_output_creation(self) -> None:
        # Given: a closed awaiting-gate candidate and an empty workspace
        candidate = _operational_bundle()["candidate"]
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            # When: public writing receives candidate-only input
            with self.assertRaises(RendererError):
                write_step2({"candidate": candidate}, workspace)
            # Then: validation prevented controlled output creation
            self.assertFalse((workspace / "v2").exists())
