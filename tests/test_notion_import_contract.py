from __future__ import annotations

import copy
import csv
from dataclasses import replace
import hashlib
import io
import json
import unittest

from services.delivery.contract_validation import validate_notion_import_replay
from services.delivery.notion_import import NotionImplementationTask, build_notion_import_pack
from services.delivery.notion_import_renderers import CSV_CONTRACTS
from tests.support.notion_import import request


DESCRIPTORS = {
    "projects.csv", "tasks.csv", "assignments.csv", "artifacts.csv", "reviews.csv", "approvals.csv", "blockers.csv", "priorities.csv", "deadlines.csv", "relations.csv", "performance-checkpoints.csv", "IMPORT_ORDER.md", "PROPERTY_MAPPING.md", "USER_MAPPING_TEMPLATE.csv",
}


def request_snapshot(source) -> dict:
    inventory = source.inventory
    record_snapshot = lambda value: {"kind": value.kind, "record_id": value.record_id, "step_id": value.step_id, "revision": value.revision, "content_sha256": value.content_sha256, "payload": dict(value.payload)}
    return {
        "context": {"notion_import_manifest_id": source.context.notion_import_manifest_id, "export_id": source.context.export_id, "delivery_package_id": source.context.delivery_package_id, "source_snapshot_revision": source.context.source_snapshot_revision, "created_at": source.context.created_at, "customer_external_id": source.context.customer_external_id},
        "inventory": {"tenant_id": inventory.tenant_id, "project_id": inventory.project_id, "project_v2": record_snapshot(inventory.project_v2), "workflow": record_snapshot(inventory.workflow), "runs": [record_snapshot(value) for value in inventory.runs], "artifacts": [record_snapshot(value) for value in inventory.artifacts], "releases": [record_snapshot(value) for value in inventory.releases], "gates": [record_snapshot(value) for value in inventory.gates], "tasks": [record_snapshot(value) for value in inventory.tasks], "assignments": [record_snapshot(value) for value in inventory.assignments], "reviews": [record_snapshot(value) for value in inventory.reviews], "blockers": [record_snapshot(value) for value in inventory.blockers], "reports": [record_snapshot(value) for value in inventory.reports], "files": [{"artifact_id": value.artifact_id, "output_path": value.output_path, "content_sha256": value.content_sha256, "size_bytes": value.size_bytes} for value in inventory.files], "deliverables": [{"deliverable_id": value.deliverable_id, "artifact_id": value.artifact_id, "step_id": value.step_id, "role": value.role, "release_status": value.release_status, "output_path": value.output_path, "content_sha256": value.content_sha256} for value in inventory.deliverables]},
        "implementation_tasks": [{"task_id": value.task_id, "assignment_id": value.assignment_id, "title": value.title, "status": value.status, "comments": value.comments, "source_assignee": value.source_assignee, "priority": value.priority, "deadline": value.deadline, "role": value.role, "dependencies": value.dependencies, "artifact_relations": value.artifact_relations, "notion_user_id": value.notion_user_id} for value in source.implementation_tasks],
        "publication_registry": {"record_id": source.publication_registry.record_id, "payload": dict(source.publication_registry.payload)},
    }


def markdown_table_rows(content: str) -> list[tuple[str, str, str, str]]:
    return [tuple(cell.strip() for cell in line.split("|")[1:-1]) for line in content.splitlines() if line.startswith("| ") and not line.startswith("| ---")]


