import { afterEach, describe, expect, it, vi } from "vitest"
import type { ApiOperationMap, ArtifactCandidateSaveRequest, ArtifactPreflightResponse, ArtifactValidationRequest, GateContext } from "../generated/api-types"
import { createOperatorApiClient, OperatorApiError } from "./client"
import { OperatorReadModelError, parseArtifacts, parseCurrentRun, parseGates, parseIntegrations, parseRun, parseSteps, parseTasks, parseWorkflow } from "./readModels"

afterEach(() => {
  vi.unstubAllGlobals()
})

function json(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), { status, headers: { "Content-Type": "application/json" } })
}

const deliveryTenantId = "tenant-acme"
const deliveryProjectId = "project-acme"
const deliveryHash = "a".repeat(64)

function deliveryPreview() {
  return { scope: "checkpoint", policy_eligible: true, missing_deliverable_ids: [], errors: [], selected_deliverables: [{ artifact_id: "artifact-delivery-0001", content_sha256: deliveryHash, deliverable_id: "strategy", output_path: "packages/strategy.md", release_status: "released", role: "reviewer", step_id: "1" }] }
}

function deliveryResult() {
  return { delivery_export_result_id: "delivery-export-result-abcdefgh", schema_version: "1.0.0", tenant_id: deliveryTenantId, project_id: deliveryProjectId, delivery_export_request_id: "delivery-export-request-abcdefgh", export_id: "delivery-export-abcdefgh", delivery_package_id: "delivery-package-abcdefgh", source_snapshot_revision: 3, replay_state: "created", export_path: "exports/checkpoint.json", zip_path: "exports/checkpoint.zip", package_sha256: deliveryHash, zip_sha256: deliveryHash, zip_size_bytes: 128, delivery_manifest: { manifest_id: "delivery-package-abcdefgh", relative_path: "manifests/delivery.json", content_sha256: deliveryHash }, role_handoff_manifests: [{ manifest_id: "role-handoff-abcdefgh", relative_path: "manifests/copywriter.json", content_sha256: deliveryHash }], notion_import_manifest: { manifest_id: "notion-import-abcdefgh", relative_path: "manifests/notion.json", content_sha256: deliveryHash }, created_at: "2026-08-22T10:00:00Z" }
}

function deliveryRecord() {
  return { delivery_package_id: "delivery-package-abcdefgh", schema_version: "1.0.0", tenant_id: deliveryTenantId, project_id: deliveryProjectId, export_id: "delivery-export-abcdefgh", scope: "checkpoint", source_snapshot_revision: 3, source_records: [{ tenant_id: deliveryTenantId, project_id: deliveryProjectId, source_kind: "artifact", source_record_id: "artifact-delivery-0001", source_revision: 3, source_sha256: deliveryHash }], required_deliverables: [{ deliverable_id: "strategy", source_record_id: "artifact-delivery-0001", source_sha256: deliveryHash, package_path: "packages/strategy.md", release_status: "released" }], missing_deliverables: [], package_paths: ["packages/strategy.md"], package_sha256: deliveryHash, zip_sha256: deliveryHash, role_packages: [{ role: "copywriter", role_handoff_manifest_id: "role-handoff-abcdefgh", manifest_path: "manifests/copywriter.json", manifest_sha256: deliveryHash }], notion_import_manifest: { notion_import_manifest_id: "notion-import-abcdefgh", manifest_path: "manifests/notion.json", manifest_sha256: deliveryHash }, created_at: "2026-08-22T10:00:00Z", package_revision: 2, derived_status: "prepared" }
}

