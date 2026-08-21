from __future__ import annotations

import base64
import hashlib
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from services.operator_api.app import AppConfig, create_app
from services.operator_api.repository import WorkspaceRegistration, WorkspaceRegistry
from tests.support.artifact_revisions import PROJECT, RUN, TENANT, outputs, repository, seed_revisions


ROOT = Path(__file__).resolve().parents[1]


class ArtifactReadDiffApiTests(unittest.TestCase):
    def test_reads_exact_canonical_content_and_lists_revisions_in_canonical_order(self) -> None:
        # Given: two immutable revisions with exact textual and binary artifact bytes.
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository(workspace)
            first, second = seed_revisions(workspace, (outputs(primary_bytes=b"before\n", supporting_bytes=b"binary\xff"), outputs(key="idem-revision-0002", target=3, primary_bytes=b"after\n", supporting_bytes=b"supporting")))
            client = TestClient(create_app(WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),)), ROOT, AppConfig(ROOT)))
            prefix = f"/v1/tenants/{TENANT}/projects/{PROJECT}"
            before = _tree_hash(workspace)

            # When: the canonical content, metadata, and run-step revision list are read.
            content = client.get(f"{prefix}/artifacts/{first[0].artifact_id}/content")
            metadata = client.get(f"{prefix}/artifacts/{first[0].artifact_id}")
            revisions = client.get(f"{prefix}/runs/{RUN}/steps/1c/artifact-revisions")

            # Then: exact bytes, revision metadata, and canonical ordering are returned without writes.
            self.assertEqual(200, content.status_code)
            self.assertEqual(b"before\n", base64.b64decode(content.json()["content_base64"], validate=True))
            self.assertEqual(hashlib.sha256(b"before\n").hexdigest(), content.json()["artifact"]["content_sha256"])
            self.assertEqual(2, content.json()["artifact"]["revision"])
            self.assertEqual(200, metadata.status_code)
            self.assertEqual(first[0].artifact_id, metadata.json()["artifact"]["artifact_id"])
            self.assertEqual(200, revisions.status_code)
            self.assertEqual(
                [record.artifact_id for record in (*first, *second)],
                [record["artifact_id"] for record in revisions.json()["artifacts"]],
            )
            self.assertEqual(before, _tree_hash(workspace))

    def test_compares_text_without_mutation_and_rejects_invalid_or_binary_requests(self) -> None:
        # Given: canonical changed, identical, and binary artifact revisions.
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository(workspace)
            first, second = seed_revisions(workspace, (outputs(primary_bytes=b"before\n", supporting_bytes=b"binary\xff"), outputs(key="idem-revision-0002", target=3, primary_bytes=b"after\n", supporting_bytes=b"supporting")))
            client = TestClient(create_app(WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),)), ROOT, AppConfig(ROOT)))
            route = f"/v1/tenants/{TENANT}/projects/{PROJECT}/artifact-revisions/compare"
            before = _tree_hash(workspace)

            # When: callers compare changed, identical, invalid, and binary stored content.
            changed = client.post(route, json={"left_artifact_id": first[0].artifact_id, "right_artifact_id": second[0].artifact_id})
            identical = client.post(route, json={"left_artifact_id": first[0].artifact_id, "right_artifact_id": first[0].artifact_id})
            binary = client.post(route, json={"left_artifact_id": first[1].artifact_id, "right_artifact_id": second[1].artifact_id})
            missing = client.post(route, json={"left_artifact_id": "artifact-missing-0001", "right_artifact_id": first[0].artifact_id})
            mismatch = client.get(f"/v1/tenants/{TENANT}/projects/{PROJECT}/runs/{RUN}/steps/1/artifact-revisions")
            escaped = client.get(f"/v1/tenants/{TENANT}/projects/{PROJECT}/artifacts/..%2Fsecret/content")

            # Then: the unified diff is deterministic and every rejected read leaves canonical files unchanged.
            self.assertEqual(200, changed.status_code)
            self.assertEqual(f"--- {first[0].artifact_id}", changed.json()["unified_diff"].splitlines()[0])
            self.assertIn("-before", changed.json()["unified_diff"])
            self.assertIn("+after", changed.json()["unified_diff"])
            self.assertEqual("", identical.json()["unified_diff"])
            self.assertEqual(422, binary.status_code)
            self.assertEqual(404, missing.status_code)
            self.assertEqual(404, mismatch.status_code)
            self.assertIn(escaped.status_code, {404, 422})
            self.assertEqual(before, _tree_hash(workspace))


def _tree_hash(workspace: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((workspace / "v2/operator").rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(workspace).as_posix().encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()
