from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
import unittest

from jsonschema import Draft202012Validator, FormatChecker

from services.delivery.inventory import Deliverable, DeliveryInventory, InventoryFile
from services.delivery.record_normalization import CanonicalRecord, DeliveryInventoryError
from services.delivery.role_packages import RoleHandoffBuildContext, build_role_package
from services.delivery.renderers import render_role_package


TENANT = "tenant-demo"
PROJECT = "project-demo"
HASH = hashlib.sha256(b"artifact").hexdigest()


def record(kind: str, record_id: str, payload: dict[str, str], step: str | None = None) -> CanonicalRecord:
    return CanonicalRecord(kind, record_id, step, 1 if kind == "artifact" else None, HASH if kind == "artifact" else None, MappingProxyType({"tenant_id": TENANT, "project_id": PROJECT, **payload}))


def inventory() -> DeliveryInventory:
    artifacts = tuple(record("artifact", f"artifact-{name}-0001", {}, step) for step, name in (("1b", "architecture"), ("1c", "design"), ("2", "keywords"), ("3", "roadmap"), ("4a", "briefing"), ("4b", "html")))
    paths = tuple(InventoryFile(item.record_id, f"{item.record_id}/source.json", HASH, 8) for item in artifacts)
    deliverables = tuple(Deliverable(item.record_id.removeprefix("artifact-").removesuffix("-0001"), item.record_id, item.step_id or "", "", "released", next(path.output_path for path in paths if path.artifact_id == item.record_id), HASH) for item in artifacts)
    task = record("task", "task-copywriter-0001", {"title": "Write briefing", "priority": "high", "due_at": "2026-08-30T00:00:00Z", "status": "open"}, "4a")
    assignment = record("assignment", "assignment-copywriter-0001", {"task_id": task.record_id, "assigned_role": "copywriter"})
    review = record("review", "review-copywriter-0001", {"artifact_id": "artifact-briefing-0001"})
    blocker = record("blocker", "blocker-copywriter-0001", {"task_id": task.record_id})
    return DeliveryInventory(TENANT, PROJECT, record("project", PROJECT, {}), record("workflow", f"workflow:{PROJECT}", {}), (), artifacts, (), (), (task,), (assignment,), (review,), (blocker,), (), paths, deliverables)


def context(role: str) -> RoleHandoffBuildContext:
    return RoleHandoffBuildContext("delivery-export-demo-0001", "delivery-package-demo-0001", 1, "2026-08-20T00:00:00Z", role, f"role-handoff-{role}-0001")


