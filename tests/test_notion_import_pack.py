from __future__ import annotations

import copy
import csv
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
from types import MappingProxyType
import unittest

from jsonschema import Draft202012Validator, FormatChecker

from services.delivery.contract_validation import validate_notion_import_replay
from services.delivery.inventory import Deliverable, DeliveryInventory, InventoryFile
from services.delivery.notion_import import (
    NotionImplementationTask,
    NotionImportBuildContext,
    NotionImportRequest,
    PublicationRegistryRecord,
    build_notion_import_pack,
)
from services.delivery.record_normalization import CanonicalRecord, DeliveryInventoryError


TENANT = "tenant-demo"
PROJECT = "project-demo"
HASH = hashlib.sha256(b"artifact").hexdigest()


def record(kind: str, record_id: str, payload: dict[str, str], step: str | None = None) -> CanonicalRecord:
    return CanonicalRecord(kind, record_id, step, 1 if kind == "artifact" else None, HASH if kind == "artifact" else None, MappingProxyType({"tenant_id": TENANT, "project_id": PROJECT, **payload}))


def inventory() -> DeliveryInventory:
    specs = (("1", "strategy", "strategy"), ("1b", "architecture", "architecture"), ("1c", "design", "developer"), ("2", "keywords", "concept"), ("3", "roadmap", "roadmap"), ("4a", "briefing", "copywriter"))
    artifacts = tuple(record("artifact", f"artifact-{name}-0001", {}, step) for step, name, _ in specs)
    files = tuple(InventoryFile(item.record_id, f"released/{item.record_id}.json", HASH, 8) for item in artifacts)
    deliverables = tuple(Deliverable(name, item.record_id, step, role, "released", next(file.output_path for file in files if file.artifact_id == item.record_id), HASH) for item, (step, name, role) in zip(artifacts, specs, strict=True))
    approval_ids = ("approval-caller-f7a301", "approval-caller-9c42be", "approval-caller-a81d06", "approval-caller-3e7bf9", "approval-caller-d514ac", "approval-caller-61f8d2")
    releases = tuple(record("release", f"release-{item.record_id.removeprefix('artifact-')}", {"artifact_id": item.record_id, "artifact_sha256": HASH, "run_id": "run-demo-0001", "approval_id": approval_id}, item.step_id) for (item, _), approval_id in zip(zip(artifacts, specs, strict=True), approval_ids, strict=True))
    task = record("task", "task-core-0001", {"title": "Validate concept"}, "4a")
    review = record("review", "review-concept-0001", {"artifact_id": artifacts[0].record_id})
    blocker = record("blocker", "blocker-concept-0001", {"artifact_id": artifacts[0].record_id})
    return DeliveryInventory(TENANT, PROJECT, record("project", PROJECT, {}), record("workflow", f"workflow:{PROJECT}", {}), (), artifacts, releases, (), (task,), (), (review,), (blocker,), (), files, deliverables)


def request(source: DeliveryInventory | None = None) -> NotionImportRequest:
    task = NotionImplementationTask("task-implementation-0001", "assignment-implementation-0001", "Publish content", "not_started", "", "", "high", "2026-09-01", "copywriter", ())
    context = NotionImportBuildContext("notion-import-demo-0001", "delivery-export-demo-0001", "delivery-package-demo-0001", 9, "2026-08-22T00:00:00Z", "customer-demo")
    registry = PublicationRegistryRecord("publication-registry-demo", {"publication_registry_record_id": "publication-registry-demo", "urls": ["https://example.test/content"]})
    return NotionImportRequest(context, source or inventory(), (task,), registry)


def _canonical_request(source: NotionImportRequest) -> dict:
    inventory_value = source.inventory
    record_value = lambda item: {"kind": item.kind, "record_id": item.record_id, "step_id": item.step_id, "revision": item.revision, "content_sha256": item.content_sha256, "payload": dict(item.payload)}
    return {
        "context": {"notion_import_manifest_id": source.context.notion_import_manifest_id, "export_id": source.context.export_id, "delivery_package_id": source.context.delivery_package_id, "source_snapshot_revision": source.context.source_snapshot_revision, "created_at": source.context.created_at, "customer_external_id": source.context.customer_external_id},
        "inventory": {"tenant_id": inventory_value.tenant_id, "project_id": inventory_value.project_id, "project_v2": record_value(inventory_value.project_v2), "workflow": record_value(inventory_value.workflow), "artifacts": [record_value(item) for item in inventory_value.artifacts], "releases": [record_value(item) for item in inventory_value.releases], "tasks": [record_value(item) for item in inventory_value.tasks], "reviews": [record_value(item) for item in inventory_value.reviews], "blockers": [record_value(item) for item in inventory_value.blockers], "files": [{"artifact_id": item.artifact_id, "output_path": item.output_path, "content_sha256": item.content_sha256, "size_bytes": item.size_bytes} for item in inventory_value.files]},
        "implementation_tasks": [{"task_id": item.task_id, "assignment_id": item.assignment_id, "title": item.title, "status": item.status, "comments": item.comments, "source_assignee": item.source_assignee, "priority": item.priority, "deadline": item.deadline, "role": item.role, "dependencies": item.dependencies, "artifact_relations": item.artifact_relations, "notion_user_id": item.notion_user_id} for item in source.implementation_tasks],
        "publication_registry": {"record_id": source.publication_registry.record_id, "payload": dict(source.publication_registry.payload)},
    }


