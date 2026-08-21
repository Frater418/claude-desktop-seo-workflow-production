from __future__ import annotations

import tempfile
import unittest
import json
import socket
from pathlib import Path
from unittest.mock import patch

from services.operator_api.artifact_revisions import ArtifactRevisionError

from tests.support.artifact_revisions import PROJECT, RUN, TENANT, outputs, persist_transaction, repository, service


class ArtifactRevisionRecoveryTests(unittest.TestCase):
    def test_mid_write_failure_keeps_records_invisible_and_recovery_materializes_once(self) -> None:
        # Given: an injected failure after the first immutable content file is written
        with tempfile.TemporaryDirectory() as temporary:
            project_repository = repository(Path(temporary))
            revisions = service(project_repository)
            original = revisions._repository._write_once_content
            calls = 0

            def fail_after_first(*args: object) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected")
                original(*args)

            # When: persistence stops during content materialization
            with patch.object(revisions._repository, "_write_once_content", side_effect=fail_after_first):
                with self.assertRaisesRegex(ArtifactRevisionError, "ERROR_ARTIFACT_PERSISTENCE"):
                    persist_transaction(revisions, outputs())
            # Then: no partial output set is observable and recovery publishes exactly once
            self.assertEqual((), revisions.list_revisions(TENANT, PROJECT, RUN, "1c"))
            recovered = revisions.recover_output_set(TENANT, PROJECT, RUN, "1c", "idem-revision-0001")
            self.assertEqual(2, len(recovered.records))
            self.assertEqual(2, len(revisions.list_revisions(TENANT, PROJECT, RUN, "1c")))
            self.assertEqual(recovered, revisions.recover_output_set(TENANT, PROJECT, RUN, "1c", "idem-revision-0001"))

    def test_rejects_active_parent_lock_and_contained_content_paths(self) -> None:
        # Given: a current revision lock and a path escaping artifact identity
        with tempfile.TemporaryDirectory() as temporary:
            project_repository = repository(Path(temporary))
            revisions = service(project_repository)
            lock = Path(temporary) / "v2/operator/artifact-revision-locks/run-revision-0001--1c.lock"
            lock.parent.mkdir(parents=True)
            # When: a competing writer holds a process-owned lock and an unsafe content lookup is attempted
            with revisions._repository.lock(TENANT, PROJECT, RUN, "1c"):
                with self.assertRaisesRegex(ArtifactRevisionError, "ERR_CONCURRENT_PARENT_CONFLICT"):
                    persist_transaction(revisions, outputs())
            with self.assertRaisesRegex(ArtifactRevisionError, "ERR_TENANT_ISOLATION"):
                revisions.content_bytes(TENANT, PROJECT, "../escape")
            # Then: no content was written outside the registered workspace
            self.assertFalse((Path(temporary).parent / "escape.md").exists())

    def test_recovers_a_lock_owned_by_a_confirmed_dead_local_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_repository = repository(Path(temporary))
            revisions = service(project_repository)
            lock = Path(temporary) / "v2/operator/artifact-revision-locks/run-revision-0001--1c.lock"
            lock.parent.mkdir(parents=True)
            lock.write_text(json.dumps({"schema_version": 1, "pid": 99999999, "hostname": socket.gethostname(), "token": "dead"}), encoding="utf-8")

            persisted = persist_transaction(revisions, outputs())

            self.assertEqual(2, len(persisted.records))
            self.assertFalse(lock.exists())

    def test_old_revision_bytes_are_never_overwritten(self) -> None:
        # Given: a persisted first revision and a second revision with distinct bytes
        with tempfile.TemporaryDirectory() as temporary:
            project_repository = repository(Path(temporary))
            revisions = service(project_repository)
            first = persist_transaction(revisions, outputs())
            second = persist_transaction(revisions, outputs(key="idem-revision-0002", target=3, primary_bytes=b"new-primary", supporting_bytes=b"new-supporting"))
            # When: both immutable revisions are read after the successor exists
            original = revisions.content_bytes(TENANT, PROJECT, first.records[0].artifact_id)
            latest = revisions.content_bytes(TENANT, PROJECT, second.records[0].artifact_id)
            # Then: the first exact byte sequence is unchanged and lineage is contract-specific
            self.assertEqual(b"primary", original)
            self.assertEqual(b"new-primary", latest)
            self.assertEqual((first.records[0].artifact_id,), second.records[0].parent_artifact_ids)

    def test_cleanup_failure_after_commit_keeps_visible_revision_and_replay_rematerializes(self) -> None:
        # Given: cleanup fails after the idempotency marker and visible projections commit
        with tempfile.TemporaryDirectory() as temporary:
            project_repository = repository(Path(temporary))
            revisions = service(project_repository)
            with patch.object(revisions._repository, "_remove_if_present", side_effect=OSError("injected")):
                # When: the artifact transaction reaches its commit point
                committed = persist_transaction(revisions, outputs())
            recovered_run = project_repository.run(TENANT, PROJECT, RUN)
            recovered_run["revision"] = 1
            project_repository.write_run(TENANT, PROJECT, recovered_run)
            # Then: the committed revision stays visible and replay verifies the same projections
            replayed = persist_transaction(revisions, outputs())
            self.assertEqual(committed, replayed)
            self.assertEqual(2, project_repository.run(TENANT, PROJECT, RUN)["revision"])
            self.assertEqual(2, len(revisions.list_revisions(TENANT, PROJECT, RUN, "1c")))
