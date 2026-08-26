import { useEffect } from "react"
import { act, renderHook } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"
import { createOperatorApiClient } from "../api/client"
import { OperatorReadModelError } from "../api/readModels"
import { useOperatorWorkspace } from "./useOperatorWorkspace"

const tenantId = "tenant-welle-zwei"
const firstProjectId = "projekt-welle-zwei"
const secondProjectId = "projekt-zwei"

type FixtureOptions = {
  readonly currentRun?: Promise<unknown>
  readonly currentStep?: "1b" | "4a"
  readonly artifacts?: readonly object[]
  readonly gates?: readonly object[]
  readonly artifactRunId?: string
  readonly gateRunId?: string
  readonly stepRunId?: string
  readonly contextRunId?: string
}

afterEach(() => {
  vi.unstubAllGlobals()
})

function json(payload: unknown): Response {
  return new Response(JSON.stringify(payload), { headers: { "Content-Type": "application/json" } })
}

function project(projectId: string): object {
  return { tenant_id: tenantId, project_id: projectId, name: `Pflegedienst ${projectId}`, customer: "Welle Zwei GmbH", current_step: "1b", progress: "3 von 8 Schritten", blocker_count: 1, owner: "Operator Welle Zwei", next_action: "Themenstruktur pruefen" }
}

function artifactRecord(artifactId: string, revision: number): object {
  return { tenant_id: tenantId, project_id: firstProjectId, run_id: `lauf-${firstProjectId}`, step_id: "1b", artifact_id: artifactId, revision, content_sha256: "a".repeat(64), input_hash: "b".repeat(64), storage_key: "outputs/themenstruktur.md", created_at: "2026-08-21T10:00:00Z" }
}

function gateRecord(overrides: Record<string, unknown> = {}): object {
  return {
    quality_gate_run_id: "qgr-domain-contract-0001",
    quality_gate_id: "qg-domain-contract",
    human_gate_id: "GATE-1B",
    tenant_id: tenantId,
    run_id: `lauf-${firstProjectId}`,
    step_id: "1b",
    artifact_id: "artifact-welle-zwei",
    artifact_sha256: "a".repeat(64),
    artifact_revision: 17,
    registry_version: "1.1.0",
    policy_version: "1.1.0",
    result: "passed",
    evidence: { validator_result: "passed" },
    findings: [],
    checked_at: "2026-08-21T10:00:00Z",
    checker_version: "heartweb-step-validation/1.0.0",
    ...overrides,
  }
}