class DeliveryRolePackageTests(unittest.TestCase):
    def test_copywriter_selects_only_steps_and_related_records(self) -> None:
        # Given: canonical inventory records for both role surfaces
        source = inventory()
        # When: a copywriter handoff is derived
        package = build_role_package(context("copywriter"), source)
        # Then: only canonical Step 2, 3, and 4a artifact references remain
        self.assertEqual(("2", "3", "4a"), tuple(item.step_id for item in package.artifacts))
        self.assertEqual(("task-copywriter-0001",), tuple(item.record_id for item in package.tasks))
        self.assertEqual(("review-copywriter-0001",), tuple(item.record_id for item in package.reviews))
        self.assertEqual(("blocker-copywriter-0001",), tuple(item.record_id for item in package.blockers))

    def test_developer_selects_only_developer_steps_and_renderer_is_deterministic(self) -> None:
        # Given: canonical records with no developer assignment
        source = inventory()
        # When: a developer handoff is derived and rendered twice
        package = build_role_package(context("developer"), source)
        first = render_role_package(package)
        # Then: architecture, design, roadmap and HTML are included byte-identically
        self.assertEqual(("1b", "1c", "3", "4b"), tuple(item.step_id for item in package.artifacts))
        self.assertEqual(first, render_role_package(package))
        self.assertTrue(all(path.path.startswith("developer-handoff/") for path in first))

    def test_manifest_is_schema_valid_and_draft_state_is_not_promoted(self) -> None:
        # Given: an explicitly included draft Step 4a deliverable
        source = inventory()
        draft = replace(source.deliverables[4], release_status="draft")
        source = replace(source, deliverables=(*source.deliverables[:4], draft, *source.deliverables[5:]))
        # When: a package is built
        package = build_role_package(context("copywriter"), source)
        schema = json.loads(Path("standards/delivery/role-handoff-manifest.schema.json").read_text(encoding="utf-8"))
        # Then: draft state remains visible and the final manifest validates
        self.assertEqual("draft", package.artifacts[-1].release_status)
        self.assertEqual([], list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(package.manifest)))

    def test_rejects_dangling_assignment_and_empty_or_unsupported_role(self) -> None:
        # Given: a canonical role assignment without its required task
        source = inventory()
        dangling = record("assignment", "assignment-developer-0001", {"task_id": "task-missing-0001", "assigned_role": "developer"})
        # When/Then: invalid relations and unavailable role views fail explicitly
        with self.assertRaisesRegex(DeliveryInventoryError, "ROLE_ASSIGNMENT_TASK_DANGLING"):
            build_role_package(context("developer"), replace(source, assignments=(dangling,)))
        with self.assertRaisesRegex(DeliveryInventoryError, "ROLE_PACKAGE_EMPTY"):
            build_role_package(context("copywriter"), replace(source, deliverables=()))
        with self.assertRaisesRegex(DeliveryInventoryError, "ROLE_UNSUPPORTED"):
            build_role_package(context("reviewer"), source)

    def test_unresolved_assignments_are_sorted_and_role_records_are_filtered(self) -> None:
        # Given: two unordered copywriter assignments and unrelated developer records
        source = inventory()
        second = record("task", "task-copywriter-0002", {"title": "Write second briefing", "priority": "normal", "status": "open"}, "4a")
        first_assignment = source.assignments[0]
        second_assignment = record("assignment", "assignment-copywriter-0002", {"task_id": second.record_id, "role": "copywriter"})
        developer = record("assignment", "assignment-developer-0001", {"task_id": "task-copywriter-0001", "assigned_role": "developer"})
        source = replace(source, tasks=(source.tasks[0], second), assignments=(second_assignment, developer, first_assignment))
        # When: the copywriter package is built
        package = build_role_package(context("copywriter"), source)
        # Then: unknown assignees are explicit, sorted, and other-role records are excluded
        self.assertEqual(("assignment-copywriter-0001", "assignment-copywriter-0002"), package.handoff_manifest.unresolved_assignee_ids)
        self.assertNotIn("assignment-developer-0001", tuple(item.record_id for item in package.assignments))
        self.assertIn("unresolved:assignment-copywriter-0001", next(item.content.decode("utf-8") for item in render_role_package(package) if item.path.endswith("TASK_SUMMARY.md")))

    def test_rejects_conflicting_source_identity_and_preserves_input(self) -> None:
        # Given: a review that conflicts with a selected task identity
        source = inventory()
        conflicting_review = record("review", "task-copywriter-0001", {"artifact_id": "artifact-briefing-0001", "decision": "required"})
        source = replace(source, reviews=(conflicting_review,))
        before = source
        # When/Then: conflict is rejected without changing the immutable input inventory
        with self.assertRaisesRegex(DeliveryInventoryError, "ROLE_SOURCE_ID_CONFLICT"):
            build_role_package(context("copywriter"), source)
        self.assertEqual(before, source)

    def test_resolved_assignments_remain_resolved_and_each_assignment_renders(self) -> None:
        # Given: two copywriter assignments for one task with distinct assignment values
        source = inventory()
        resolved = record("assignment", "assignment-copywriter-0002", {"task_id": "task-copywriter-0001", "assigned_role": "copywriter", "assignee_id": "user-writer-0001", "priority": "critical", "deadline": "2026-08-21T00:00:00Z"})
        unresolved = record("assignment", "assignment-copywriter-0001", {"task_id": "task-copywriter-0001", "assigned_role": "copywriter", "priority": "low", "deadline": "2026-08-31T00:00:00Z"})
        source = replace(source, assignments=(resolved, unresolved))
        # When: the package is rendered
        package = build_role_package(context("copywriter"), source)
        summary = next(item.content.decode("utf-8") for item in render_role_package(package) if item.path.endswith("TASK_SUMMARY.md"))
        # Then: only the missing assignee is unresolved and both assignment rows retain their values
        self.assertEqual(("assignment-copywriter-0001",), package.handoff_manifest.unresolved_assignee_ids)
        self.assertIn("user-writer-0001", summary)
        self.assertIn("unresolved:assignment-copywriter-0001", summary)
        self.assertIn("critical", summary)
        self.assertIn("2026-08-21T00:00:00Z", summary)
        self.assertIn("low", summary)
        self.assertIn("2026-08-31T00:00:00Z", summary)

    def test_excludes_role_labeled_records_with_excluded_relations(self) -> None:
        # Given: requested-role records bound to developer-only artifact and task IDs
        source = inventory()
        review = record("review", "review-excluded-0001", {"artifact_id": "artifact-html-0001", "role": "copywriter"})
        blocker = record("blocker", "blocker-excluded-0001", {"task_id": "task-developer-0001", "role": "copywriter"})
        source = replace(source, reviews=(review,), blockers=(blocker,))
        # When: the copywriter view is built
        package = build_role_package(context("copywriter"), source)
        # Then: explicit contradictory relations outrank the matching role label
        self.assertEqual((), package.reviews)
        self.assertEqual((), package.blockers)

    def test_rejects_every_invalid_deliverable_file_binding(self) -> None:
        # Given: canonical Step 2 selection variants that do not bind exactly one file
        source = inventory()
        keyword = source.deliverables[2]
        duplicate = InventoryFile(keyword.artifact_id, "keyword-extra/evidence.json", HASH, 8)
        mismatched_path = InventoryFile(keyword.artifact_id, "keyword-extra/evidence.json", HASH, 8)
        mismatched_hash = InventoryFile(keyword.artifact_id, keyword.output_path or "", "b" * 64, 8)
        # When/Then: missing, duplicate, path, and hash bindings fail closed
        without = tuple(item for item in source.files if item.artifact_id != keyword.artifact_id)
        cases = ((replace(source, files=without), "ROLE_DELIVERABLE_FILE_MISSING"), (replace(source, files=(*source.files, duplicate)), "ROLE_DELIVERABLE_FILE_DUPLICATE"), (replace(source, files=tuple(mismatched_path if item.artifact_id == keyword.artifact_id else item for item in source.files)), "ROLE_DELIVERABLE_FILE_PATH_MISMATCH"), (replace(source, files=tuple(mismatched_hash if item.artifact_id == keyword.artifact_id else item for item in source.files)), "ROLE_DELIVERABLE_FILE_HASH_MISMATCH"))
        for changed, code in cases:
            with self.subTest(code=code), self.assertRaisesRegex(DeliveryInventoryError, code):
                build_role_package(context("copywriter"), changed)

    def test_recomputed_manifest_hash_and_reordered_inputs_are_identical(self) -> None:
        # Given: semantically identical inventories with reversed collection order
        source = inventory()
        reordered = replace(source, artifacts=tuple(reversed(source.artifacts)), files=tuple(reversed(source.files)), deliverables=tuple(reversed(source.deliverables)), assignments=tuple(reversed(source.assignments)))
        # When: each is independently built and rendered
        first = build_role_package(context("copywriter"), source)
        second = build_role_package(context("copywriter"), reordered)
        payload = first.manifest
        digest = payload.pop("manifest_sha256")
        # Then: package, canonical hash, and output bytes are invariant
        self.assertEqual(first, second)
        self.assertEqual(digest, hashlib.sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest())
        self.assertEqual(render_role_package(first), render_role_package(second))

    def test_context_paths_links_and_successful_builds_fail_or_preserve_as_required(self) -> None:
        # Given: valid inventory, malformed contexts, and a matching unsafe selected artifact path
        source = inventory()
        unsafe_file = InventoryFile("artifact-keywords-0001", "../escape.json", HASH, 8)
        unsafe_deliverable = replace(source.deliverables[2], output_path="../escape.json")
        unsafe = replace(source, files=tuple(unsafe_file if item.artifact_id == unsafe_file.artifact_id else item for item in source.files), deliverables=(*source.deliverables[:2], unsafe_deliverable, *source.deliverables[3:]))
        invalid = (replace(context("copywriter"), export_id="bad"), replace(context("copywriter"), source_snapshot_revision=0), replace(context("copywriter"), created_at="invalid"))
        # When/Then: final schema validation rejects context defects and path/link boundaries stay safe
        for changed in invalid:
            with self.subTest(changed=changed), self.assertRaisesRegex(DeliveryInventoryError, "ROLE_MANIFEST_INVALID"):
                build_role_package(changed, source)
        with self.assertRaisesRegex(DeliveryInventoryError, "ROLE_OUTPUT_PATH_INVALID"):
            build_role_package(context("copywriter"), unsafe)
        before = source
        package = build_role_package(context("copywriter"), source)
        index = next(item.content.decode("utf-8") for item in render_role_package(package) if item.path.endswith("ROLE_INDEX.md"))
        self.assertEqual(before, source)
        self.assertIn("](../artifact-keywords-0001/source.json)", index)

    def test_duplicate_identical_sources_deduplicate_and_requirements_render(self) -> None:
        # Given: repeated identical review sources with canonical review and blocker requirement fields
        source = inventory()
        review = record("review", "review-copywriter-0001", {"artifact_id": "artifact-briefing-0001", "status": "required", "requirements": "Claim proof", "technical_qa": "Schema check"})
        blocker = record("blocker", "blocker-copywriter-0001", {"task_id": "task-copywriter-0001", "status": "open", "instructions": "Await staging evidence"})
        source = replace(source, reviews=(review, review), blockers=(blocker,))
        # When: the package is built and indexed
        package = build_role_package(context("copywriter"), source)
        index = next(item.content.decode("utf-8") for item in render_role_package(package) if item.path.endswith("ROLE_INDEX.md"))
        source_ids = tuple(item.source_record_id for item in package.handoff_manifest.source_records)
        # Then: canonical source IDs deduplicate and operational requirements remain readable
        self.assertEqual(1, source_ids.count("review-copywriter-0001"))
        self.assertIn("Claim proof", index)
        self.assertIn("Schema check", index)
        self.assertIn("Await staging evidence", index)


if __name__ == "__main__":
    unittest.main()
