from __future__ import annotations

import hashlib
from types import MappingProxyType

from services.delivery.inventory import Deliverable, DeliveryInventory, InventoryFile
from services.delivery.notion_import import NotionImplementationTask, NotionImportBuildContext, NotionImportRequest, PublicationRegistryRecord
from services.delivery.record_normalization import CanonicalRecord


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
