import { afterEach, describe, expect, it, vi } from "vitest"
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import type { OperatorApiClient } from "../../api/client"
import type { DeliveryExportResultRead, DeliveryPackageRecordRead, DeliveryPreviewRead, DeliveryScope } from "../../api/deliveryReadModels"
import type { DeliveryCreateRequest } from "../../generated/api-types"
import { DeliveryCenter } from "./DeliveryCenter"

const tenantId = "tenant-delivery"
const projectId = "project-delivery"
const sha256 = "a".repeat(64)
const taskJson = JSON.stringify([{ task_id: "task-delivery-0001", assignment_id: "assignment-delivery-0001", title: "Landingpage pruefen", status: "not_started", comments: "", source_assignee: "Redaktion", priority: "high", deadline: "2026-09-01", role: "copywriter", dependencies: [], artifact_relations: [], notion_user_id: "notion-user-delivery-0001" }])

type DeliveryClient = Pick<OperatorApiClient, "previewDelivery" | "createDeliveryExport" | "listDeliveryExports" | "getDeliveryExport" | "downloadDeliveryExport">
type DeliveryPreviewMethod = DeliveryClient["previewDelivery"]; type DeliveryCreateMethod = DeliveryClient["createDeliveryExport"]; type DeliveryHistoryMethod = DeliveryClient["listDeliveryExports"]; type DeliveryRecordMethod = DeliveryClient["getDeliveryExport"]; type DeliveryDownloadMethod = DeliveryClient["downloadDeliveryExport"]

const checkpointPreview: DeliveryPreviewRead = {
  scope: "checkpoint",
  policyEligible: true,
  missingDeliverableIds: ["developer-handoff"],
  errors: [],
  selectedDeliverables: [
    { artifactId: "artifact-strategy-0001", contentSha256: sha256, deliverableId: "strategy", outputPath: "outputs/strategy.md", releaseStatus: "released", role: "copywriter", stepId: "1" },
    { artifactId: "artifact-design-0001", contentSha256: null, deliverableId: "design", outputPath: null, releaseStatus: "draft", role: "developer", stepId: "1c" },
  ],
}

const finalPreview: DeliveryPreviewRead = { ...checkpointPreview, scope: "final", policyEligible: false, errors: [{ code: "ERR_FINAL_RELEASE", message: "Die finale Uebergabe braucht freigegebene Lieferobjekte." }] }

const historyResult: DeliveryExportResultRead = {
  tenantId,
  projectId,
  deliveryExportResultId: "delivery-export-result-history-0001",
  deliveryExportRequestId: "delivery-export-request-history-0001",
  deliveryPackageId: "delivery-package-history-0001",
  exportId: "delivery-export-history-0001",
  sourceSnapshotRevision: 3,
  replayState: "created",
  exportPath: "delivery/history/result.json",
  zipPath: "delivery/history/archive.zip",
  packageSha256: sha256,
  zipSha256: sha256,
  zipSizeBytes: 1024,
  deliveryManifest: { manifestId: "delivery-package-history-0001", relativePath: "delivery/history/manifest.json", contentSha256: sha256 },
  roleHandoffManifests: [{ manifestId: "role-handoff-history-0001", relativePath: "delivery/history/copywriter.json", contentSha256: sha256 }],
  notionImportManifest: { manifestId: "notion-import-history-0001", relativePath: "delivery/history/notion.json", contentSha256: sha256 },
  createdAt: "2026-08-22T10:00:00Z",
}

function recordFor(request: DeliveryCreateRequest): DeliveryPackageRecordRead {
  return {
    tenantId,
    projectId,
    deliveryPackageId: request.delivery_package_id,
    exportId: request.export_id,
    scope: request.export_request.scope,
    sourceSnapshotRevision: request.export_request.source_snapshot_revision,
    sourceRecords: [{ tenantId, projectId, sourceKind: "project", sourceRecordId: projectId, sourceRevision: request.export_request.source_snapshot_revision, sourceSha256: sha256 }],
    requiredDeliverables: [{ deliverableId: "strategy", sourceRecordId: "artifact-strategy-0001", sourceSha256: sha256, packagePath: "delivery/strategy.md", releaseStatus: "released" }],
    missingDeliverables: [],
    packagePaths: ["delivery/strategy.md", "delivery/archive.zip"],
    packageSha256: sha256,
    zipSha256: sha256,
    rolePackages: request.role_package_requests.map((item) => ({ role: item.role, roleHandoffManifestId: item.role_handoff_manifest_id, manifestPath: `delivery/${item.role}.json`, manifestSha256: sha256 })),
    notionImportManifest: { notionImportManifestId: request.notion_import_request.notion_import_manifest_id, manifestPath: "delivery/notion.json", manifestSha256: sha256 },
    createdAt: request.export_request.created_at,
    packageRevision: request.package_revision,
    derivedStatus: "archived",
    taskAssignmentManifestPath: "delivery/tasks.json",
    qualitySummary: { summaryPath: "delivery/quality.json", contentSha256: sha256 },
    exportManifestPath: "delivery/export.json",
    checksumsPath: "delivery/checksums.json",
  }
}

