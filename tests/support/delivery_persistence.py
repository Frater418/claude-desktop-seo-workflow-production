from __future__ import annotations

import hashlib
from pathlib import Path

from services.operator_api.delivery_models import (
    DeliveryCreateRequest,
    DeliveryExportResult,
    DeliveryPackageRecord,
)
from services.operator_api.delivery_persistence_values import (
    DeliveryFailureBoundary,
    DeliveryPersistRequest,
    DeliveryRecoverySidecar,
    canonical_json_bytes,
)
from services.operator_api.delivery_replay_recovery import DeliveryReplayRecovery

from .delivery_api import PROJECT, TENANT, delivery_request


ARCHIVE = b"immutable delivery archive"
ARCHIVE_SHA = hashlib.sha256(ARCHIVE).hexdigest()
PACKAGE_SHA = hashlib.sha256(b"package material").hexdigest()


def transaction(
    *,
    export_id: str = "delivery-export-00000001",
    package_id: str = "delivery-package-00000001",
    result_id: str = "delivery-export-result-00000001",
    request_id: str = "delivery-export-request-00000001",
    idempotency_key: str = "idem-delivery-00000001",
    created_at: str = "2026-08-22T10:15:30Z",
) -> DeliveryPersistRequest:
    sequence = request_id.rsplit("-", maxsplit=1)[-1]
    payload = delivery_request(
        export_id=export_id,
        delivery_package_id=package_id,
        delivery_export_result_id=result_id,
        delivery_export_request_id=request_id,
        idempotency_key=idempotency_key,
        created_at=created_at,
    )
    payload["role_package_requests"][0]["role_handoff_manifest_id"] = f"role-handoff-copywriter-{sequence}"
    payload["role_package_requests"][1]["role_handoff_manifest_id"] = f"role-handoff-developer-{sequence}"
    payload["notion_import_request"]["notion_import_manifest_id"] = f"notion-import-{sequence}"
    create_request = DeliveryCreateRequest.model_validate(
        payload
    )
    manifest_sha = hashlib.sha256(b"manifest").hexdigest()
    package_record = DeliveryPackageRecord.model_validate(
        {
            "delivery_package_id": package_id,
            "schema_version": "1.0.0",
            "tenant_id": TENANT,
            "project_id": PROJECT,
            "export_id": export_id,
            "scope": "checkpoint",
            "source_snapshot_revision": 11,
            "source_records": [{"tenant_id": TENANT, "project_id": PROJECT, "source_kind": "project", "source_record_id": PROJECT, "source_revision": 1, "source_sha256": manifest_sha}],
            "required_deliverables": [{"deliverable_id": "strategy", "source_record_id": "artifact-strategy-0001", "source_sha256": manifest_sha, "package_path": "strategy/topic.md", "release_status": "released"}],
            "missing_deliverables": [],
            "package_paths": ["strategy/topic.md"],
            "package_sha256": PACKAGE_SHA,
            "zip_sha256": ARCHIVE_SHA,
            "role_packages": [{"role": "copywriter", "role_handoff_manifest_id": f"role-handoff-copywriter-{sequence}", "manifest_path": "roles/copywriter.json", "manifest_sha256": manifest_sha}, {"role": "developer", "role_handoff_manifest_id": f"role-handoff-developer-{sequence}", "manifest_path": "roles/developer.json", "manifest_sha256": manifest_sha}],
            "notion_import_manifest": {"notion_import_manifest_id": f"notion-import-{sequence}", "manifest_path": "notion/import.json", "manifest_sha256": manifest_sha},
            "created_at": created_at,
            "package_revision": 7,
            "derived_status": "archived",
        }
    )
    result = DeliveryExportResult.model_validate(
        {
            "delivery_export_result_id": result_id,
            "schema_version": "1.0.0",
            "tenant_id": TENANT,
            "project_id": PROJECT,
            "delivery_export_request_id": request_id,
            "export_id": export_id,
            "delivery_package_id": package_id,
            "source_snapshot_revision": 11,
            "replay_state": "created",
            "export_path": f"delivery/exports/{export_id}",
            "zip_path": f"delivery/exports/{export_id}/archive.zip",
            "package_sha256": PACKAGE_SHA,
            "zip_sha256": ARCHIVE_SHA,
            "zip_size_bytes": len(ARCHIVE),
            "delivery_manifest": {"manifest_id": package_id, "relative_path": "export-manifest.json", "content_sha256": manifest_sha},
            "role_handoff_manifests": [{"manifest_id": f"role-handoff-copywriter-{sequence}", "relative_path": "roles/copywriter.json", "content_sha256": manifest_sha}, {"manifest_id": f"role-handoff-developer-{sequence}", "relative_path": "roles/developer.json", "content_sha256": manifest_sha}],
            "notion_import_manifest": {"manifest_id": f"notion-import-{sequence}", "relative_path": "notion/import.json", "content_sha256": manifest_sha},
            "created_at": created_at,
        }
    )
    return DeliveryPersistRequest(tenant_id=TENANT, project_id=PROJECT, create_request=create_request, result=result, package_record=package_record, archive_bytes=ARCHIVE)


def write_incomplete_delivery(workspace: Path, request: DeliveryPersistRequest, boundary: DeliveryFailureBoundary) -> None:
    root = workspace / "v2/operator/delivery"
    recovery = root / DeliveryReplayRecovery.recovery_relative(request.idempotency_key)
    recovery.parent.mkdir(parents=True, exist_ok=True)
    recovery.write_bytes(canonical_json_bytes(DeliveryRecoverySidecar.from_request(request).model_dump(mode="json")))
    files: dict[DeliveryFailureBoundary, tuple[tuple[str, bytes], ...]] = {
        DeliveryFailureBoundary.SIDECAR_WRITTEN: (),
        DeliveryFailureBoundary.ARCHIVE_WRITTEN: (("request.json", canonical_json_bytes(request.create_request.model_dump(mode="json"))), ("archive.zip", request.archive_bytes)),
        DeliveryFailureBoundary.PACKAGE_RECORD_WRITTEN: (("request.json", canonical_json_bytes(request.create_request.model_dump(mode="json"))), ("archive.zip", request.archive_bytes), ("delivery-package-record.json", canonical_json_bytes(request.package_record.model_dump(mode="json")))),
        DeliveryFailureBoundary.RESULT_WRITTEN: (("request.json", canonical_json_bytes(request.create_request.model_dump(mode="json"))), ("archive.zip", request.archive_bytes), ("delivery-package-record.json", canonical_json_bytes(request.package_record.model_dump(mode="json"))), ("result.json", canonical_json_bytes(request.result.model_dump(mode="json")))),
        DeliveryFailureBoundary.BEFORE_IDEMPOTENCY: (("request.json", canonical_json_bytes(request.create_request.model_dump(mode="json"))), ("archive.zip", request.archive_bytes), ("delivery-package-record.json", canonical_json_bytes(request.package_record.model_dump(mode="json"))), ("result.json", canonical_json_bytes(request.result.model_dump(mode="json")))),
        DeliveryFailureBoundary.BEFORE_SIDECAR_REMOVAL: (("request.json", canonical_json_bytes(request.create_request.model_dump(mode="json"))), ("archive.zip", request.archive_bytes), ("delivery-package-record.json", canonical_json_bytes(request.package_record.model_dump(mode="json"))), ("result.json", canonical_json_bytes(request.result.model_dump(mode="json")))),
    }
    for name, content in files[boundary]:
        path = root / "exports" / request.result.export_id / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
