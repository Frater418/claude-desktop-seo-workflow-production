from __future__ import annotations

from dataclasses import replace
import unittest

from services.delivery.inventory import InventoryFile
from services.delivery.notion_import import NotionImplementationTask, PublicationRegistryRecord, build_notion_import_pack
from services.delivery.record_normalization import DeliveryInventoryError
from tests.support.notion_import import HASH, inventory, record, request


class NotionImportFailureTests(unittest.TestCase):
    def assert_error(self, source, code: str) -> None:
        with self.assertRaisesRegex(DeliveryInventoryError, code):
            build_notion_import_pack(source)

    def test_rejects_missing_released_strategy_or_roadmap(self) -> None:
        for role in ("strategy", "roadmap"):
            with self.subTest(role=role):
                source = inventory()
                missing = tuple(item for item in source.deliverables if item.role != role)
                available_artifact = next(item for item in source.artifacts if item.record_id == "artifact-architecture-0001")
                review = record("review", "review-concept-0001", {"artifact_id": available_artifact.record_id})
                blocker = record("blocker", "blocker-concept-0001", {"artifact_id": available_artifact.record_id})
                self.assert_error(request(replace(source, deliverables=missing, reviews=(review,), blockers=(blocker,))), "NOTION_PERFORMANCE_REFERENCE_MISSING")

    def test_rejects_invalid_publication_review_blocker_and_approval_bindings(self) -> None:
        source = request()
        invalid = (
            replace(source, publication_registry=PublicationRegistryRecord("publication-registry-demo", {})),
            replace(source, publication_registry=PublicationRegistryRecord("publication-registry-demo", {"publication_registry_record_id": "publication-registry-other"})),
            request(replace(source.inventory, reviews=())),
            request(replace(source.inventory, blockers=())),
            request(replace(source.inventory, releases=source.inventory.releases[1:])),
            request(replace(source.inventory, releases=(record("release", source.inventory.releases[0].record_id, {"artifact_id": source.inventory.artifacts[0].record_id, "artifact_sha256": "b" * 64, "run_id": "run-demo-0001", "approval_id": "approval-caller-f7a301"}, source.inventory.releases[0].step_id), *source.inventory.releases[1:]))),
        )
        codes = ("NOTION_PUBLICATION_REFERENCE_INVALID", "NOTION_PUBLICATION_REFERENCE_INVALID", "NOTION_CORE_ROWS_MISSING", "NOTION_CORE_ROWS_MISSING", "NOTION_RELEASE_BINDING_INVALID", "NOTION_RELEASE_BINDING_INVALID")
        for candidate, code in zip(invalid, codes, strict=True):
            with self.subTest(code=code):
                self.assert_error(candidate, code)

    def test_rejects_missing_or_duplicate_canonical_approval_ids(self) -> None:
        source = inventory()
        missing = tuple(record("release", item.record_id, {"artifact_id": item.payload["artifact_id"], "artifact_sha256": HASH, "run_id": "run-demo-0001"}, item.step_id) if index == 0 else item for index, item in enumerate(source.releases))
        duplicate = tuple(record("release", item.record_id, {"artifact_id": item.payload["artifact_id"], "artifact_sha256": HASH, "run_id": "run-demo-0001", "approval_id": "approval-caller-7f3a"}, item.step_id) for item in source.releases)
        self.assert_error(request(replace(source, releases=missing)), "NOTION_APPROVAL_BINDING_INVALID")
        self.assert_error(request(replace(source, releases=duplicate)), "NOTION_APPROVAL_BINDING_INVALID")

    def test_rejects_empty_or_invalid_implementation_task_fields(self) -> None:
        source = request()
        task = source.implementation_tasks[0]
        self.assert_error(replace(source, implementation_tasks=()), "NOTION_IMPLEMENTATION_TASKS_MISSING")
        invalid = {
            "task_id": "",
            "task_id_invalid": "invalid-id",
            "assignment_id": "",
            "assignment_id_invalid": "invalid-id",
            "status": "waiting",
            "priority": "urgent",
            "priority_empty": "",
            "deadline": "2026-09-31",
            "deadline_empty": "",
        }
        for field, value in invalid.items():
            with self.subTest(field=field):
                field_name = field.removesuffix("_invalid").removesuffix("_empty")
                self.assert_error(replace(source, implementation_tasks=(replace(task, **{field_name: value}),)), "NOTION_MANIFEST_INVALID")

    def test_rejects_duplicate_implementation_ids_and_relations(self) -> None:
        source = request()
        task = source.implementation_tasks[0]
        second = replace(task, task_id="task-implementation-0002", assignment_id="assignment-implementation-0002", dependencies=(task.task_id,), artifact_relations=("artifact-strategy-0001",))
        cases = (
            (replace(task, assignment_id="assignment-implementation-0002", title="Duplicate task"), "NOTION_STABLE_ID_CONFLICT"),
            (replace(task, task_id="task-implementation-0002", title="Duplicate assignment"), "NOTION_STABLE_ID_CONFLICT"),
            (replace(second, dependencies=(task.task_id, task.task_id)), "NOTION_RELATION_DUPLICATE"),
            (replace(second, artifact_relations=("artifact-strategy-0001", "artifact-strategy-0001")), "NOTION_RELATION_DUPLICATE"),
        )
        for candidate, code in cases:
            with self.subTest(code=code):
                self.assert_error(replace(source, implementation_tasks=(task, candidate)), code)

    def test_rejects_dangling_implementation_relations_and_unsafe_artifact_paths(self) -> None:
        source = request()
        task = source.implementation_tasks[0]
        for candidate in (replace(task, dependencies=("task-missing-0001",)), replace(task, artifact_relations=("artifact-missing-0001",))):
            with self.subTest(candidate=candidate):
                self.assert_error(replace(source, implementation_tasks=(candidate,)), "NOTION_RELATION_DANGLING")
        original = source.inventory.files[0]
        for unsafe_path in ("../escape.json", "/absolute.json"):
            with self.subTest(unsafe_path=unsafe_path):
                unsafe_file = InventoryFile(original.artifact_id, unsafe_path, original.content_sha256, original.size_bytes)
                unsafe_deliverable = replace(source.inventory.deliverables[0], output_path=unsafe_path)
                unsafe_inventory = replace(source.inventory, files=(unsafe_file, *source.inventory.files[1:]), deliverables=(unsafe_deliverable, *source.inventory.deliverables[1:]))
                self.assert_error(request(unsafe_inventory), "NOTION_MANIFEST_INVALID")

    def test_deduplicates_identical_canonical_sources_and_rejects_conflicting_hashes(self) -> None:
        source = inventory()
        exact_duplicate = record("assignment", "task-core-0001", {"title": "Validate concept"})
        pack = build_notion_import_pack(request(replace(source, assignments=(exact_duplicate,))))
        self.assertEqual(1, sum(row["source_record_id"] == "task-core-0001" for row in pack.manifest["source_records"]))
        conflicting = record("assignment", "task-core-0001", {"title": "Different canonical content"})
        self.assert_error(request(replace(source, assignments=(conflicting,))), "NOTION_SOURCE_ID_CONFLICT")

    def test_rejects_every_credential_shape_and_invalid_verified_user(self) -> None:
        source = request()
        task = source.implementation_tasks[0]
        credentials = (
            "-----BEGIN PRIVATE KEY-----",
            "AKIA1234567890ABCDEF",
            "ghp_abcdefghijklmnopqrstuv",
            "xoxb-abcdefghijklmnop",
            "sk-live-abcdefghijklmnop",
            "sk_live_abcdefghijklmnop",
            "sk_test_abcdefghijklmnop",
            "api_key=abcdefghijklmnop",
            "API_KEY=abcdefghijklmnop",
            "api_key = abcdefghijklmnop",
            "client_secret=abcdefghijklmnop",
            "client_secret: abcdefghijklmnop",
            "abcdefghijklmnop.abcdefghijklmnop.abcdefghijklmnop",
            "Bearer abcdefghijklmnop",
        )
        for value in credentials:
            with self.subTest(credential=value):
                self.assert_error(replace(source, implementation_tasks=(replace(task, comments=value),)), "NOTION_CREDENTIAL_LEAK")
        for user_id in ("notion-user-", "notion-user-!", "notion-user-UPPER-0001", "Regina Example"):
            with self.subTest(user_id=user_id):
                self.assert_error(replace(source, implementation_tasks=(replace(task, notion_user_id=user_id),)), "NOTION_USER_ID_INVALID")


if __name__ == "__main__":
    unittest.main()