function fixture(options: FixtureOptions = {}): { readonly api: ReturnType<typeof createOperatorApiClient>; readonly calls: readonly string[] } {
  const calls: string[] = []
  const fetch: typeof globalThis.fetch = (input) => {
    const url = input.toString()
    calls.push(url)
    const selectedProjectId = url.includes(`/${secondProjectId}`) ? secondProjectId : firstProjectId
    const runId = `lauf-${selectedProjectId}`
    const current = { tenant_id: tenantId, project_id: selectedProjectId, run_id: runId, step_id: options.currentStep ?? "1b", expected_revision: 17 }
    if (url.endsWith("/readyz")) return Promise.resolve(json({ data: { status: "ready" } }))
    if (url.endsWith("/projects")) return Promise.resolve(json({ data: [project(firstProjectId), project(secondProjectId)] }))
    if (url.endsWith(`/projects/${selectedProjectId}`)) return Promise.resolve(json({ data: project(selectedProjectId) }))
    if (url.endsWith("/runs/current")) return (options.currentRun ?? Promise.resolve(current)).then(json)
    if (url.includes("/runs/")) return Promise.resolve(json({ data: { ...current, revision: 17, status: "in_progress" } }))
    if (url.endsWith("/workflow")) return Promise.resolve(json({ data: { tenant_id: tenantId, project_id: selectedProjectId, initial_edges: [{ from_step_id: "0", to_step_id: "1" }], sideflows: [{ step_id: "3b", status: "not_due" }] } }))
    if (url.endsWith("/steps")) return Promise.resolve(json({ data: [{ ...current, run_id: options.stepRunId ?? runId, status: "in_progress", blocker: "Freigabe fehlt", next_action: "Themenstruktur pruefen" }] }))
    if (url.endsWith("/tasks")) return Promise.resolve(json({ data: [{ ...current, task_id: "aufgabe-welle-zwei", title: "Themenstruktur pruefen", status: "open", owner: "Operator Welle Zwei", priority: "hoch", deadline: "2026-08-25", resolution: "Pillar-Struktur pruefen", dependency: "Freigabe" }] }))
    if (url.endsWith("/artifacts")) return Promise.resolve(json({ data: options.artifacts ?? [{ ...current, run_id: options.artifactRunId ?? runId, artifact_id: "artifact-welle-zwei", revision: 17, content_sha256: "a".repeat(64), input_hash: "b".repeat(64), storage_key: "outputs/themenstruktur.md", created_at: "2026-08-21T10:00:00Z" }] }))
    if (url.endsWith("/gates")) return Promise.resolve(json({ data: options.gates ?? [gateRecord({ run_id: options.gateRunId ?? runId })] }))
    if (url.endsWith("/context-packages")) return Promise.resolve(json({ data: [{ ...current, run_id: options.contextRunId ?? runId, context_package_id: "context-workspace-fixture", target_revision: 17, sources: [{ source_id: "prompt" }, { source_id: "contract" }, { source_id: "project-v2" }] }] }))
    if (url.endsWith("/integrations/status")) return Promise.resolve(json({ data: [{ tenant_id: tenantId, project_id: selectedProjectId, name: "Notion", mode: "simulated" }] }))
    if (url.endsWith("/intake")) return Promise.resolve(json({ data: { tenant_id: tenantId, project_id: selectedProjectId, reviewed: { tenant_id: tenantId, project_id: selectedProjectId, title: "Geprüftes Briefing", project_v2: {} }, accepted_at: "2026-08-21T10:00:00Z", accepted_by: "Raphael Rechberger", markdown: "# Geprüftes Briefing", source_sha256: "c".repeat(64), generation: null } }))
    if (url.endsWith("/releases")) return Promise.resolve(json({ data: [] }))
    return Promise.reject(new Error(`Unexpected request: ${url}`))
  }
  vi.stubGlobal("fetch", fetch)
  return { api: createOperatorApiClient({ baseUrl: "", tenantId }), calls }
}