class NotionImportPackTests(unittest.TestCase):
    def test_builds_schema_valid_deterministic_manual_pack(self) -> None:
        # Given: released canonical records and explicit implementation work
        source = request()
        # When: the pack is rendered twice
        first = build_notion_import_pack(source)
        second = build_notion_import_pack(source)
        schema = json.loads(Path("standards/delivery/notion-import-manifest.schema.json").read_text(encoding="utf-8"))
        # Then: all closed descriptors and bytes remain stable and schema-valid
        self.assertEqual(first, second)
        self.assertEqual(14, len(first.manifest["files"]))
        self.assertEqual([], list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(first.manifest)))
        self.assertEqual(15, len(first.files))
        self.assertTrue(validate_notion_import_replay(first.manifest, second.manifest).idempotent)

    def test_enforces_core_history_and_notion_ownership_boundaries(self) -> None:
        # Given: canonical history and an unresolved explicit Notion task
        pack = build_notion_import_pack(request())
        # When: task rows are examined
        core = next(row for row in pack.manifest["task_rows"] if row["task_class"] == "core_history")
        implementation = next(row for row in pack.manifest["task_rows"] if row["task_class"] == "notion_implementation")
        mapping = pack.files["notion-import/PROPERTY_MAPPING.md"].decode("utf-8")
        # Then: history cannot expose mutable values and Notion values stay one-way
        self.assertEqual({"external_id", "tenant_id", "project_id", "task_class", "title", "history_only"}, set(core))
        self.assertEqual("unassigned", implementation["assignee"])
        self.assertEqual(["assignment-implementation-0001"], pack.manifest["unresolved_assignee_ids"])
        self.assertNotIn("resume_run", mapping)
        self.assertIn("Daily task completion has no Core callback", mapping)

    def test_preserves_canonical_approvals_and_complete_rendered_manifest(self) -> None:
        # Given: a pack with release-bound canonical approval IDs
        pack = build_notion_import_pack(request())
        schema = json.loads(Path("standards/delivery/notion-import-manifest.schema.json").read_text(encoding="utf-8"))
        # When: the rendered JSON manifest is parsed
        rendered = json.loads(pack.files["notion-import/notion-import-manifest.json"])
        # Then: it is complete, schema-valid, and retains the release approval identity
        self.assertEqual(pack.manifest, rendered)
        self.assertEqual([], list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(rendered)))
        self.assertIn("approval-caller-f7a301", {row["external_id"] for row in rendered["approval_rows"]})
        for descriptor in rendered["files"]:
            content = pack.files[descriptor["relative_path"]]
            self.assertEqual(descriptor["content_sha256"], hashlib.sha256(content).hexdigest())
            if descriptor["file_name"].endswith(".csv"):
                self.assertEqual(descriptor["row_count"], len(list(csv.reader(io.StringIO(content.decode("utf-8"), newline="")))) - 1)
            else:
                self.assertEqual(descriptor["row_count"], content.decode("utf-8").count("\n"))

    def test_reordering_and_user_resolution_are_canonical(self) -> None:
        # Given: two independent task orders with one verified and one source-only assignee
        source = request()
        second = NotionImplementationTask("task-implementation-0002", "assignment-implementation-0002", "Review content", "in_progress", "Working", "Regina", "medium", "2026-09-02", "copywriter", ("task-implementation-0001",), (), "notion-user-regina-0001")
        forward = replace(source, implementation_tasks=(*source.implementation_tasks, second))
        backward = replace(source, implementation_tasks=tuple(reversed(forward.implementation_tasks)))
        # When: equivalent input orders are rendered
        first, reordered = build_notion_import_pack(forward), build_notion_import_pack(backward)
        template = first.files["notion-import/USER_MAPPING_TEMPLATE.csv"].decode("utf-8")
        # Then: every byte is stable and only unverified users require mapping
        self.assertEqual(first, reordered)
        self.assertEqual(["assignment-implementation-0001"], first.manifest["unresolved_assignee_ids"])
        self.assertIn("assignment-implementation-0001,,", template)
        self.assertNotIn("assignment-implementation-0002", template)

    def test_rejects_publication_identity_and_credential_content_without_mutation(self) -> None:
        # Given: invalid external provenance variants and an immutable request snapshot
        source = request()
        before = copy.deepcopy(_canonical_request(source))
        bad_registry = replace(source, publication_registry=PublicationRegistryRecord("publication-registry-demo", {"publication_registry_record_id": "publication-registry-other"}))
        secret_task = replace(source.implementation_tasks[0], comments="sk-live-abcdefghijklmnop")
        # When/Then: both fail closed and the source request remains intact
        with self.assertRaisesRegex(DeliveryInventoryError, "NOTION_PUBLICATION_REFERENCE_INVALID"):
            build_notion_import_pack(bad_registry)
        with self.assertRaisesRegex(DeliveryInventoryError, "NOTION_CREDENTIAL_LEAK"):
            build_notion_import_pack(replace(source, implementation_tasks=(secret_task,)))
        self.assertEqual(before, _canonical_request(source))

    def test_generated_structured_files_are_one_way_and_lf_only(self) -> None:
        # Given: a complete manual import pack
        pack = build_notion_import_pack(request())
        # When: generated CSV and JSON bytes are inspected as machine structures
        structured = {path: content for path, content in pack.files.items() if path.endswith(".csv") or path.endswith(".json")}
        forbidden = (b"resume_run", b"gate_approval", b"revision_creation", b"artifact_mutation", b"webhook", b"command_callback", b"task_completion_callback")
        # Then: no inbound authority field exists and stable line endings are preserved
        self.assertTrue(all(b"\r" not in content for content in structured.values()))
        self.assertTrue(all(token not in content for content in structured.values() for token in forbidden))
        implementation = next(row for row in pack.manifest["task_rows"] if row["task_class"] == "notion_implementation")
        self.assertEqual("none", implementation["core_effect"])

    def test_rejects_credential_shapes_and_invalid_notion_users(self) -> None:
        # Given: representative credential material and invalid verified-user identities
        source = request()
        credentials = ("sk_live_abcdefghijklmnop", "api_key=abcdefghijklmnop", "client_secret=abcdefghijklmnop", "abcdefghijklmnop.abcdefghijklmnop.abcdefghijklmnop")
        invalid_users = ("notion-user-", "notion-user-!", "notion-user-UPPER-0001", "Regina Example")
        # When/Then: generated content and user IDs fail closed
        for value in credentials:
            with self.subTest(value=value), self.assertRaisesRegex(DeliveryInventoryError, "NOTION_CREDENTIAL_LEAK"):
                build_notion_import_pack(replace(source, implementation_tasks=(replace(source.implementation_tasks[0], comments=value),)))
        for value in invalid_users:
            with self.subTest(value=value), self.assertRaisesRegex(DeliveryInventoryError, "NOTION_USER_ID_INVALID"):
                build_notion_import_pack(replace(source, implementation_tasks=(replace(source.implementation_tasks[0], notion_user_id=value),)))

    def test_projects_csv_contains_customer_then_project_and_mapping_covers_headers(self) -> None:
        # Given: the closed pack and its deterministic documentation
        pack = build_notion_import_pack(request())
        projects = pack.files["notion-import/projects.csv"].decode("utf-8").splitlines()
        mapping = pack.files["notion-import/PROPERTY_MAPPING.md"].decode("utf-8")
        # When: the projects rows and every generated CSV header are inspected
        headers = {path.rsplit("/", 1)[1]: content.decode("utf-8").splitlines()[0].split(",") for path, content in pack.files.items() if path.endswith(".csv")}
        # Then: customer precedes project and each actual header is documented
        self.assertEqual("customer", projects[1].split(",")[0])
        self.assertEqual("project", projects[2].split(",")[0])
        for name, columns in headers.items():
            for column in columns:
                self.assertIn(f"| {name} | {column} |", mapping)

    def test_rejects_missing_released_bindings_and_draft_artifacts(self) -> None:
        # Given: valid canonical inventory variants that cannot support a complete release
        source = inventory()
        # When/Then: draft and incomplete releases fail closed
        draft = replace(source.deliverables[0], release_status="draft")
        with self.assertRaisesRegex(DeliveryInventoryError, "NOTION_ARTIFACT_NOT_RELEASED"):
            build_notion_import_pack(request(replace(source, deliverables=(draft, *source.deliverables[1:]))))
        with self.assertRaisesRegex(DeliveryInventoryError, "NOTION_ARTIFACT_MINIMUM"):
            build_notion_import_pack(request(replace(source, deliverables=source.deliverables[:4])))


if __name__ == "__main__":
    unittest.main()
