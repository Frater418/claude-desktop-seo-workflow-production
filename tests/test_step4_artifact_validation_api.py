from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from tests.support.step4_artifact_preflight import PROJECT, TENANT, request_body, seed_step4_preflight


ROOT = Path(__file__).resolve().parents[1]


def _snapshot(root: Path) -> tuple[tuple[str, bytes], ...]:
    return tuple(sorted((str(path.relative_to(root)), path.read_bytes()) for path in root.rglob("*") if path.is_file()))


class Step4ArtifactValidationApiTests(unittest.TestCase):
    def test_hash_only_request_is_rejected_at_the_public_request_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            client, _, record = seed_step4_preflight(Path(temporary), ROOT, "4a")
            response = client.post(
                f"/v1/tenants/{TENANT}/projects/{PROJECT}/artifacts/{record.artifact_id}/validate",
                json={"revision": record.revision, "content_sha256": record.content_sha256},
            )
            self.assertEqual(422, response.status_code)

    def test_step4a_preflight_returns_proposed_briefing_and_leaves_workspace_unchanged(self) -> None:
        self._assert_success("4a", "briefing.md", {"qg-domain-contract", "qg-step4a-claims-and-schema"})

    def test_step4b_preflight_returns_proposed_landingpage_without_external_staging_gate(self) -> None:
        self._assert_success("4b", "landingpage.html", {"qg-domain-contract"})

    def test_supporting_documents_require_exact_immutable_count_and_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            client, fixture, record = seed_step4_preflight(workspace, ROOT, "4a")
            baseline = request_body(fixture)
            cases = (([], 422), ([*baseline["supporting_documents"], {}], 422), ([{"artifact_id": "artifact-changed-0001"}], 409))
            for documents, expected_status in cases:
                before = _snapshot(workspace)
                request = {**baseline, "supporting_documents": documents}
                response = client.post(f"/v1/tenants/{TENANT}/projects/{PROJECT}/artifacts/{record.artifact_id}/validate", json=request)
                self.assertEqual(expected_status, response.status_code)
                self.assertEqual(before, _snapshot(workspace))

    def test_specialized_preflight_failure_leaves_workspace_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            client, fixture, record = seed_step4_preflight(workspace, ROOT, "4b")
            request = request_body(fixture)
            bundle = copy.deepcopy(request["bundle"])
            bundle["predecessor_release"]["artifact_sha256"] = "0" * 64
            before = _snapshot(workspace)
            response = client.post(f"/v1/tenants/{TENANT}/projects/{PROJECT}/artifacts/{record.artifact_id}/validate", json={**request, "bundle": bundle})
            self.assertEqual(422, response.status_code)
            self.assertEqual("ERROR_STEP_PREFLIGHT_INVALID", response.json()["code"])
            self.assertEqual(before, _snapshot(workspace))

    def _assert_success(self, step_id: str, view_name: str, expected_gates: set[str]) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            client, fixture, record = seed_step4_preflight(workspace, ROOT, step_id)
            before = _snapshot(workspace)
            response = client.post(f"/v1/tenants/{TENANT}/projects/{PROJECT}/artifacts/{record.artifact_id}/validate", json=request_body(fixture))
            self.assertEqual(200, response.status_code, response.text)
            payload = response.json()
            self.assertEqual(record.artifact_id, payload["artifact_id"])
            self.assertEqual(step_id, payload["step_id"])
            self.assertEqual("step_preflight", payload["validation_mode"])
            self.assertTrue(payload["valid"])
            self.assertEqual({view_name}, {view["name"] for view in payload["derived_views"]})
            self.assertTrue(next(view["content"] for view in payload["derived_views"] if view["name"] == view_name))
            self.assertEqual(expected_gates, {run["quality_gate_id"] for run in payload["quality_gate_runs"]})
            self.assertEqual(before, _snapshot(workspace))
