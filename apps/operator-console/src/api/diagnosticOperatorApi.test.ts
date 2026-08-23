import { describe, expect, it } from "vitest"
import type {
  ActionConfirmRequest,
  ActionConfirmResult,
  ActionIntent,
  ActionPreview,
  ArtifactCandidateSaveRequest,
  ArtifactValidationRequest,
  DataEnvelope,
  DiagnosticTraceOperation,
  IntakeAcceptanceRequest,
} from "../generated/api-types"
import type { DeliveryDownload } from "./deliveryDownload"
import type { DeliveryCreateRequest, DeliveryExportResultRead, DeliveryPreviewRead } from "./deliveryReadModels"
import type { ArtifactPreflightRead } from "./artifactPreflightReadModel"
import { createDiagnosticOperatorApiClient, type DiagnosticTraceRecorder } from "./diagnosticOperatorApi"
import type { OperatorApiClient } from "./client"
import { OperatorApiError } from "./operatorApiError"

const tenantId = "tenant-acme"
const projectId = "project-alpha"
const runId = "run-0001"
const customerMaterial = "Kundin: Maria Beispiel, https://customer.example/?private=secret"
const signal = new AbortController().signal

const intakeRequest = {
  confirmed: true,
  markdown: customerMaterial,
  preview_hash: "preview-intake-0001",
  reviewed: { tenant_id: tenantId, project_id: projectId, title: customerMaterial },
  source_sha256: "a".repeat(64),
} satisfies IntakeAcceptanceRequest

const intent = {
  action: "approve",
  expected_revision: 1,
  project_id: projectId,
  run_id: runId,
  step_id: "1",
  tenant_id: tenantId,
} satisfies ActionIntent

const confirmation = {
  confirmed: true,
  idempotency_key: "idem-confirm-0001",
  intent,
  preview_hash: "preview-admin-0001",
} satisfies ActionConfirmRequest

const artifactSave = {
  bundle: { execution_identity: { step_id: "4a" } },
  expected_parent_revision: 1,
  gate_context: { evidence_by_gate: { "GATE-4A": { content_complete: true } } },
  idempotency_key: "idem-artifact-0001",
  primary_document: { briefing: customerMaterial },
  run_id: runId,
  supporting_documents: [{ schema: { type: "FAQPage" } }],
} satisfies ArtifactCandidateSaveRequest

const artifactValidation = { bundle: artifactSave.bundle, content_sha256: "b".repeat(64), gate_context: artifactSave.gate_context, revision: 1, supporting_documents: artifactSave.supporting_documents ?? [] } satisfies ArtifactValidationRequest
const artifactPreflight: ArtifactPreflightRead = { artifactId: "artifact-step4a-0001", artifactHash: artifactValidation.content_sha256, artifactRevision: artifactValidation.revision, stepId: "4a", validationMode: "step_preflight", valid: true, derivedViews: [], localQualityGateRuns: [], report: "" }

const deliveryRequest = {
  delivery_export_result_id: "delivery-export-result-0001",
  delivery_package_id: "delivery-package-0001",
  export_id: "delivery-export-0001",
  export_request: {
    created_at: "2026-08-23T10:00:00Z",
    delivery_export_request_id: "delivery-export-request-0001",
    draft_inclusion_policy: "include_explicit_drafts",
    idempotency_key: "idem-delivery-0001",
    project_id: projectId,
    requested_role_packages: ["copywriter"],
    schema_version: "1.0.0",
    scope: "checkpoint",
    source_snapshot_revision: 1,
    tenant_id: tenantId,
  },
  notion_import_request: {
    customer_external_id: "customer-0001",
    implementation_tasks: [{ artifact_relations: [], assignment_id: "assignment-0001", comments: customerMaterial, deadline: "2026-08-24", dependencies: [], notion_user_id: null, priority: "high", role: "copywriter", source_assignee: "Heartweb", status: "not_started", task_id: "task-0001", title: customerMaterial }],
    notion_import_manifest_id: "notion-import-0001",
    publication_registry: { publication_registry_record_id: "publication-registry-0001", urls: ["https://customer.example/?private=secret"] },
  },
  package_revision: 1,
  role_package_requests: [{ role: "copywriter", role_handoff_manifest_id: "role-handoff-0001" }],
} satisfies DeliveryCreateRequest

