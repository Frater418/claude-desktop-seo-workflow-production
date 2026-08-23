import { describe, expect, it } from "vitest"
import { parseDeliveryExportHistory, parseDeliveryExportResult, parseDeliveryPackageRecord, parseDeliveryPreview } from "./deliveryReadModels"
import { OperatorReadModelError } from "./readModels"

const tenantId = "tenant-acme"
const projectId = "project-acme"
const hash = "a".repeat(64)

function preview() {
  return {
    scope: "checkpoint",
    policy_eligible: true,
    missing_deliverable_ids: [],
    errors: [],
    selected_deliverables: [{ artifact_id: "artifact-delivery-0001", content_sha256: hash, deliverable_id: "strategy", output_path: "packages/strategy.md", release_status: "released", role: "reviewer", step_id: "1" }],
  }
}

function result() {
  return {
    delivery_export_result_id: "delivery-export-result-abcdefgh",
    schema_version: "1.0.0",
    tenant_id: tenantId,
    project_id: projectId,
    delivery_export_request_id: "delivery-export-request-abcdefgh",
    export_id: "delivery-export-abcdefgh",
    delivery_package_id: "delivery-package-abcdefgh",
    source_snapshot_revision: 3,
    replay_state: "created",
    export_path: "exports/checkpoint.json",
    zip_path: "exports/checkpoint.zip",
    package_sha256: hash,
    zip_sha256: hash,
    zip_size_bytes: 128,
    delivery_manifest: { manifest_id: "delivery-package-abcdefgh", relative_path: "manifests/delivery.json", content_sha256: hash },
    role_handoff_manifests: [{ manifest_id: "role-handoff-abcdefgh", relative_path: "manifests/copywriter.json", content_sha256: hash }],
    notion_import_manifest: { manifest_id: "notion-import-abcdefgh", relative_path: "manifests/notion.json", content_sha256: hash },
    created_at: "2026-08-22T10:00:00Z",
  }
}

function record() {
  return {
    delivery_package_id: "delivery-package-abcdefgh",
    schema_version: "1.0.0",
    tenant_id: tenantId,
    project_id: projectId,
    export_id: "delivery-export-abcdefgh",
    scope: "checkpoint",
    source_snapshot_revision: 3,
    source_records: [{ tenant_id: tenantId, project_id: projectId, source_kind: "artifact", source_record_id: "artifact-delivery-0001", source_revision: 3, source_sha256: hash }],
    required_deliverables: [{ deliverable_id: "strategy", source_record_id: "artifact-delivery-0001", source_sha256: hash, package_path: "packages/strategy.md", release_status: "released" }],
    missing_deliverables: [],
    package_paths: ["packages/strategy.md"],
    package_sha256: hash,
    zip_sha256: hash,
    role_packages: [{ role: "copywriter", role_handoff_manifest_id: "role-handoff-abcdefgh", manifest_path: "manifests/copywriter.json", manifest_sha256: hash }],
    notion_import_manifest: { notion_import_manifest_id: "notion-import-abcdefgh", manifest_path: "manifests/notion.json", manifest_sha256: hash },
    created_at: "2026-08-22T10:00:00Z",
    package_revision: 2,
    derived_status: "prepared",
  }
}

describe("Delivery read models", () => {
  it("parses a preview only when the response scope matches the request", () => {
    expect(parseDeliveryPreview(preview(), "checkpoint")).toEqual({ scope: "checkpoint", policyEligible: true, missingDeliverableIds: [], errors: [], selectedDeliverables: [{ artifactId: "artifact-delivery-0001", contentSha256: hash, deliverableId: "strategy", outputPath: "packages/strategy.md", releaseStatus: "released", role: "reviewer", stepId: "1" }] })
    expect(parseDeliveryPreview({ ...preview(), scope: "final" }, "final")).toMatchObject({ scope: "final" })
    expect(() => parseDeliveryPreview({ ...preview(), scope: "final" }, "checkpoint")).toThrow(OperatorReadModelError)
  })

  it("parses a created export result with its route identity", () => {
    expect(parseDeliveryExportResult(result(), tenantId, projectId)).toMatchObject({ exportId: "delivery-export-abcdefgh", deliveryPackageId: "delivery-package-abcdefgh", sourceSnapshotRevision: 3, zipSizeBytes: 128 })
    expect(() => parseDeliveryExportResult({ ...result(), tenant_id: "tenant-other" }, tenantId, projectId)).toThrow(OperatorReadModelError)
  })

  it("parses every history entry instead of silently dropping malformed entries", () => {
    expect(parseDeliveryExportHistory({ data: [result()] }, tenantId, projectId)).toHaveLength(1)
    expect(() => parseDeliveryExportHistory({ data: [result(), { delivery_export_result_id: "delivery-export-result-abcdefgh" }] }, tenantId, projectId)).toThrow(OperatorReadModelError)
  })

  it("parses a package record bound to the requested export", () => {
    expect(parseDeliveryPackageRecord(record(), tenantId, projectId, "delivery-export-abcdefgh")).toMatchObject({ packageRevision: 2, derivedStatus: "prepared", packagePaths: ["packages/strategy.md"] })
    expect(() => parseDeliveryPackageRecord({ ...record(), export_id: "delivery-export-otheraaaa" }, tenantId, projectId, "delivery-export-abcdefgh")).toThrow(OperatorReadModelError)
  })

  it.each([
    ["an unknown literal", () => parseDeliveryPreview({ ...preview(), selected_deliverables: [{ ...preview().selected_deliverables[0], release_status: "unknown" }] }, "checkpoint")],
    ["a nonpositive ZIP size", () => parseDeliveryExportResult({ ...result(), zip_size_bytes: 0 }, tenantId, projectId)],
    ["an uppercase checksum", () => parseDeliveryExportResult({ ...result(), zip_sha256: "A".repeat(64) }, tenantId, projectId)],
    ["a timestamp without a timezone", () => parseDeliveryExportResult({ ...result(), created_at: "2026-08-22T10:00:00" }, tenantId, projectId)],
    ["a traversal path", () => parseDeliveryPackageRecord({ ...record(), package_paths: ["../package.zip"] }, tenantId, projectId, "delivery-export-abcdefgh")],
    ["an empty required nested array", () => parseDeliveryExportResult({ ...result(), role_handoff_manifests: [] }, tenantId, projectId)],
  ])("rejects %s", (_description, parse) => {
    expect(parse).toThrow(OperatorReadModelError)
  })
})
