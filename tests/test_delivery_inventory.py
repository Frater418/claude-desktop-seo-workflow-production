"""Deterministic delivery inventory and eligibility policy tests.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import json
import os
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from pathlib import Path

from services.delivery.inventory import (
    CanonicalDeliveryRecords,
    DeliveryInventoryError,
    DeliveryInventoryRequest,
    SelectedWorkspaceFile,
    WorkspaceRegistration,
    collect_inventory,
)
from services.delivery.policy import FinalReadinessPolicy, Step4bStagingReadiness, evaluate_checkpoint, evaluate_final


TENANT_ID = "tenant-demo"
PROJECT_ID = "project-demo"
HASH = "a" * 64
DELIVERY_HASH = hashlib.sha256(b"delivery").hexdigest()
DELIVERABLES = (
    ("1", "strategy", "strategy/topic-inventory.json"),
    ("1b", "architecture", "architecture/page-map.json"),
    ("1c", "design", "design/design-system.json"),
    ("2", "keyword-research", "keyword-research/evidence.json"),
    ("3", "roadmap", "roadmap/plan.json"),
    ("4a", "copywriter-handoff", "copywriter-handoff/briefing.json"),
    ("4b", "developer-handoff", "developer-handoff/page-spec.json"),
)


class DeliveryInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.workspace = WorkspaceRegistration(TENANT_ID, PROJECT_ID, self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _artifact(self, step_id: str, deliverable_id: str, status: str = "approved") -> dict[str, object]:
        return {
            "artifact_id": f"artifact-{deliverable_id}-0001",
            "tenant_id": TENANT_ID,
            "project_id": PROJECT_ID,
            "run_id": "run-step1-0001",
            "step_id": step_id,
            "revision": 1,
            "input_hash": HASH,
            "content_sha256": DELIVERY_HASH,
            "contract_version": "1.0.0",
            "producer_version": "test-producer",
            "storage_key": f"tenants/{TENANT_ID}/projects/{PROJECT_ID}/runs/run-step1-0001/artifacts/artifact-{deliverable_id}-0001/content.json",
            "created_at": "2026-08-20T00:00:00Z",
        }

    def _release(self, artifact: dict[str, object]) -> dict[str, object]:
        gate = {"0": "GATE-0", "1": "GATE-1", "1b": "GATE-1B", "1c": "GATE-1C", "2": "GATE-2", "3": "GATE-3", "3b": "GATE-3B", "4a": "GATE-4A", "4b": "GATE-4B"}[str(artifact["step_id"])]
        return {
            "release_id": f"release-{artifact['artifact_id']}",
            "tenant_id": TENANT_ID,
            "project_id": PROJECT_ID,
            "artifact_id": artifact["artifact_id"],
            "artifact_sha256": artifact["content_sha256"],
            "artifact_revision": artifact["revision"],
            "run_id": artifact["run_id"],
            "step_id": artifact["step_id"],
            "gate_id": gate,
            "approval_id": "approval-demo-0001",
            "policy_version": "1.0.0",
            "status": "released",
            "released_at": "2026-08-20T00:00:00Z",
        }

    def _records(self, artifacts: tuple[dict[str, object], ...], releases: tuple[dict[str, object], ...]) -> CanonicalDeliveryRecords:
        scope = {"tenant_id": TENANT_ID, "project_id": PROJECT_ID}
        artifact = artifacts[0]
        artifact_id = str(artifact.get("artifact_id", "artifact-strategy-0001"))
        return CanonicalDeliveryRecords(
            project_v2=self._project_v2(),
            workflow={**scope, "initial_edges": [{"from_step_id": before, "to_step_id": after} for before, after in zip(("0", "1", "1b", "1c", "2", "3", "4a"), ("1", "1b", "1c", "2", "3", "4a", "4b"), strict=True)], "sideflows": [{"step_id": "3b", "status": "not_due"}]},
            runs=({**scope, "run_id": "run-step1-0001", "step_id": "1", "gate_id": "GATE-1", "revision": 1, "input_hash": HASH, "status": "pending", "attempt": 1, "created_at": "2026-08-20T00:00:00Z", "gate_context": {"local_workflow": True}},),
            artifacts=artifacts,
            releases=releases,
            gates=({"quality_gate_run_id": "qgr-step1-0001", "quality_gate_id": "qg-step-1", "human_gate_id": "GATE-1", "tenant_id": TENANT_ID, "run_id": "run-step1-0001", "step_id": "1", "artifact_id": artifact_id, "artifact_sha256": DELIVERY_HASH, "artifact_revision": 1, "registry_version": "1.0.0", "policy_version": "1.0.0", "result": "passed", "evidence": {"check": "passed"}, "checked_at": "2026-08-20T00:00:00Z", "checker_version": "test"},),
            tasks=({**scope, "task_id": "task-demo-0001", "run_id": "run-step1-0001", "step_id": "1", "task_type": "missing_input", "title": "Provide the missing crawl export", "description": "Upload the verified crawl export before the Step 1 gate can continue.", "owner_role": "operator", "priority": "high", "blocking_scope": "step", "artifact": {"artifact_id": artifact_id, "content_sha256": DELIVERY_HASH, "revision": 1}, "evidence": [{"evidence_id": "evidence-crawl-0001", "content_sha256": HASH}], "acceptance_criteria": ["The crawl export is stored as immutable evidence."], "resolution_method": "provide_input", "status": "open", "operator_action": {"action": "request_input", "requested_by": "operator-raphael", "requested_at": "2026-08-19T12:00:00Z", "instructions": "Attach the crawl export evidence."}},),
            assignments=({**scope, "assignment_id": "assignment-demo-0001"},),
            reviews=({**scope, "review_id": "review-demo-0001"},),
            blockers=({**scope, "blocker_id": "blocker-demo-0001"},),
            reports=({**scope, "report_id": "report-demo-0001"},),
        )

    def _project_v2(self) -> dict[str, object]:
        fixture = next((Path(__file__).parent / "fixtures" / "domain" / "real-customer-matrix").glob("*.json"))
        project = json.loads(fixture.read_text(encoding="utf-8"))
        project["project_id"] = PROJECT_ID
        project["tenant"]["tenant_id"] = TENANT_ID
        return project

    def _request(
        self,
        artifacts: tuple[dict[str, object], ...],
        releases: tuple[dict[str, object], ...],
        selections: tuple[SelectedWorkspaceFile, ...] = (),
        include_drafts: bool = False,
    ) -> DeliveryInventoryRequest:
        return DeliveryInventoryRequest(self.workspace, self._records(artifacts, releases), selections, include_drafts)

    def _write_selection(self, artifact: dict[str, object], output_path: str, content: bytes = b"delivery") -> SelectedWorkspaceFile:
        source_path = f"source/{artifact['artifact_id']}.json"
        path = self.root / source_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        content_sha256 = hashlib.sha256(content).hexdigest()
        return SelectedWorkspaceFile(source_path, output_path, content_sha256, str(artifact["artifact_id"]))

    def test_collects_all_records_files_and_uses_canonical_order(self) -> None:
        artifacts = tuple(self._artifact(step, deliverable) for step, deliverable, _ in reversed(DELIVERABLES))
        releases = tuple(self._release(item) for item in reversed(artifacts))
        selections = tuple(self._write_selection(artifact, output) for artifact, (_, _, output) in zip(artifacts, reversed(DELIVERABLES), strict=True))

        inventory = collect_inventory(self._request(artifacts, releases, selections))

        self.assertEqual(tuple(item[1] for item in DELIVERABLES), tuple(item.deliverable_id for item in inventory.deliverables))
        self.assertEqual(tuple(sorted(item.output_path for item in inventory.files)), tuple(item.output_path for item in inventory.files))
        self.assertEqual(hashlib.sha256(b"delivery").hexdigest(), inventory.files[0].content_sha256)
        self.assertEqual(DELIVERY_HASH, inventory.artifacts[0].content_sha256)
        self.assertEqual("project-demo", inventory.project_v2.record_id)

    def test_checkpoint_succeeds_and_reports_exact_missing_deliverables(self) -> None:
        artifact = self._artifact("1", "strategy")
        inventory = collect_inventory(self._request((artifact,), (self._release(artifact),), (self._write_selection(artifact, "strategy/topic-inventory.json"),)))

        result = evaluate_checkpoint(inventory)

        self.assertTrue(result.eligible)
        self.assertEqual(("architecture", "design", "keyword-research", "roadmap", "copywriter-handoff", "developer-handoff"), result.missing_deliverable_ids)
        self.assertEqual((), result.errors)

    def test_final_succeeds_with_all_released_deliverables(self) -> None:
        artifacts = tuple(self._artifact(step, deliverable) for step, deliverable, _ in DELIVERABLES)
        inventory = collect_inventory(self._request(artifacts, tuple(self._release(item) for item in artifacts), tuple(self._write_selection(item, output) for item, (_, _, output) in zip(artifacts, DELIVERABLES, strict=True))))

        result = evaluate_final(inventory)

        self.assertTrue(result.eligible)
        self.assertEqual((), result.missing_deliverable_ids)

    def test_final_fails_closed_before_step_4b_is_released(self) -> None:
        artifacts = tuple(self._artifact(step, deliverable) for step, deliverable, _ in DELIVERABLES)
        releases = tuple(self._release(item) for item in artifacts if item["step_id"] != "4b")
        inventory = collect_inventory(self._request(artifacts, releases))

        result = evaluate_final(inventory)

        self.assertFalse(result.eligible)
        self.assertIn("DELIVERY_FINAL_STEP_4B_NOT_READY", {error.code for error in result.errors})

    def test_final_fails_when_a_required_released_file_is_missing(self) -> None:
        artifacts = tuple(self._artifact(step, deliverable) for step, deliverable, _ in DELIVERABLES)
        releases = tuple(self._release(item) for item in artifacts)
        selections = tuple(self._write_selection(item, output) for item, (_, _, output) in zip(artifacts[:-1], DELIVERABLES[:-1], strict=True))
        inventory = collect_inventory(self._request(artifacts, releases, selections))

        result = evaluate_final(inventory)

        self.assertFalse(result.eligible)
        self.assertEqual(("developer-handoff",), result.missing_deliverable_ids)

    def test_drafts_are_included_only_when_explicitly_requested(self) -> None:
        draft = self._artifact("1", "strategy", "draft")
        selection = self._write_selection(draft, "strategy/topic-inventory.json")

        excluded = collect_inventory(self._request((draft,), (), (selection,)))
        included = collect_inventory(self._request((draft,), (), (selection,), include_drafts=True))

        self.assertEqual((), excluded.deliverables)
        self.assertEqual(("draft",), tuple(item.release_status for item in included.deliverables))

    def test_staging_ready_step_4b_requires_explicit_workflow_policy(self) -> None:
        artifacts = tuple(self._artifact(step, deliverable) for step, deliverable, _ in DELIVERABLES)
        releases = tuple(self._release(item) for item in artifacts if item["step_id"] != "4b")
        selections = tuple(self._write_selection(item, output) for item, (_, _, output) in zip(artifacts, DELIVERABLES, strict=True))
        inventory = collect_inventory(self._request(artifacts, releases, selections))

        result = evaluate_final(inventory)

        self.assertFalse(result.eligible)

    def test_rejects_tenant_mismatch_and_malformed_record(self) -> None:
        artifact = self._artifact("1", "strategy")
        mismatched = dict(artifact, tenant_id="tenant-other")

        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_SOURCE_SCOPE_INVALID"):
            collect_inventory(self._request((mismatched,), ()))
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_SOURCE_RECORD_MALFORMED"):
            collect_inventory(self._request(({"tenant_id": TENANT_ID},), ()))

    def test_rejects_unsafe_selected_files(self) -> None:
        artifact = self._artifact("1", "strategy")
        source = self._write_selection(artifact, "strategy/topic-inventory.json")
        cases = (
            (SelectedWorkspaceFile("../escape.json", source.output_path, source.source_sha256, source.artifact_id), "DELIVERY_PATH_TRAVERSAL"),
            (SelectedWorkspaceFile(str(self.root / "source" / "x.json"), source.output_path, source.source_sha256, source.artifact_id), "DELIVERY_PATH_ABSOLUTE"),
            (SelectedWorkspaceFile("source", source.output_path, source.source_sha256, source.artifact_id), "DELIVERY_FILE_NOT_REGULAR"),
            (SelectedWorkspaceFile(source.source_path, "secrets/token.json", source.source_sha256, source.artifact_id), "DELIVERY_FILE_CREDENTIAL_LIKE"),
            (SelectedWorkspaceFile(source.source_path, "/absolute-output.json", source.source_sha256, source.artifact_id), "DELIVERY_PATH_ABSOLUTE"),
        )

        for selection, code in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(DeliveryInventoryError, code):
                    collect_inventory(self._request((artifact,), (self._release(artifact),), (selection,)))

    def test_rejects_symlink_hash_mismatch_and_duplicate_output_path(self) -> None:
        artifact = self._artifact("1", "strategy")
        selection = self._write_selection(artifact, "strategy/topic-inventory.json")
        linked = self.root / "source" / "linked.json"
        os.symlink(self.root / selection.source_path, linked)
        wrong_hash = SelectedWorkspaceFile(selection.source_path, selection.output_path, HASH, selection.artifact_id)
        duplicate = SelectedWorkspaceFile(selection.source_path, selection.output_path, selection.source_sha256, "artifact-other-0001")

        for selected, code in (((SelectedWorkspaceFile("source/linked.json", selection.output_path, selection.source_sha256, selection.artifact_id),), "DELIVERY_PATH_LINK"), ((wrong_hash,), "DELIVERY_FILE_HASH_MISMATCH"), ((selection, duplicate), "DELIVERY_OUTPUT_PATH_DUPLICATE")):
            with self.subTest(code=code):
                with self.assertRaisesRegex(DeliveryInventoryError, code):
                    collect_inventory(self._request((artifact,), (self._release(artifact),), selected))

    def test_rejects_link_ancestor(self) -> None:
        artifact = self._artifact("1", "strategy")
        target = self.root / "target"
        target.mkdir()
        (target / "artifact.json").write_bytes(b"delivery")
        os.symlink(target, self.root / "linked")
        selection = SelectedWorkspaceFile("linked/artifact.json", "strategy/topic-inventory.json", hashlib.sha256(b"delivery").hexdigest(), str(artifact["artifact_id"]))

        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_PATH_LINK"):
            collect_inventory(self._request((artifact,), (self._release(artifact),), (selection,)))

    def test_rejects_workspace_root_with_linked_ancestor(self) -> None:
        artifact = self._artifact("1", "strategy")
        target = self.root / "target"
        target.mkdir()
        registered = target / "registered"
        registered.mkdir()
        linked_ancestor = self.root / "linked-ancestor"
        os.symlink(target, linked_ancestor)
        workspace = WorkspaceRegistration(TENANT_ID, PROJECT_ID, linked_ancestor / "registered")

        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_PATH_LINK"):
            collect_inventory(DeliveryInventoryRequest(workspace, self._records((artifact,), ()), ()))

    def test_rejects_simulated_reparse_point(self) -> None:
        artifact = self._artifact("1", "strategy")
        original_lstat = os.lstat

        def reparse_lstat(path: str | bytes | os.PathLike[str] | os.PathLike[bytes]) -> os.stat_result | SimpleNamespace:
            metadata = original_lstat(path)
            if Path(path) == self.root:
                return SimpleNamespace(st_mode=metadata.st_mode, st_file_attributes=0x400)
            return metadata

        with patch("services.delivery.path_safety.os.lstat", side_effect=reparse_lstat):
            with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_PATH_LINK"):
                collect_inventory(self._request((artifact,), ()))

    def test_does_not_mutate_injected_records(self) -> None:
        artifact = self._artifact("1", "strategy")
        records = self._records((artifact,), (self._release(artifact),))
        selection = self._write_selection(artifact, "strategy/topic-inventory.json")
        before = copy.deepcopy(records)

        collect_inventory(DeliveryInventoryRequest(self.workspace, records, (selection,)))

        self.assertEqual(before, records)

    def test_rejects_forged_duplicate_and_mismatched_release_bindings(self) -> None:
        artifact = self._artifact("1", "strategy")
        valid = self._release(artifact)
        cases = ((dict(valid, artifact_id="artifact-unknown-0001"), "DELIVERY_RELEASE_UNKNOWN_ARTIFACT"), (dict(valid, artifact_revision=2), "DELIVERY_RELEASE_BINDING_MISMATCH"), (dict(valid, artifact_sha256=HASH), "DELIVERY_RELEASE_BINDING_MISMATCH"), (dict(valid, run_id="run-other-0001"), "DELIVERY_RELEASE_BINDING_MISMATCH"), (dict(valid, step_id="2"), "DELIVERY_RELEASE_MALFORMED"))

        for release, code in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(DeliveryInventoryError, code):
                    collect_inventory(self._request((artifact,), (release,)))
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_DUPLICATE_RELEASE_BINDING"):
            collect_inventory(self._request((artifact,), (valid, dict(valid, release_id="release-second-0001"))))

    def test_rejects_noncanonical_completed_task_and_duplicate_ids(self) -> None:
        artifact = self._artifact("1", "strategy")
        records = self._records((artifact, dict(artifact)), ())
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_DUPLICATE_RECORD_ID"):
            collect_inventory(DeliveryInventoryRequest(self.workspace, records, ()))
        task = dict(self._records((artifact,), ()).tasks[0], status="completed")
        records = replace(self._records((artifact,), ()), tasks=(task,))
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_SOURCE_RECORD_MALFORMED"):
            collect_inventory(DeliveryInventoryRequest(self.workspace, records, ()))

    def test_rejects_windows_host_paths_and_credential_names(self) -> None:
        artifact = self._artifact("1", "strategy")
        selection = self._write_selection(artifact, "strategy/topic-inventory.json")
        unsafe = ("C:relative.json", "C:\\absolute.json", "\\\\host\\share\\file", "\\\\?\\C:\\file", "\\\\.\\pipe\\file", "api_key.json", "apikey.json", ".npmrc", ".netrc", "certificate.pfx")
        for value in unsafe:
            with self.subTest(value=value):
                with self.assertRaises(DeliveryInventoryError):
                    collect_inventory(self._request((artifact,), (self._release(artifact),), (SelectedWorkspaceFile(value, selection.output_path, selection.source_sha256, selection.artifact_id),)))

    def test_staging_requires_explicit_policy_and_matching_evidence(self) -> None:
        artifacts = tuple(self._artifact(step, deliverable) for step, deliverable, _ in DELIVERABLES)
        releases = tuple(self._release(item) for item in artifacts if item["step_id"] != "4b")
        selections = tuple(self._write_selection(item, output) for item, (_, _, output) in zip(artifacts, DELIVERABLES, strict=True))
        inventory = collect_inventory(self._request(artifacts, releases, selections, include_drafts=True))
        step_4b = artifacts[-1]
        evidence = Step4bStagingReadiness(str(step_4b["artifact_id"]), 1, DELIVERY_HASH)

        self.assertFalse(evaluate_final(inventory, staging_readiness=evidence).eligible)
        self.assertFalse(evaluate_final(inventory, FinalReadinessPolicy(True), Step4bStagingReadiness(evidence.artifact_id, 2, evidence.artifact_sha256)).eligible)
        self.assertTrue(evaluate_final(inventory, FinalReadinessPolicy(True), evidence).eligible)

    def test_rejects_release_contract_gaps_and_payload_host_paths(self) -> None:
        artifact = self._artifact("1", "strategy")
        for field in ("approval_id", "gate_id", "policy_version", "released_at"):
            release = self._release(artifact)
            release.pop(field)
            with self.subTest(field=field):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_RELEASE_MALFORMED"):
                    collect_inventory(self._request((artifact,), (release,)))
        for host_path in ("/home/operator/customer", "C:\\Users\\operator\\customer", "\\\\host\\share\\customer"):
            records = self._records((artifact,), ())
            assignment = dict(records.assignments[0], metadata={"host_path": host_path})
            with self.subTest(host_path=host_path):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_PATH_ABSOLUTE"):
                    collect_inventory(replace(self._request((artifact,), ()), records=replace(records, assignments=(assignment,))))

    def test_rejects_exact_credential_names_and_root_link(self) -> None:
        artifact = self._artifact("1", "strategy")
        for name in ("api_key", "apikey", ".npmrc", ".netrc", "certificate.pfx", "certificate.p12", "certificate.pem", "certificate.key"):
            path = self.root / name
            path.write_bytes(b"delivery")
            selection = SelectedWorkspaceFile(name, "strategy/topic-inventory.json", DELIVERY_HASH, str(artifact["artifact_id"]))
            with self.subTest(name=name):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_FILE_CREDENTIAL_LIKE"):
                    collect_inventory(self._request((artifact,), (self._release(artifact),), (selection,)))
        target = self.root / "target"
        target.mkdir()
        link = self.root / "workspace-link"
        os.symlink(target, link)
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_PATH_LINK"):
            collect_inventory(DeliveryInventoryRequest(WorkspaceRegistration(TENANT_ID, PROJECT_ID, link), self._records((artifact,), ()), ()))

    def test_rejects_hash_shape_duplicate_task_and_nested_path(self) -> None:
        artifact = self._artifact("1", "strategy")
        for field, target in (("input_hash", artifact), ("content_sha256", artifact), ("artifact_sha256", self._release(artifact))):
            changed = dict(target, **{field: "not-a-hash"})
            records = self._records((artifact if target is not artifact else changed,), (changed,) if target is not artifact else ())
            with self.subTest(field=field):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_RELEASE_MALFORMED" if field == "artifact_sha256" else "DELIVERY_SOURCE_RECORD_MALFORMED"):
                    collect_inventory(DeliveryInventoryRequest(self.workspace, records, ()))
        task = self._records((artifact,), ()).tasks[0]
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_DUPLICATE_RECORD_ID"):
            collect_inventory(replace(self._request((artifact,), ()), records=replace(self._records((artifact,), ()), tasks=(task, dict(task)))) )
        records = self._records((artifact,), ())
        report = dict(records.reports[0], metadata=[{"path": "/home/operator/customer"}])
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_PATH_ABSOLUTE"):
            collect_inventory(replace(self._request((artifact,), ()), records=replace(records, reports=(report,))))

    def test_rejects_missing_project_identity_for_every_scoped_record(self) -> None:
        artifact = self._artifact("1", "strategy")
        release = self._release(artifact)
        records = self._records((artifact,), (release,))
        for attribute in ("runs", "artifacts", "releases", "tasks", "assignments", "reviews", "blockers", "reports"):
            record = dict(getattr(records, attribute)[0])
            record.pop("project_id")
            with self.subTest(attribute=attribute):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_SOURCE_SCOPE_INVALID"):
                    collect_inventory(replace(self._request((artifact,), (release,)), records=replace(records, **{attribute: (record,)})))

    def test_accepts_canonical_gate_without_project_identity(self) -> None:
        artifact = self._artifact("1", "strategy")
        inventory = collect_inventory(self._request((artifact,), ()))

        self.assertNotIn("project_id", inventory.gates[0].payload)
        self.assertEqual("qgr-step1-0001", inventory.gates[0].record_id)

    def test_rejects_artifact_schema_gaps_with_exact_code(self) -> None:
        artifact = self._artifact("1", "strategy")
        missing_contract = dict(artifact)
        missing_contract.pop("contract_version")
        missing_producer = dict(artifact)
        missing_producer.pop("producer_version")
        invalid = (
            missing_contract,
            missing_producer,
            dict(artifact, storage_key="artifacts/strategy.json"),
            dict(artifact, created_at="2026-08-20T00:00:00"),
            dict(artifact, created_at="not-a-date"),
            dict(artifact, unexpected="value"),
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_SOURCE_RECORD_MALFORMED"):
                    collect_inventory(self._request((value,), ()))

    def test_accepts_canonical_resolved_operator_task_with_evidence(self) -> None:
        artifact = self._artifact("1", "strategy")
        records = self._records((artifact,), ())
        task = dict(records.tasks[0], status="resolved", operator_action={"action": "resolve_task", "requested_by": "operator-raphael", "requested_at": "2026-08-20T12:00:00Z", "instructions": "The crawl export is verified."})

        inventory = collect_inventory(replace(self._request((artifact,), ()), records=replace(records, tasks=(task,))))

        self.assertEqual("resolved", inventory.tasks[0].payload["status"])

    def test_rejects_empty_or_malformed_resolved_task_evidence(self) -> None:
        artifact = self._artifact("1", "strategy")
        records = self._records((artifact,), ())
        task = dict(records.tasks[0], status="resolved", operator_action={"action": "resolve_task", "requested_by": "operator-raphael", "requested_at": "2026-08-20T12:00:00Z", "instructions": "The crawl export is verified."})
        for evidence in ([], [{"evidence_id": "", "content_sha256": HASH}]):
            with self.subTest(evidence=evidence):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_SOURCE_RECORD_MALFORMED"):
                    collect_inventory(replace(self._request((artifact,), ()), records=replace(records, tasks=(dict(task, evidence=evidence),))))

    def test_release_contract_rejects_ids_dates_extras_and_wrong_gate(self) -> None:
        artifact = self._artifact("1", "strategy")
        invalid = [
            dict(self._release(artifact), release_id="release-invalid"),
            dict(self._release(artifact), approval_id="approval-invalid"),
            dict(self._release(artifact), released_at="not-a-date"),
            dict(self._release(artifact), released_at="2026-08-20T00:00:00"),
            dict(self._release(artifact), gate_id="GATE-2"),
            dict(self._release(artifact), unexpected="value"),
        ]
        for release in invalid:
            with self.subTest(release=release):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_RELEASE_MALFORMED"):
                    collect_inventory(self._request((artifact,), (release,)))
        offset_release = dict(self._release(artifact), released_at="2026-08-20T02:00:00+02:00")

        inventory = collect_inventory(self._request((artifact,), (offset_release,)))

        self.assertEqual("release-artifact-strategy-0001", inventory.releases[0].record_id)

    def test_rejects_file_uri_payload_and_selected_paths(self) -> None:
        artifact = self._artifact("1", "strategy")
        records = self._records((artifact,), ())
        assignment = dict(records.assignments[0], metadata={"source_path": "file:///workspace/customer.json"})
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_PATH_ABSOLUTE"):
            collect_inventory(replace(self._request((artifact,), ()), records=replace(records, assignments=(assignment,))))
        safe = self._artifact("1", "strategy")
        selection = self._write_selection(safe, "strategy/topic-inventory.json")
        file_uri = SelectedWorkspaceFile("file:///workspace/customer.json", selection.output_path, selection.source_sha256, selection.artifact_id)
        with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_PATH_ABSOLUTE"):
            collect_inventory(self._request((safe,), (self._release(safe),), (file_uri,)))

    def test_rejects_file_uri_under_arbitrary_key_and_nested_path_sequence(self) -> None:
        artifact = self._artifact("1", "strategy")
        records = self._records((artifact,), ())
        invalid = (
            dict(records.assignments[0], note="FiLe:///workspace/customer.json"),
            dict(records.assignments[0], metadata={"paths": ["/home/operator/customer"]}),
        )
        for assignment in invalid:
            with self.subTest(assignment=assignment):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_PATH_ABSOLUTE"):
                    collect_inventory(replace(self._request((artifact,), ()), records=replace(records, assignments=(assignment,))))

    def test_allows_urls_and_routes_under_non_path_keys(self) -> None:
        artifact = self._artifact("1", "strategy")
        records = self._records((artifact,), ())
        assignment = dict(records.assignments[0], note="https://heartweb.example/customer", route="/customer")

        inventory = collect_inventory(replace(self._request((artifact,), ()), records=replace(records, assignments=(assignment,))))

        self.assertEqual("/customer", inventory.assignments[0].payload["route"])

    def test_rejects_compound_credential_paths_using_existing_files(self) -> None:
        artifact = self._artifact("1", "strategy")
        for source_path in ("access-token.json", "database-password.txt", "private-key.json", ".ssh/id_ed25519", "credentials.json", "client-secret.json", "oauth.json", "api-key.json", "api_key.json", "apikey.json"):
            path = self.root / source_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"delivery")
            selection = SelectedWorkspaceFile(source_path, "strategy/topic-inventory.json", DELIVERY_HASH, str(artifact["artifact_id"]))
            with self.subTest(source_path=source_path):
                with self.assertRaisesRegex(DeliveryInventoryError, "DELIVERY_FILE_CREDENTIAL_LIKE"):
                    collect_inventory(self._request((artifact,), (self._release(artifact),), (selection,)))

    def test_staging_evidence_without_step_4b_file_keeps_exact_missing_status(self) -> None:
        artifacts = tuple(self._artifact(step, deliverable) for step, deliverable, _ in DELIVERABLES)
        releases = tuple(self._release(item) for item in artifacts if item["step_id"] != "4b")
        selections = tuple(self._write_selection(item, output) for item, (_, _, output) in zip(artifacts[:-1], DELIVERABLES[:-1], strict=True))
        inventory = collect_inventory(self._request(artifacts, releases, selections, include_drafts=True))
        staged = artifacts[-1]

        result = evaluate_final(inventory, FinalReadinessPolicy(True), Step4bStagingReadiness(str(staged["artifact_id"]), 1, DELIVERY_HASH))

        self.assertFalse(result.eligible)
        self.assertEqual(("developer-handoff",), result.missing_deliverable_ids)
        self.assertEqual(("DELIVERY_FINAL_STEP_4B_NOT_READY", "DELIVERY_FINAL_DELIVERABLE_MISSING"), tuple(error.code for error in result.errors))


if __name__ == "__main__":
    unittest.main()