const deliveryResult = {
  createdAt: "2026-08-23T10:00:00Z",
  deliveryExportRequestId: "delivery-export-request-0001",
  deliveryExportResultId: "delivery-export-result-0001",
  deliveryManifest: { contentSha256: "c".repeat(64), manifestId: "delivery-package-0001", relativePath: "delivery/export/manifest.json" },
  deliveryPackageId: "delivery-package-0001",
  exportId: "delivery-export-0001",
  exportPath: "delivery/export/result.json",
  notionImportManifest: { contentSha256: "d".repeat(64), manifestId: "notion-import-0001", relativePath: "delivery/export/notion.json" },
  packageSha256: "e".repeat(64),
  projectId,
  replayState: "created",
  roleHandoffManifests: [{ contentSha256: "f".repeat(64), manifestId: "role-handoff-0001", relativePath: "delivery/export/copywriter.json" }],
  sourceSnapshotRevision: 1,
  tenantId,
  zipPath: "delivery/export/archive.zip",
  zipSha256: "0".repeat(64),
  zipSizeBytes: 1,
} satisfies DeliveryExportResultRead

const dataEnvelope = { data: {} } satisfies DataEnvelope
const actionPreview = { allowed: true, blockers: [], consequence: {}, intent, preview_hash: "preview-admin-0001" } satisfies ActionPreview
const actionConfirmation = { canonical: {}, preview_hash: "preview-admin-0001", readback_urls: [], replay: false } satisfies ActionConfirmResult
const deliveryPreview = { errors: [], missingDeliverableIds: [], policyEligible: true, scope: "checkpoint", selectedDeliverables: [] } satisfies DeliveryPreviewRead
const download = { blob: new Blob(["zip"]), etag: "etag-0001", filename: "delivery.zip" } satisfies DeliveryDownload

type ApiOverrides = {
  readonly acceptMarkdownIntake?: OperatorApiClient["acceptMarkdownIntake"]
  readonly createDeliveryExport?: OperatorApiClient["createDeliveryExport"]
}

async function unexpected(): Promise<never> {
  throw new Error("Unexpected API method")
}

function createApi(overrides: ApiOverrides = {}): OperatorApiClient {
  const readyz: OperatorApiClient["readyz"] = async () => dataEnvelope
  const acceptMarkdownIntake: OperatorApiClient["acceptMarkdownIntake"] = async () => ({ projectId, tenantId })
  const saveArtifactRevision: OperatorApiClient["saveArtifactRevision"] = async () => dataEnvelope
  const validateArtifactRevision: OperatorApiClient["validateArtifactRevision"] = async () => artifactPreflight
  const previewAdminAction: OperatorApiClient["previewAdminAction"] = async () => actionPreview
  const confirmAdminAction: OperatorApiClient["confirmAdminAction"] = async () => actionConfirmation
  const previewDelivery: OperatorApiClient["previewDelivery"] = async () => deliveryPreview
  const createDeliveryExport: OperatorApiClient["createDeliveryExport"] = async () => deliveryResult
  const downloadDeliveryExport: OperatorApiClient["downloadDeliveryExport"] = async () => download
  return {
    acceptMarkdownIntake: overrides.acceptMarkdownIntake ?? acceptMarkdownIntake,
    compareArtifactRevisions: unexpected,
    confirmAdminAction,
    createDeliveryExport: overrides.createDeliveryExport ?? createDeliveryExport,
    downloadDeliveryExport,
    getArtifactContent: unexpected,
    getCurrentRun: unexpected,
    getDeliveryExport: unexpected,
    getIntegrationStatus: unexpected,
    getProject: unexpected,
    getRun: unexpected,
    getWorkflow: unexpected,
    listArtifactRevisions: unexpected,
    listArtifacts: unexpected,
    listContextPackages: unexpected,
    listDeliveryExports: unexpected,
    listGates: unexpected,
    listProjects: unexpected,
    listReleases: unexpected,
    listSteps: unexpected,
    listTasks: unexpected,
    previewAdminAction,
    previewDelivery,
    previewMarkdownIntake: unexpected,
    readyz,
    saveArtifactRevision,
    validateArtifactRevision,
  }
}