function resultFor(request: DeliveryCreateRequest): DeliveryExportResultRead {
  return {
    tenantId,
    projectId,
    deliveryExportResultId: request.delivery_export_result_id,
    deliveryExportRequestId: request.export_request.delivery_export_request_id,
    deliveryPackageId: request.delivery_package_id,
    exportId: request.export_id,
    sourceSnapshotRevision: request.export_request.source_snapshot_revision,
    replayState: "created",
    exportPath: "delivery/export/result.json",
    zipPath: "delivery/export/archive.zip",
    packageSha256: sha256,
    zipSha256: sha256,
    zipSizeBytes: 2048,
    deliveryManifest: { manifestId: request.delivery_package_id, relativePath: "delivery/export/manifest.json", contentSha256: sha256 },
    roleHandoffManifests: request.role_package_requests.map((item) => ({ manifestId: item.role_handoff_manifest_id, relativePath: `delivery/export/${item.role}.json`, contentSha256: sha256 })),
    notionImportManifest: { manifestId: request.notion_import_request.notion_import_manifest_id, relativePath: "delivery/export/notion.json", contentSha256: sha256 },
    createdAt: request.export_request.created_at,
  }
}

function historyRecord(): DeliveryPackageRecordRead {
  const request: DeliveryCreateRequest = {
    delivery_export_result_id: historyResult.deliveryExportResultId,
    delivery_package_id: historyResult.deliveryPackageId,
    export_id: historyResult.exportId,
    export_request: { delivery_export_request_id: historyResult.deliveryExportRequestId, schema_version: "1.0.0", tenant_id: tenantId, project_id: projectId, scope: "checkpoint", draft_inclusion_policy: "include_explicit_drafts", idempotency_key: "idem-history-0001", created_at: historyResult.createdAt, source_snapshot_revision: historyResult.sourceSnapshotRevision, requested_role_packages: ["copywriter"] },
    package_revision: 2,
    role_package_requests: [{ role: "copywriter", role_handoff_manifest_id: "role-handoff-history-0001" }],
    notion_import_request: { notion_import_manifest_id: "notion-import-history-0001", customer_external_id: "customer-history", implementation_tasks: [{ task_id: "task-history-0001", assignment_id: "assignment-history-0001", title: "Historische Aufgabe", status: "done", comments: "", source_assignee: "Redaktion", priority: "high", deadline: "2026-09-01", role: "copywriter", dependencies: [], artifact_relations: [], notion_user_id: "notion-user-history-0001" }], publication_registry: { publication_registry_record_id: "publication-registry-history-0001", urls: ["https://example.test/history"] } },
  }
  return recordFor(request)
}

function createClient() {
  const records = new Map<string, DeliveryPackageRecordRead>([[historyResult.exportId, historyRecord()]])
  const previewDelivery = vi.fn<DeliveryPreviewMethod>(async (_projectId, scope) => {
    switch (scope) {
      case "checkpoint": return checkpointPreview
      case "final": return finalPreview
    }
  })
  const createDeliveryExport = vi.fn<DeliveryCreateMethod>(async (_projectId, request) => {
    const record = recordFor(request)
    records.set(request.export_id, record)
    return resultFor(request)
  })
  const listDeliveryExports = vi.fn<DeliveryHistoryMethod>(async () => [historyResult])
  const getDeliveryExport = vi.fn<DeliveryRecordMethod>(async (_projectId, exportId) => {
    const record = records.get(exportId)
    if (record === undefined) throw new Error("Export nicht gefunden")
    return record
  })
  const downloadDeliveryExport = vi.fn<DeliveryDownloadMethod>(async () => ({ blob: new Blob(["zip"]), filename: "server-export.zip", etag: "delivery-etag" }))
  const api = { previewDelivery, createDeliveryExport, listDeliveryExports, getDeliveryExport, downloadDeliveryExport } satisfies DeliveryClient
  return { api, previewDelivery, createDeliveryExport, listDeliveryExports, getDeliveryExport, downloadDeliveryExport }
}

