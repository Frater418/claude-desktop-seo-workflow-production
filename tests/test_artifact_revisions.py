from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from services.operator_api.artifact_revisions import ArtifactRevisionError
from tests.support.artifact_revisions import INPUT_HASH, PROJECT, RUN, TENANT, outputs, persist_transaction, repository, service, write_projection


class ArtifactRevisionServiceTests(unittest.TestCase):
    def test_persists_first_multi_output_revision_with_exact_bytes_and_readbacks(self) -> None:
        # Given: a current run and an ordered two-output provider response
        with tempfile.TemporaryDirectory() as temporary:
            project_repository = repository(Path(temporary))
            revisions = service(project_repository)
            output_set = outputs(primary_bytes=b"\x00primary", supporting_bytes=b"supporting\xff")
            # When: the immutable output set is persisted
            result = persist_transaction(revisions, output_set)
            # Then: both contract-compliant records and their original bytes are available
            self.assertEqual(2, len(result.records))
            self.assertEqual((), result.records[0].parent_artifact_ids)
            self.assertEqual(2, project_repository.run(TENANT, PROJECT, RUN)["revision"])
            self.assertEqual([record.artifact_id for record in result.records], [record.artifact_id for record in revisions.list_revisions(TENANT, PROJECT, RUN, "1c")])
            self.assertEqual(b"\x00primary", revisions.content_bytes(TENANT, PROJECT, result.records[0].artifact_id))
            self.assertEqual(b"supporting\xff", revisions.content_bytes(TENANT, PROJECT, result.records[1].artifact_id))

    def test_replay_is_stable_but_changed_payload_and_stale_parent_conflict(self) -> None:
        # Given: an already persisted provider output set
        with tempfile.TemporaryDirectory() as temporary:
            project_repository = repository(Path(temporary))
            revisions = service(project_repository)
            initial = outputs()
            first = persist_transaction(revisions, initial)
            # When: the exact set is replayed under its idempotency key
            replay = persist_transaction(revisions, initial)
            # Then: the original records are returned without duplicates
            self.assertEqual(first, replay)
            self.assertEqual(2, len(revisions.list_revisions(TENANT, PROJECT, RUN, "1c")))
            with self.assertRaisesRegex(ArtifactRevisionError, "ERR_IDEMPOTENCY_CONFLICT"):
                persist_transaction(revisions, outputs(primary_bytes=b"changed"))
            with self.assertRaisesRegex(ArtifactRevisionError, "ERR_STALE_REVISION"):
                persist_transaction(revisions, outputs(key="idem-revision-0002"))

    def test_requires_existing_run_matching_input_hash_and_rejects_released_parent_edits(self) -> None:
        # Given: a run that is missing, mismatched, or has a released current artifact
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            project_repository = repository(workspace)
            revisions = service(project_repository)
            write_projection(workspace, f"runs/{RUN}.json", {"tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": "1c", "revision": 1, "input_hash": "b" * 64, "status": "pending"})
            with self.assertRaisesRegex(ArtifactRevisionError, "ERROR_CONTEXT_SOURCE_INVALID"):
                persist_transaction(revisions, outputs())
            write_projection(workspace, f"runs/{RUN}.json", {"tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": "1c", "revision": 1, "input_hash": INPUT_HASH, "status": "pending"})
            result = persist_transaction(revisions, outputs())
            write_projection(workspace, "releases/release-revision-0001.json", {"release_id": "release-revision-0001", "tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": "1c", "artifact_id": result.records[0].artifact_id, "artifact_sha256": result.records[0].content_sha256, "artifact_revision": 2, "status": "released"})
            with self.assertRaisesRegex(ArtifactRevisionError, "ERR_RELEASED_ARTIFACT_IMMUTABLE"):
                persist_transaction(revisions, outputs(key="idem-revision-0002", target=3))

    def test_rejects_missing_run_before_writing_any_artifact(self) -> None:
        # Given: no run projection for an otherwise valid output set
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            project_repository = repository(workspace)
            (workspace / "v2/operator" / f"runs/{RUN}.json").unlink()
            # When: persistence attempts to bind the output set to its run
            with self.assertRaisesRegex(ArtifactRevisionError, "ERROR_DOMAIN_CONTRACT_FILE_MISSING"):
                persist_transaction(service(project_repository), outputs())
            # Then: neither artifact metadata nor content becomes visible
            self.assertEqual([], project_repository.artifacts(TENANT, PROJECT))