function recorder(entries: DiagnosticTraceOperation[]): DiagnosticTraceRecorder {
  return { record: async (entry) => { entries.push(entry) } }
}

function traced(api: OperatorApiClient, entries: DiagnosticTraceOperation[]): OperatorApiClient {
  return createDiagnosticOperatorApiClient({ api, now: () => new Date("2026-08-23T10:15:30.987Z"), reporter: recorder(entries), tenantId })
}

function firstEntry(entries: readonly DiagnosticTraceOperation[]): DiagnosticTraceOperation {
  const entry = entries.at(0)
  if (entry === undefined) throw new Error("Expected diagnostic entry")
  return entry
}

describe("Diagnostic operator API", () => {
  it("records exactly seven explicit operator actions after canonical success", async () => {
    // Given: a decorated client and requests containing customer material.
    const entries: DiagnosticTraceOperation[] = []
    const api = traced(createApi(), entries)

    // When: each allowlisted operator action succeeds.
    await api.acceptMarkdownIntake(intakeRequest, signal)
    await api.previewAdminAction(projectId, "approve", intent, signal)
    await api.confirmAdminAction(projectId, "approve", confirmation, signal)
    await api.saveArtifactRevision(projectId, artifactSave, signal)
    await api.validateArtifactRevision(projectId, "artifact-0001", artifactValidation, signal)
    await api.createDeliveryExport(projectId, deliveryRequest, signal)
    await api.downloadDeliveryExport(projectId, "delivery-export-0001", signal)

    // Then: each entry is deterministic, path-safe, and contains no customer request data.
    expect(entries.map((entry) => entry.action)).toEqual(["accept_markdown_intake", "preview_admin_action", "confirm_admin_action", "save_artifact_revision", "validate_artifact_revision", "create_delivery_export", "download_delivery_export"])
    expect(entries.map((entry) => entry.operation_id)).toEqual(["operation-0001-accept-markdown-intake", "operation-0002-preview-admin-action", "operation-0003-confirm-admin-action", "operation-0004-save-artifact-revision", "operation-0005-validate-artifact-revision", "operation-0006-create-delivery-export", "operation-0007-download-delivery-export"])
    expect(entries.map((entry) => entry.api_status)).toEqual([200, 200, 200, 200, 200, 201, 200])
    for (const entry of entries) {
      expect(entry.occurred_at).toBe("2026-08-23T10:15:30Z")
      expect(entry.expected_actions).toEqual([entry.action])
      expect(entry.rendered_actions).toEqual([entry.action])
      expect(entry.disabled_actions).toEqual([])
      expect(entry.evidence_references).toEqual([])
      expect(entry.route).not.toContain("?")
    }
    const serialized = JSON.stringify(entries)
    expect(serialized).not.toContain(customerMaterial)
    expect(serialized).not.toContain("https://customer.example")
    expect(serialized).not.toContain("private=secret")
  })

  it("delegates background reads unchanged without recording an operation", async () => {
    // Given: a raw client with read methods and a diagnostic recorder.
    const entries: DiagnosticTraceOperation[] = []
    const raw = createApi()
    const api = traced(raw, entries)

    // When: loading and delivery preview/readback methods run.
    await api.readyz(signal)
    await api.previewDelivery(projectId, "checkpoint", signal)

    // Then: the methods are unchanged and no background read is reported.
    expect(api.readyz).toBe(raw.readyz)
    expect(api.getArtifactContent).toBe(raw.getArtifactContent)
    expect(api.listArtifactRevisions).toBe(raw.listArtifactRevisions)
    expect(api.listDeliveryExports).toBe(raw.listDeliveryExports)
    expect(api.getDeliveryExport).toBe(raw.getDeliveryExport)
    expect(entries).toEqual([])
  })

  it("uses replay-aware Delivery status and preserves canonical success when reporting rejects", async () => {
    // Given: a replayed Delivery result and an unavailable diagnostic reporter.
    const replayResult = { ...deliveryResult, replayState: "replayed" } satisfies DeliveryExportResultRead
    const raw = createApi({ createDeliveryExport: async () => replayResult })
    const reporter: DiagnosticTraceRecorder = { record: async () => { throw new OperatorApiError({ kind: "network", message: "diagnostic unavailable", status: 0 }) } }
    const api = createDiagnosticOperatorApiClient({ api: raw, now: () => new Date("2026-08-23T10:15:30.987Z"), reporter, tenantId })

    // When: the canonical Delivery replay succeeds after diagnostic reporting rejects.
    await expect(api.createDeliveryExport(projectId, deliveryRequest, signal)).resolves.toEqual(replayResult)

    // Then: the diagnostic failure cannot mask the canonical result.
  })

  it("records bounded, path-free failures and rethrows the original operator error", async () => {
    // Given: primary actions that fail with and without a stable API code.
    const codedError = new OperatorApiError({ code: "ERR_OPERATOR_INPUT", kind: "http", message: customerMaterial, status: 422 })
    const codedEntries: DiagnosticTraceOperation[] = []
    const codedApi = traced(createApi({ acceptMarkdownIntake: async () => { throw codedError } }), codedEntries)
    const networkError = new OperatorApiError({ kind: "network", message: customerMaterial, status: 0 })
    const networkEntries: DiagnosticTraceOperation[] = []
    const networkApi = traced(createApi({ acceptMarkdownIntake: async () => { throw networkError } }), networkEntries)
    const unexpectedError = new Error(customerMaterial)
    const unexpectedEntries: DiagnosticTraceOperation[] = []
    const unexpectedApi = traced(createApi({ acceptMarkdownIntake: async () => { throw unexpectedError } }), unexpectedEntries)

    // When: the canonical action fails.
    await expect(codedApi.acceptMarkdownIntake(intakeRequest, signal)).rejects.toBe(codedError)
    await expect(networkApi.acceptMarkdownIntake(intakeRequest, signal)).rejects.toBe(networkError)
    await expect(unexpectedApi.acceptMarkdownIntake(intakeRequest, signal)).rejects.toBe(unexpectedError)

    // Then: diagnostic evidence keeps only stable codes, status, and safe route data.
    expect(firstEntry(codedEntries)).toMatchObject({ action: "accept_markdown_intake", api_method: "POST", api_status: 422, error_code: "ERR_OPERATOR_INPUT", remediation: "retry-operator-action", route: "/v1/tenants/tenant-acme/intake/accept" })
    expect(firstEntry(networkEntries)).toMatchObject({ api_status: 599, error_code: "ERROR_DIAGNOSTIC_OPERATOR_NETWORK", remediation: "retry-operator-action" })
    expect(firstEntry(unexpectedEntries)).toMatchObject({ api_status: 599, error_code: "ERROR_DIAGNOSTIC_OPERATOR_UNEXPECTED", remediation: "retry-operator-action" })
    expect(JSON.stringify([...codedEntries, ...networkEntries, ...unexpectedEntries])).not.toContain(customerMaterial)
  })
})