class NotionImportContractTests(unittest.TestCase):
    def test_builder_does_not_mutate_canonical_plain_input(self) -> None:
        source = request()
        before = copy.deepcopy(request_snapshot(source))
        build_notion_import_pack(source)
        self.assertEqual(before, request_snapshot(source))

    def test_returned_views_are_mutation_isolated_from_authoritative_pack_bytes(self) -> None:
        pack = build_notion_import_pack(request())
        manifest = pack.manifest
        files = pack.files
        manifest["artifact_rows"][0]["role"] = "mutated"
        manifest["source_records"].clear()
        files["notion-import/projects.csv"] = b"mutated\n"
        self.assertEqual("strategy", next(row["role"] for row in pack.manifest["artifact_rows"] if row["external_id"] == "artifact-strategy-0001"))
        self.assertTrue(pack.manifest["source_records"])
        self.assertNotEqual(b"mutated\n", pack.files["notion-import/projects.csv"])

    def test_equivalent_task_and_relation_orders_render_byte_identically(self) -> None:
        source = request()
        first = source.implementation_tasks[0]
        second = NotionImplementationTask("task-implementation-0002", "assignment-implementation-0002", "Review content", "in_progress", "Working", "Regina", "medium", "2026-09-02", "copywriter", (first.task_id,), ("artifact-strategy-0001",), "notion-user-regina-0001")
        third = NotionImplementationTask("task-implementation-0003", "assignment-implementation-0003", "Measure content", "not_started", "", "", "low", "2026-09-03", "concept", (first.task_id, second.task_id), ("artifact-strategy-0001", "artifact-roadmap-0001"))
        forward = replace(source, implementation_tasks=(first, second, third))
        reversed_tuples = replace(third, dependencies=tuple(reversed(third.dependencies)), artifact_relations=tuple(reversed(third.artifact_relations)))
        reordered = replace(source, implementation_tasks=(reversed_tuples, second, first))
        self.assertEqual(build_notion_import_pack(forward).files, build_notion_import_pack(reordered).files)

    def test_csv_contract_headers_rows_hashes_and_line_endings_are_exact(self) -> None:
        pack = build_notion_import_pack(request())
        descriptors = {item["file_name"]: item for item in pack.manifest["files"]}
        for contract in CSV_CONTRACTS:
            with self.subTest(file_name=contract.file_name):
                content = pack.files[f"notion-import/{contract.file_name}"]
                rows = list(csv.reader(io.StringIO(content.decode("utf-8"), newline="")))
                self.assertEqual([column.name for column in contract.columns], rows[0])
                self.assertNotIn(b"\r", content)
                descriptor = descriptors[contract.file_name]
                self.assertEqual(len(rows) - 1, descriptor["row_count"])
                self.assertEqual(hashlib.sha256(content).hexdigest(), descriptor["content_sha256"])

    def test_manifest_and_publication_hashes_are_independently_recomputed(self) -> None:
        source = request()
        pack = build_notion_import_pack(source)
        manifest = copy.deepcopy(pack.manifest)
        recorded_hash = manifest.pop("manifest_sha256")
        preimage = json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        self.assertEqual(hashlib.sha256(preimage).hexdigest(), recorded_hash)
        expected_publication_hash = hashlib.sha256(json.dumps(dict(source.publication_registry.payload), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
        publication_row = next(row for row in pack.manifest["source_records"] if row["source_record_id"] == source.publication_registry.record_id)
        self.assertEqual(expected_publication_hash, publication_row["source_sha256"])

    def test_replay_is_idempotent_only_for_exact_canonical_pack(self) -> None:
        existing = build_notion_import_pack(request()).manifest
        replay = build_notion_import_pack(request()).manifest
        self.assertTrue(validate_notion_import_replay(existing, replay).idempotent)
        changed = copy.deepcopy(replay)
        changed["task_rows"][-1]["comments"] = "Changed"
        result = validate_notion_import_replay(existing, changed)
        self.assertFalse(result.idempotent)
        self.assertIn("DELIVERY_REPLAY_CONFLICT", {error.code for error in result.errors})

    def test_mapping_and_import_order_define_the_exact_closed_contract(self) -> None:
        pack = build_notion_import_pack(request())
        mapping = markdown_table_rows(pack.files["notion-import/PROPERTY_MAPPING.md"].decode("utf-8"))
        expected = [(contract.file_name, column.name, column.property_type, column.authority) for contract in CSV_CONTRACTS for column in contract.columns]
        self.assertEqual(expected, mapping[-len(expected):])
        self.assertNotIn("Core read-only or Notion implementation", pack.files["notion-import/PROPERTY_MAPPING.md"].decode("utf-8"))
        order = pack.files["notion-import/IMPORT_ORDER.md"].decode("utf-8")
        sequence = [line.split("`")[1] for line in order.splitlines() if line[:1].isdigit() and "`" in line]
        self.assertEqual(14, len(sequence))
        self.assertEqual(DESCRIPTORS, set(sequence))
        self.assertEqual(1, sequence.count("projects.csv"))
        self.assertIn("## Contract Resolution", order)
        self.assertIn("`projects.csv` imports the customer row before the project row.", order)
        self.assertIn("no separate run, step, escalation, or command files", order)

    def test_checkpoint_and_unrelated_canonical_approval_ids_are_exact(self) -> None:
        pack = build_notion_import_pack(request())
        checkpoints = pack.manifest["performance_checkpoint_rows"]
        self.assertEqual([30, 60, 90], [row["day_after_publication"] for row in checkpoints])
        self.assertEqual({"approval-caller-f7a301", "approval-caller-9c42be", "approval-caller-a81d06", "approval-caller-3e7bf9", "approval-caller-d514ac", "approval-caller-61f8d2"}, {row["external_id"] for row in pack.manifest["approval_rows"]})
        self.assertFalse(any(row["external_id"].removeprefix("approval-caller-") in row["artifact_external_id"] for row in pack.manifest["approval_rows"]))


if __name__ == "__main__":
    unittest.main()