function fillCheckpointForm(): void {
  fireEvent.change(screen.getByLabelText("Exportumfang"), { target: { value: "checkpoint" } })
  fireEvent.change(screen.getByLabelText("Exportfolge"), { target: { value: "7" } })
  fireEvent.change(screen.getByLabelText("Quell-Snapshot-Revision"), { target: { value: "3" } })
  fireEvent.change(screen.getByLabelText("Paketrevision"), { target: { value: "2" } })
  fireEvent.change(screen.getByLabelText("Entwurfsrichtlinie"), { target: { value: "include_explicit_drafts" } })
  fireEvent.click(screen.getByLabelText("Copywriter"))
  fireEvent.change(screen.getByLabelText("Externe Kundenkennung"), { target: { value: "customer-delivery" } })
  fireEvent.change(screen.getByLabelText("Publikations-URLs"), { target: { value: "https://example.test/delivery" } })
  fireEvent.change(screen.getByLabelText("Notion-Implementierungsaufgaben"), { target: { value: taskJson } })
}

afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

describe("DeliveryCenter", () => {
  it("loads checkpoint, final, and history in parallel with one abort signal and renders delivery status", async () => {
    const client = createClient()
    const view = render(<DeliveryCenter api={client.api} tenantId={tenantId} projectId={projectId} />)

    expect(await screen.findByText("Checkpoint-Vorschau")).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Finale Uebergabe" })).toBeInTheDocument()
    expect(screen.getAllByText("Freigegeben")).not.toHaveLength(0)
    expect(screen.getAllByText("Entwurf")).not.toHaveLength(0)
    expect(screen.getAllByText("Developer-Handoff")).not.toHaveLength(0)
    expect(client.previewDelivery).toHaveBeenCalledTimes(2)
    expect(client.listDeliveryExports).toHaveBeenCalledOnce()
    const checkpointSignal = client.previewDelivery.mock.calls[0]?.[2]
    const finalSignal = client.previewDelivery.mock.calls[1]?.[2]
    const historySignal = client.listDeliveryExports.mock.calls[0]?.[1]
    expect(checkpointSignal).toBe(finalSignal)
    expect(checkpointSignal).toBe(historySignal)

    view.rerender(<DeliveryCenter api={client.api} tenantId={tenantId} projectId="project-delivery-next" />)
    await waitFor(() => expect(client.previewDelivery).toHaveBeenCalledTimes(4))
    expect(client.listDeliveryExports).toHaveBeenCalledTimes(2)
    expect(checkpointSignal?.aborted).toBe(true)

    view.unmount()

    expect(client.previewDelivery.mock.calls[2]?.[2]?.aborted).toBe(true)
  })

  it("keeps failed preview and history panels independent from a ready sibling", async () => {
    const client = createClient()
    client.previewDelivery.mockImplementation(async (_projectId, scope) => {
      if (scope === "checkpoint") throw new Error("Checkpoint nicht erreichbar")
      return finalPreview
    })
    client.listDeliveryExports.mockRejectedValue(new Error("Historie nicht erreichbar"))

    render(<DeliveryCenter api={client.api} tenantId={tenantId} projectId={projectId} />)

    expect(await screen.findByText("Checkpoint nicht erreichbar")).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Finale Uebergabe" })).toBeInTheDocument()
    expect(screen.getByText("Historie nicht erreichbar")).toBeInTheDocument()
  })

  it("starts incomplete and blocks final creation when policy eligibility is false", async () => {
    const client = createClient()
    render(<DeliveryCenter api={client.api} tenantId={tenantId} projectId={projectId} />)
    await screen.findByText("Checkpoint-Vorschau")

    expect(screen.getByText("Unvollstaendig")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Export erstellen" })).toBeDisabled()
    fireEvent.change(screen.getByLabelText("Exportumfang"), { target: { value: "final" } })
    expect(screen.getByText("Export nicht zulaessig")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Export erstellen" })).toBeDisabled()
  })

  it("creates with explicit input, reads back the canonical record, and exposes the record manifests", async () => {
    const client = createClient()
    render(<DeliveryCenter api={client.api} tenantId={tenantId} projectId={projectId} />)
    await screen.findByText("Checkpoint-Vorschau")
    fillCheckpointForm()

    fireEvent.click(screen.getByRole("button", { name: "Export erstellen" }))

    await waitFor(() => expect(client.createDeliveryExport).toHaveBeenCalledOnce())
    const request = client.createDeliveryExport.mock.calls[0]?.[1]
    expect(request?.export_request.created_at).toMatch(/^\d{4}-\d{2}-\d{2}T/)
    expect(client.getDeliveryExport).toHaveBeenCalledWith(projectId, request?.export_id, expect.any(AbortSignal))
    expect(await screen.findByText("Export wurde erstellt und kanonisch gelesen.")).toBeInTheDocument()
    expect(screen.getByText(/delivery\/notion\.json/)).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /Copywriter.*herunterladen/i })).toBeNull()
  })

  it("retries the exact pending request and requires a higher sequence after submitted input changes", async () => {
    const client = createClient()
    let attempt = 0
    client.createDeliveryExport.mockImplementation(async (_projectId, request) => {
      attempt += 1
      if (attempt === 1) throw new Error("Erste Erstellung fehlgeschlagen")
      return resultFor(request)
    })
    render(<DeliveryCenter api={client.api} tenantId={tenantId} projectId={projectId} />)
    await screen.findByText("Checkpoint-Vorschau")
    fillCheckpointForm()

    fireEvent.click(screen.getByRole("button", { name: "Export erstellen" }))
    expect(await screen.findByText("Erste Erstellung fehlgeschlagen")).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: "Export unveraendert wiederholen" }))
    await waitFor(() => expect(client.createDeliveryExport).toHaveBeenCalledTimes(2))
    expect(client.createDeliveryExport.mock.calls[1]?.[1]).toBe(client.createDeliveryExport.mock.calls[0]?.[1])

    fireEvent.change(screen.getByLabelText("Paketrevision"), { target: { value: "3" } })
    expect(await screen.findByText("Die Exportdaten wurden nach einem Sendeversuch geaendert. Erhoehen Sie die Exportfolge fuer einen neuen Export.")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Export erstellen" })).toBeDisabled()
    fireEvent.change(screen.getByLabelText("Exportfolge"), { target: { value: "8" } })
    expect(screen.getByRole("button", { name: "Export erstellen" })).toBeEnabled()
  })

  it("loads a selected history record and downloads only the server-named whole ZIP", async () => {
    const client = createClient()
    const clickedDownloads: string[] = []
    const anchorClick = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement): void { clickedDownloads.push(this.download) })
    const createObjectUrl = vi.fn(() => "blob:delivery")
    const revokeObjectUrl = vi.fn()
    vi.stubGlobal("URL", { createObjectURL: createObjectUrl, revokeObjectURL: revokeObjectUrl })
    render(<DeliveryCenter api={client.api} tenantId={tenantId} projectId={projectId} />)
    await screen.findByText("Exporthistorie")

    fireEvent.click(screen.getByRole("button", { name: "Export delivery-export-history-0001 waehlen" }))
    expect(await screen.findByText("Paketstatus")).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: "Gesamtes ZIP herunterladen" }))

    await waitFor(() => expect(client.downloadDeliveryExport).toHaveBeenCalledWith(projectId, historyResult.exportId, expect.any(AbortSignal)))
    expect(clickedDownloads).toEqual(["server-export.zip"])
    expect(createObjectUrl).toHaveBeenCalledOnce()
    expect(revokeObjectUrl).toHaveBeenCalledWith("blob:delivery")
    anchorClick.mockRestore()
  })

  it("prepares a local no-write Notion preview and makes unresolved assignees visible", async () => {
    const client = createClient()
    const unresolvedTaskJson = taskJson.replace("\"Redaktion\"", "\"\"").replace("\"notion-user-delivery-0001\"", "null")
    render(<DeliveryCenter api={client.api} tenantId={tenantId} projectId={projectId} />)
    await screen.findByText("Checkpoint-Vorschau")
    fillCheckpointForm()
    fireEvent.change(screen.getByLabelText("Notion-Implementierungsaufgaben"), { target: { value: unresolvedTaskJson } })

    expect(screen.getByText("Offene Notion-Zuordnungen").parentElement).toHaveTextContent("1")
    fireEvent.click(screen.getByRole("button", { name: "Notion-Uebergabe vorbereiten" }))

    expect(await screen.findByText("Diese Vorschau bereitet nur das manuelle Notion-Importpaket vor. Es werden keine externen Daten geschrieben.")).toBeInTheDocument()
    expect(client.createDeliveryExport).not.toHaveBeenCalled()
    expect(client.getDeliveryExport).not.toHaveBeenCalled()
    expect(client.downloadDeliveryExport).not.toHaveBeenCalled()
  })
})