function deliveryRequest(): ApiOperationMap["createDeliveryExport"]["request"] {
  return { delivery_export_result_id: "delivery-export-result-abcdefgh", delivery_package_id: "delivery-package-abcdefgh", export_id: "delivery-export-abcdefgh", package_revision: 2, export_request: { delivery_export_request_id: "delivery-export-request-abcdefgh", schema_version: "1.0.0", tenant_id: deliveryTenantId, project_id: deliveryProjectId, scope: "checkpoint", draft_inclusion_policy: "exclude_drafts", idempotency_key: "idem-abcdefgh", created_at: "2026-08-22T10:00:00Z", source_snapshot_revision: 3, requested_role_packages: ["copywriter"] }, role_package_requests: [{ role: "copywriter", role_handoff_manifest_id: "role-handoff-abcdefgh" }], notion_import_request: { notion_import_manifest_id: "notion-import-abcdefgh", customer_external_id: "customer-acme", implementation_tasks: [{ task_id: "task-abcdefgh", assignment_id: "assignment-abcdefgh", title: "Uebergabe pruefen", status: "not_started", comments: "", source_assignee: "", priority: "high", deadline: "2026-08-30", role: "copywriter", dependencies: [], artifact_relations: [], notion_user_id: null }], publication_registry: { publication_registry_record_id: "publication-registry-acme", urls: ["https://example.com"] } } }
}

function zipResponse(contentDisposition = 'attachment; filename="project-acme-checkpoint-r2.zip"', content = new Uint8Array([80, 75])): Response {
  return new Response(content, { headers: { "Content-Disposition": contentDisposition, ETag: '"etag-delivery"' } })
}

const step4Hash = "b".repeat(64)
const step4ArtifactId = "artifact-step4a-0001"

function step4GateContext(): GateContext {
  return {
    evidence_by_gate: { "GATE-4A-SEO": { content_complete: true, evidence_count: 2 } },
    evidence_documents: [{ classification: "local_validation", evidence_id: "evidence-step4a-0001", report_sha256: step4Hash, source: "operator-console", subject_content_sha256: step4Hash, tool: "step-validation-service" }],
  }
}

function artifactSaveRequest(): ArtifactCandidateSaveRequest {
  return {
    bundle: { execution_identity: { step_id: "4a", revision: 2 } },
    expected_parent_revision: 1,
    gate_context: step4GateContext(),
    idempotency_key: "artifact-save-step4a-0001",
    primary_document: { briefing: "Canonical Step 4A content" },
    run_id: "run-step4a-0001",
    supporting_documents: [{ schema: { type: "FAQPage" } }],
  }
}

function artifactValidationRequest(): ArtifactValidationRequest {
  return {
    bundle: { execution_identity: { step_id: "4a", revision: 2 } },
    content_sha256: step4Hash,
    gate_context: step4GateContext(),
    revision: 2,
    supporting_documents: [{ schema: { type: "FAQPage" } }],
  }
}

function artifactPreflightResponse(): ArtifactPreflightResponse {
  return {
    artifact_id: step4ArtifactId,
    content_sha256: step4Hash,
    derived_views: [{ artifact_id: step4ArtifactId, name: "copywriter-briefing", content: "Briefing content" }],
    quality_gate_runs: [{ quality_gate_run_id: "qgr-4a-seo-aaaaaaaa", quality_gate_id: "GATE-4A-SEO", human_gate_id: "HUMAN-4A", tenant_id: "tenant-step4", run_id: "run-step4a-0001", step_id: "4a", artifact_id: step4ArtifactId, artifact_sha256: step4Hash, artifact_revision: 2, registry_version: "1.0.0", policy_version: "1.0.0", result: "passed", evidence: { content_complete: true, evidence_count: 2 }, findings: [], checked_at: "2026-08-23T10:00:00Z", checker_version: "step-validation-service-1.0.0" }],
    revision: 2,
    step_id: "4a",
    valid: true,
    validation_mode: "step_preflight",
  }
}

