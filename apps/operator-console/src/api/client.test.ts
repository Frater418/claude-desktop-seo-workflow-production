import { afterEach, describe, expect, it, vi } from "vitest"
import { createOperatorApiClient } from "./client"
import { OperatorReadModelError, parseArtifacts, parseCurrentRun, parseRun, parseWorkflow } from "./readModels"

afterEach(() => {
  vi.unstubAllGlobals()
})

function json(payload: unknown): Response {
  return new Response(JSON.stringify(payload), { headers: { "Content-Type": "application/json" } })
}

describe("OperatorApiClient read boundary", () => {
  it("rejects a malformed project list instead of projecting guessed project data", async () => {
    const fetch = vi.fn(() => Promise.resolve(json({ data: [{ name: "Ohne Projektkennung" }] })))
    vi.stubGlobal("fetch", fetch)
    const client = createOperatorApiClient({ baseUrl: "", tenantId: "tenant-welle-zwei" })

    await expect(client.listProjects(new AbortController().signal)).rejects.toBeInstanceOf(OperatorReadModelError)
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

  it.each([
    { step_id: "1b", status: "not_due" },
    { step_id: "3b", status: "unknown" },
  ])("rejects malformed workflow sideflow %#", (sideflow) => {
    expect(() => parseWorkflow({ data: { tenant_id: "tenant-welle-zwei", project_id: "projekt-welle-zwei", initial_edges: [], sideflows: [sideflow] } }, "tenant-welle-zwei", "projekt-welle-zwei")).toThrow(OperatorReadModelError)
  })
})