describe("useOperatorWorkspace", () => {
  it("resolves reload only after a consumer observed committed canonical state", async () => {
    let releaseCurrentRun: (value: unknown) => void = () => undefined
    const currentRun = new Promise<unknown>((resolve) => { releaseCurrentRun = resolve })
    const { api } = fixture({ currentRun })
    const observedStates: string[] = []
    const { result } = renderHook(() => {
      const workspace = useOperatorWorkspace(api)
      useEffect(() => { observedStates.push(workspace.state.kind) }, [workspace.state])
      return workspace
    })

    let resolved = false
    const reload = result.current.selectProject(firstProjectId).then(() => { resolved = true })
    await Promise.resolve()
    expect(resolved).toBe(false)
    releaseCurrentRun({ tenant_id: tenantId, project_id: firstProjectId, run_id: `lauf-${firstProjectId}`, step_id: "1b", expected_revision: 17 })
    await act(async () => { await reload })
    expect(result.current.state.kind).toBe("ready")
    expect(result.current.selectedProjectId).toBe(firstProjectId)
    expect(observedStates[observedStates.length - 1]).toBe("ready")
  })

  it("reloads canonical state for an explicitly selected project", async () => {
    const { api, calls } = fixture()
    const { result } = renderHook(() => useOperatorWorkspace(api))

    await act(async () => { await result.current.selectProject(secondProjectId) })
    expect(result.current.selectedProjectId).toBe(secondProjectId)
    expect(result.current.state.kind).toBe("ready")
    expect(calls.some((url) => url.endsWith(`/projects/${secondProjectId}/runs/current`))).toBe(true)
  })

  it("does not expose a different run as current step or context", async () => {
    const { api } = fixture({ stepRunId: "lauf-fremd", contextRunId: "lauf-fremd" })
    const { result } = renderHook(() => useOperatorWorkspace(api))

    await act(async () => { await result.current.selectProject(firstProjectId) })

    expect(result.current.state).toMatchObject({ kind: "ready", data: { current: { step: null, context: null } } })
  })

  it("keeps historical artifacts without exposing them as current", async () => {
    const { api } = fixture({ artifactRunId: "lauf-fremd" })
    const { result } = renderHook(() => useOperatorWorkspace(api))

    await act(async () => { await result.current.selectProject(firstProjectId) })
    expect(result.current.state).toMatchObject({ kind: "ready", data: { current: { artifact: null } } })
  })

  it("keeps historical gates without exposing them as current", async () => {
    const { api } = fixture({ gateRunId: "lauf-fremd" })
    const { result } = renderHook(() => useOperatorWorkspace(api))

    await act(async () => { await result.current.selectProject(firstProjectId) })
    expect(result.current.state).toMatchObject({ kind: "ready", data: { current: { gate: null } } })
  })

  it("selects the highest canonical artifact revision when artifacts arrive shuffled", async () => {
    const { api } = fixture({ artifacts: [artifactRecord("artifact-low", 16), artifactRecord("artifact-high", 18), artifactRecord("artifact-middle", 17)] })
    const { result } = renderHook(() => useOperatorWorkspace(api))

    await act(async () => { await result.current.selectProject(firstProjectId) })
    expect(result.current.state).toMatchObject({ kind: "ready", data: { current: { artifact: { artifact_id: "artifact-high", revision: 18 } } } })
  })

  it("selects the Step 4 primary artifact bound by the current gate when outputs share a revision", async () => {
    const primaryArtifactId = "artifact-step4-primary"
    const primaryHash = "c".repeat(64)
    const supportingArtifactId = "artifact-step4-supporting"
    const { api } = fixture({
      currentStep: "4a",
      artifacts: [
        { tenant_id: tenantId, project_id: firstProjectId, run_id: `lauf-${firstProjectId}`, step_id: "4a", artifact_id: supportingArtifactId, revision: 17, content_sha256: "d".repeat(64), input_hash: "b".repeat(64), storage_key: "outputs/supporting.md", created_at: "2026-08-21T10:00:00Z" },
        { tenant_id: tenantId, project_id: firstProjectId, run_id: `lauf-${firstProjectId}`, step_id: "4a", artifact_id: primaryArtifactId, revision: 17, content_sha256: primaryHash, input_hash: "b".repeat(64), storage_key: "outputs/primary.md", created_at: "2026-08-21T10:00:00Z" },
      ],
      gates: [gateRecord({ human_gate_id: "GATE-4A", run_id: `lauf-${firstProjectId}`, step_id: "4a", quality_gate_id: "qg-step4a-contract", quality_gate_run_id: "qgr-step4a-contract-0001", artifact_id: primaryArtifactId, artifact_sha256: primaryHash, artifact_revision: 17 })],
    })
    const { result } = renderHook(() => useOperatorWorkspace(api))

    await act(async () => { await result.current.selectProject(firstProjectId) })

    expect(result.current.state).toMatchObject({ kind: "ready", data: { current: { artifact: { artifact_id: primaryArtifactId, revision: 17 } } } })
  })

  it("rejects ambiguous duplicate canonical artifact revisions", async () => {
    const { api } = fixture({ artifacts: [artifactRecord("artifact-first", 17), artifactRecord("artifact-second", 17)] })
    const { result } = renderHook(() => useOperatorWorkspace(api))

    await act(async () => { await expect(result.current.selectProject(firstProjectId)).rejects.toBeInstanceOf(OperatorReadModelError) })
    expect(result.current.state.kind).toBe("error")
  })
})