describe("OperatorApiClient read boundary", () => {
  it("rejects a malformed project list instead of projecting guessed project data", async () => {
    const fetch = vi.fn(() => Promise.resolve(json({ data: [{ name: "Ohne Projektkennung" }] })))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "", tenantId: "tenant-welle-zwei" })

    await expect(client.listProjects(new AbortController().signal)).rejects.toBeInstanceOf(OperatorReadModelError)
  })

  it("reports a non-JSON HTTP failure as an HTTP error instead of blaming invalid JSON", async () => {
    const fetch = vi.fn(() => Promise.resolve(new Response("Internal Server Error", { status: 500, headers: { "Content-Type": "text/plain" } })))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "", tenantId: "tenant-welle-zwei" })

    await expect(client.listProjects(new AbortController().signal)).rejects.toMatchObject({ kind: "http", status: 500, message: "Die lokale Operator-API ist mit HTTP 500 fehlgeschlagen und hat keine lesbare Fehlerantwort geliefert." })
  })

  it("rejects a current run whose project identity differs from the requested project", async () => {
    const fetch = vi.fn(() => Promise.resolve(json({ tenant_id: "tenant-welle-zwei", project_id: "projekt-fremd", run_id: "lauf-20260821-a", step_id: "1b", expected_revision: 17 })))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "", tenantId: "tenant-welle-zwei" })

    await expect(client.getCurrentRun("projekt-welle-zwei", new AbortController().signal)).rejects.toBeInstanceOf(OperatorReadModelError)
  })

  it("reads canonical releases through the generated release operation", async () => {
    const release = { release_id: "release-welle-zwei", tenant_id: "tenant-welle-zwei", project_id: "projekt-welle-zwei", run_id: "lauf-20260821-a", step_id: "1b", gate_id: "GATE-1B", artifact_id: "artifact-welle-zwei", artifact_sha256: "a".repeat(64), artifact_revision: 17, approval_id: "approval-welle-zwei", policy_version: "1.0.0", status: "released", released_at: "2026-08-21T10:00:00Z" }
    const fetch = vi.fn(() => Promise.resolve(json({ data: [release] })))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "", tenantId: "tenant-welle-zwei" })

    await expect(client.listReleases("projekt-welle-zwei", new AbortController().signal)).resolves.toEqual([{ releaseId: release.release_id, tenantId: release.tenant_id, projectId: release.project_id, runId: release.run_id, stepId: release.step_id, gateId: release.gate_id, artifactId: release.artifact_id, artifactHash: release.artifact_sha256, artifactRevision: release.artifact_revision, approvalId: release.approval_id, policyVersion: release.policy_version, releasedAt: release.released_at }])
    expect(fetch).toHaveBeenCalledWith("/v1/tenants/tenant-welle-zwei/projects/projekt-welle-zwei/releases", expect.any(Object))
  })

  it("rejects malformed canonical releases instead of treating them as empty", async () => {
    const fetch = vi.fn(() => Promise.resolve(json({ data: [{ release_id: "release-welle-zwei" }] })))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "", tenantId: "tenant-welle-zwei" })

    await expect(client.listReleases("projekt-welle-zwei", new AbortController().signal)).rejects.toBeInstanceOf(OperatorReadModelError)
  })

  it.each([0, -1])("rejects current-run expected revision %i", (expectedRevision) => {
    expect(() => parseCurrentRun({ tenant_id: "tenant-welle-zwei", project_id: "projekt-welle-zwei", run_id: "lauf-20260821-a", step_id: "1b", expected_revision: expectedRevision }, "tenant-welle-zwei", "projekt-welle-zwei")).toThrow(OperatorReadModelError)
  })

  it.each([0, -1])("rejects run revision %i", (revision) => {
    expect(() => parseRun({ data: { tenant_id: "tenant-welle-zwei", project_id: "projekt-welle-zwei", run_id: "lauf-20260821-a", step_id: "1b", revision, status: "in_progress" } }, "tenant-welle-zwei", "projekt-welle-zwei", "lauf-20260821-a")).toThrow(OperatorReadModelError)
  })

  it.each([0, -1])("rejects artifact revision %i", (revision) => {
    expect(() => parseArtifacts({ data: [{ tenant_id: "tenant-welle-zwei", project_id: "projekt-welle-zwei", run_id: "lauf-20260821-a", step_id: "1b", artifact_id: "artifact-welle-zwei", revision, content_sha256: "a".repeat(64), input_hash: "b".repeat(64), storage_key: "outputs/themenstruktur.md", created_at: "2026-08-21T10:00:00Z" }] }, "tenant-welle-zwei", "projekt-welle-zwei")).toThrow(OperatorReadModelError)
  })

  it("preserves Step 4 parent artifact lineage from the canonical artifact list", () => {
    const parentArtifactIds = ["artifact-step4-parent-0001", "artifact-step4-parent-0002"]
    const listed = parseArtifacts({ data: [{ tenant_id: "tenant-step4", project_id: "project-step4", run_id: "run-step4a-0001", step_id: "4a", artifact_id: step4ArtifactId, revision: 2, content_sha256: step4Hash, input_hash: "c".repeat(64), storage_key: "outputs/briefing.md", created_at: "2026-08-23T10:00:00Z", parent_artifact_ids: parentArtifactIds }] }, "tenant-step4", "project-step4")

    expect(listed).toMatchObject([{ artifact_id: step4ArtifactId, parent_artifact_ids: parentArtifactIds }])
  })

  it.each([["an empty parent ID", [""]], ["a non-list parent value", "artifact-step4-parent-0001"]])("rejects %s in artifact lineage", (_description, parentArtifactIds) => {
    expect(() => parseArtifacts({ data: [{ tenant_id: "tenant-step4", project_id: "project-step4", run_id: "run-step4a-0001", step_id: "4a", artifact_id: step4ArtifactId, revision: 2, content_sha256: step4Hash, input_hash: "c".repeat(64), storage_key: "outputs/briefing.md", created_at: "2026-08-23T10:00:00Z", parent_artifact_ids: parentArtifactIds }] }, "tenant-step4", "project-step4")).toThrow(OperatorReadModelError)
  })

  it.each([
    { step_id: "1b", status: "not_due" },
    { step_id: "3b", status: "unknown" },
  ])("rejects malformed workflow sideflow %#", (sideflow) => {
    expect(() => parseWorkflow({ data: { tenant_id: "tenant-welle-zwei", project_id: "projekt-welle-zwei", initial_edges: [], sideflows: [sideflow] } }, "tenant-welle-zwei", "projekt-welle-zwei")).toThrow(OperatorReadModelError)
  })

  it("Given unsupported primary status values, when read models are parsed, then the boundary rejects every record", () => {
    const identity = { tenant_id: "tenant-welle-zwei", project_id: "projekt-welle-zwei", run_id: "lauf-20260821-a", step_id: "1b" }

    expect(() => parseRun({ data: { ...identity, revision: 17, status: "unknown" } }, "tenant-welle-zwei", "projekt-welle-zwei", identity.run_id)).toThrow(OperatorReadModelError)
    expect(() => parseSteps({ data: [{ ...identity, status: "unknown", blocker: "Keiner", next_action: "Pruefen" }] }, "tenant-welle-zwei", "projekt-welle-zwei")).toThrow(OperatorReadModelError)
    expect(() => parseGates({ data: [{ ...identity, quality_gate_id: "GATE-1B", result: "unknown", summary: "Unbekannt" }] }, "tenant-welle-zwei", "projekt-welle-zwei")).toThrow(OperatorReadModelError)
    expect(() => parseTasks({ data: [{ ...identity, task_id: "task-1", title: "Pruefen", status: "unknown", owner: "Operator", priority: "high", deadline: "2026-08-25", resolution: "Loesen", dependency: "Keine" }] }, "tenant-welle-zwei", "projekt-welle-zwei")).toThrow(OperatorReadModelError)
    expect(() => parseIntegrations({ data: [{ tenant_id: identity.tenant_id, project_id: identity.project_id, name: "Notion", mode: "unknown" }] }, "tenant-welle-zwei", "projekt-welle-zwei")).toThrow(OperatorReadModelError)
  })
})

describe("OperatorApiClient Step 4 artifact boundary", () => {
  it("preserves generated save and preflight documents on their exact POST routes", async () => {
    const fetch = vi.fn(() => Promise.resolve(json({ data: {} })))
    fetch.mockImplementationOnce(() => Promise.resolve(json({ data: {} })))
    fetch.mockImplementationOnce(() => Promise.resolve(json(artifactPreflightResponse())))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "https://operator.example/", tenantId: "tenant-step4" })
    const signal = new AbortController().signal
    const saveRequest = artifactSaveRequest()
    const validationRequest = artifactValidationRequest()

    await client.saveArtifactRevision("project-step4", saveRequest, signal)
    await client.validateArtifactRevision("project-step4", step4ArtifactId, validationRequest, signal)

    expect(fetch).toHaveBeenNthCalledWith(1, "https://operator.example/v1/tenants/tenant-step4/projects/project-step4/artifacts", expect.objectContaining({ method: "POST", body: JSON.stringify(saveRequest), signal }))
    expect(fetch).toHaveBeenNthCalledWith(2, `https://operator.example/v1/tenants/tenant-step4/projects/project-step4/artifacts/${step4ArtifactId}/validate`, expect.objectContaining({ method: "POST", body: JSON.stringify(validationRequest), signal }))
  })

  it("parses a valid direct artifact preflight response", async () => {
    const fetch = vi.fn(() => Promise.resolve(json(artifactPreflightResponse())))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "", tenantId: "tenant-step4" })

    await expect(client.validateArtifactRevision("project-step4", step4ArtifactId, artifactValidationRequest(), new AbortController().signal)).resolves.toMatchObject({ artifactId: step4ArtifactId, artifactHash: step4Hash, artifactRevision: 2, stepId: "4a", valid: true, validationMode: "step_preflight", derivedViews: [{ artifactId: step4ArtifactId, name: "copywriter-briefing", content: "Briefing content" }], localQualityGateRuns: [{ localQualityGateRunId: "qgr-4a-seo-aaaaaaaa", evidenceSummary: { content_complete: true, evidence_count: 2 } }] })
  })

  it.each([
    ["the obsolete data envelope", { data: { result: "passed", report: "obsolete" } }],
    ["a malformed local quality-gate binding", { ...artifactPreflightResponse(), quality_gate_runs: artifactPreflightResponse().quality_gate_runs.map((run) => ({ ...run, artifact_sha256: "c".repeat(64) })) }],
    ["an unknown direct response field", { ...artifactPreflightResponse(), unexpected: true }],
  ])("rejects %s", async (_description, response) => {
    const fetch = vi.fn(() => Promise.resolve(json(response)))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "", tenantId: "tenant-step4" })

    await expect(client.validateArtifactRevision("project-step4", step4ArtifactId, artifactValidationRequest(), new AbortController().signal)).rejects.toBeInstanceOf(OperatorReadModelError)
  })
})

describe("OperatorApiClient Delivery boundary", () => {
  it("binds all Delivery operations to their generated routes and caller signal", async () => {
    const responses = [json(deliveryPreview()), json(deliveryResult()), json({ data: [deliveryResult()] }), json(deliveryRecord()), zipResponse('attachment; filename*=UTF-8\'\'project-acme-checkpoint-r2.zip')]
    const fetch = vi.fn(() => Promise.resolve(responses.shift() ?? json({})))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "https://operator.example/", tenantId: deliveryTenantId })
    const signal = new AbortController().signal
    const request = deliveryRequest()

    await expect(client.previewDelivery(deliveryProjectId, "checkpoint", signal)).resolves.toMatchObject({ scope: "checkpoint", policyEligible: true })
    await expect(client.createDeliveryExport(deliveryProjectId, request, signal)).resolves.toMatchObject({ exportId: "delivery-export-abcdefgh" })
    await expect(client.listDeliveryExports(deliveryProjectId, signal)).resolves.toHaveLength(1)
    await expect(client.getDeliveryExport(deliveryProjectId, "delivery-export-abcdefgh", signal)).resolves.toMatchObject({ packageRevision: 2 })
    await expect(client.downloadDeliveryExport(deliveryProjectId, "delivery-export-abcdefgh", signal)).resolves.toMatchObject({ filename: "project-acme-checkpoint-r2.zip", etag: '"etag-delivery"' })

    expect(fetch).toHaveBeenNthCalledWith(1, "https://operator.example/v1/tenants/tenant-acme/projects/project-acme/delivery/preview?scope=checkpoint", expect.objectContaining({ method: "GET", signal }))
    expect(fetch).toHaveBeenNthCalledWith(2, "https://operator.example/v1/tenants/tenant-acme/projects/project-acme/delivery/exports", expect.objectContaining({ method: "POST", body: JSON.stringify(request), signal }))
    expect(fetch).toHaveBeenNthCalledWith(3, "https://operator.example/v1/tenants/tenant-acme/projects/project-acme/delivery/exports", expect.objectContaining({ method: "GET", signal }))
    expect(fetch).toHaveBeenNthCalledWith(4, "https://operator.example/v1/tenants/tenant-acme/projects/project-acme/delivery/exports/delivery-export-abcdefgh", expect.objectContaining({ method: "GET", signal }))
    expect(fetch).toHaveBeenNthCalledWith(5, "https://operator.example/v1/tenants/tenant-acme/projects/project-acme/delivery/exports/delivery-export-abcdefgh/download", expect.objectContaining({ method: "GET", signal }))
  })

  it("encodes Delivery route identities", async () => {
    const fetch = vi.fn(() => Promise.resolve(json(deliveryPreview())))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "", tenantId: deliveryTenantId })

    await expect(client.previewDelivery("project-acme/section", "checkpoint", new AbortController().signal)).resolves.toMatchObject({ scope: "checkpoint" })

    expect(fetch).toHaveBeenCalledWith("/v1/tenants/tenant-acme/projects/project-acme%2Fsection/delivery/preview?scope=checkpoint", expect.any(Object))
  })

  it("uses the existing error model for JSON Delivery failures", async () => {
    const fetch = vi.fn(() => Promise.resolve(json({ code: "ERR_DELIVERY_MISSING", message: "Export fehlt." }, 404)))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "", tenantId: deliveryTenantId })

    await expect(client.downloadDeliveryExport(deliveryProjectId, "delivery-export-abcdefgh", new AbortController().signal)).rejects.toMatchObject({ kind: "http", status: 404, message: "Export fehlt." })
  })

  it.each([
    ['attachment; filename="delivery.zip"', "delivery.zip"],
    ["attachment; filename*=UTF-8''delivery%2Darchive.zip", "delivery-archive.zip"],
  ])("accepts a safe ZIP filename from %s", async (contentDisposition, filename) => {
    const fetch = vi.fn(() => Promise.resolve(zipResponse(contentDisposition)))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "", tenantId: deliveryTenantId })

    await expect(client.downloadDeliveryExport(deliveryProjectId, "delivery-export-abcdefgh", new AbortController().signal)).resolves.toMatchObject({ filename })
  })

  it.each([
    ["a missing content disposition", new Response(new Uint8Array([80, 75]), { headers: { ETag: '"etag-delivery"' } })],
    ["a missing ETag", new Response(new Uint8Array([80, 75]), { headers: { "Content-Disposition": 'attachment; filename="delivery.zip"' } })],
    ["an unsafe ZIP filename", zipResponse('attachment; filename="../delivery.zip"')],
    ["an empty ZIP blob", zipResponse('attachment; filename="delivery.zip"', new Uint8Array())],
  ])("rejects %s as an unparseable Delivery download", async (_description, response) => {
    const fetch = vi.fn(() => Promise.resolve(response))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "", tenantId: deliveryTenantId })

    await expect(client.downloadDeliveryExport(deliveryProjectId, "delivery-export-abcdefgh", new AbortController().signal)).rejects.toMatchObject({ kind: "unparseable", status: 200 })
  })

  it("uses the existing error model when the Delivery download cannot reach the API", async () => {
    const fetch = vi.fn(() => Promise.reject(new TypeError("offline")))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "", tenantId: deliveryTenantId })

    await expect(client.downloadDeliveryExport(deliveryProjectId, "delivery-export-abcdefgh", new AbortController().signal)).rejects.toBeInstanceOf(OperatorApiError)
  })
})
