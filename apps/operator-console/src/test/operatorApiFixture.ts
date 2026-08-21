import { vi } from "vitest"

const tenantId = "tenant-welle-zwei"
const projectId = "projekt-welle-zwei"
const secondProjectId = "projekt-beta-welle-zwei"
const acceptedProjectId = "projekt-intake-welle-zwei"
const runId = "lauf-20260821-a"
const stepId = "1b"
const revision = 17
const actionResults = {
  approve: { result: "Freigabe wird als menschliche Entscheidung gespeichert.", previewHash: "approve-preview" },
  reject: { result: "Die Revision wird abgelehnt.", previewHash: "reject-preview" },
  "request-revision": { result: "Eine Revision wird angefordert.", previewHash: "revision-preview" },
  "request-input": { result: "Eine Eingabe wird angefordert.", previewHash: "input-preview" },
  escalate: { result: "Die Entscheidung wird eskaliert.", previewHash: "escalate-preview" },
  "request-waiver": { result: "Die Ausnahmeanfrage wird geprueft.", previewHash: "waiver-preview" },
} as const

type ActionName = keyof typeof actionResults
type FixtureRun = { readonly tenant_id: string; readonly project_id: string; readonly run_id: string; readonly step_id: string; readonly expected_revision: number }

type FixtureState = { readonly calls: string[]; readonly requestBodies: string[] }

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), { headers: { "Content-Type": "application/json" } })
}

function urlOf(input: RequestInfo | URL): string {
  return input instanceof Request ? input.url : input.toString()
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function requestBody(init: RequestInit | undefined): Record<string, unknown> | null {
  if (typeof init?.body !== "string") return null
  try {
    const body: unknown = JSON.parse(init.body)
    return isRecord(body) ? body : null
  } catch {
    return null
  }
}

function actionName(url: string, projectPath: string, suffix: "preview" | "confirm"): ActionName | null {
  const prefix = `${projectPath}/actions/`
  const ending = `/${suffix}`
  if (!url.startsWith(prefix) || !url.endsWith(ending)) return null
  switch (url.slice(prefix.length, -ending.length)) {
    case "approve": return "approve"
    case "reject": return "reject"
    case "request-revision": return "request-revision"
    case "request-input": return "request-input"
    case "escalate": return "escalate"
    case "request-waiver": return "request-waiver"
    default: return null
  }
}

function matchesIntent(body: Record<string, unknown> | null, action: ActionName, run: FixtureRun): boolean {
  return body !== null && body["action"] === action && body["tenant_id"] === run.tenant_id && body["project_id"] === run.project_id && body["run_id"] === run.run_id && body["step_id"] === run.step_id && body["expected_revision"] === run.expected_revision
}

function matchesConfirmation(body: Record<string, unknown> | null, action: ActionName, run: FixtureRun): boolean {
  return body !== null && body["confirmed"] === true && body["preview_hash"] === actionResults[action].previewHash && typeof body["idempotency_key"] === "string" && isRecord(body["intent"]) && matchesIntent(body["intent"], action, run)
}

function isBlockedWaiver(body: Record<string, unknown>): boolean {
  return isRecord(body["payload"]) && body["payload"]["reason"] === "Blockierte Ausnahme"
}

export function createOperatorApiFixture(): { readonly fetch: typeof fetch; readonly state: FixtureState } {
  const state: { calls: string[]; requestBodies: string[] } = { calls: [], requestBodies: [] }
  const project = { tenant_id: tenantId, project_id: projectId, name: "Pflegedienst Alpha", customer: "Alpha Pflege GmbH", current_step: stepId, progress: "3 von 8 Schritten", blocker_count: 1, owner: "Heartweb Admin Operator", next_action: "Informationsarchitektur pruefen" }
  const currentRun = { tenant_id: tenantId, project_id: projectId, run_id: runId, step_id: stepId, expected_revision: revision }
  const secondProject = { tenant_id: tenantId, project_id: secondProjectId, name: "Pflegedienst Beta", customer: "Beta Pflege GmbH", current_step: "2", progress: "4 von 8 Schritten", blocker_count: 0, owner: "Heartweb Admin Operator", next_action: "Cluster pruefen" }
  const secondRun = { tenant_id: tenantId, project_id: secondProjectId, run_id: "lauf-beta-20260821", step_id: "2", expected_revision: 8 }
  const acceptedProject = { tenant_id: tenantId, project_id: acceptedProjectId, name: "Pflegedienst Alpha", customer: "Aufnahme GmbH", current_step: "0", progress: "0 von 8 Schritten", blocker_count: 0, owner: "Heartweb Admin Operator", next_action: "Kickoff starten" }
  const acceptedRun = { tenant_id: tenantId, project_id: acceptedProjectId, run_id: "lauf-intake-20260821", step_id: "0", expected_revision: 1 }
  const previousArtifact = { artifact_id: "artifact-welle-zwei-16", tenant_id: tenantId, project_id: projectId, run_id: runId, step_id: stepId, revision: 16, content_sha256: "d".repeat(64), input_hash: "e".repeat(64), storage_key: "outputs/themenstruktur.md", created_at: "2026-08-20T10:00:00Z" }
  const artifact = { artifact_id: "artifact-welle-zwei", tenant_id: tenantId, project_id: projectId, run_id: runId, step_id: stepId, revision, content_sha256: "a".repeat(64), input_hash: "b".repeat(64), storage_key: "outputs/themenstruktur.md", created_at: "2026-08-21T10:00:00Z", parent_artifact_ids: [previousArtifact.artifact_id] }
  const createdArtifact = { ...artifact, artifact_id: "artifact-welle-zwei-18", content_sha256: "c".repeat(64), parent_artifact_ids: [artifact.artifact_id], revision: 18 }
  let artifactSaved = false
  let intakeAccepted = false
  const handler: typeof fetch = (input, init) => {
    const url = urlOf(input)
    const method = init?.method ?? "GET"
    const acceptedProjectRequested = url.includes(`/projects/${acceptedProjectId}`)
    const secondProjectRequested = url.includes(`/projects/${secondProjectId}`)
    const activeProject = acceptedProjectRequested ? acceptedProject : secondProjectRequested ? secondProject : project
    const activeRun = acceptedProjectRequested ? acceptedRun : secondProjectRequested ? secondRun : currentRun
    const activePreviousArtifact = { ...previousArtifact, project_id: activeProject.project_id, run_id: activeRun.run_id, step_id: activeRun.step_id }
    const activeArtifact = { ...artifact, project_id: activeProject.project_id, run_id: activeRun.run_id, step_id: activeRun.step_id }
    const projectPath = `/v1/tenants/${tenantId}/projects/${activeProject.project_id}`
    state.calls.push(`${method} ${url}`)
    if (typeof init?.body === "string") state.requestBodies.push(init.body)
    if (url.endsWith("/readyz")) return Promise.resolve(jsonResponse({ data: { status: "ready" } }))
    if (url.endsWith("/projects")) return Promise.resolve(jsonResponse({ data: intakeAccepted ? [project, secondProject, acceptedProject] : [project, secondProject] }))
    if (url.endsWith(`/projects/${activeProject.project_id}/runs/current`)) return Promise.resolve(jsonResponse(activeRun))
    if (url.endsWith(`/projects/${activeProject.project_id}/runs/${activeRun.run_id}`)) return Promise.resolve(jsonResponse({ data: { ...activeRun, revision: activeRun.expected_revision, status: "in_progress" } }))
    if (url.endsWith(`/projects/${activeProject.project_id}`)) return Promise.resolve(jsonResponse({ data: activeProject }))
    if (url.endsWith("/workflow")) return Promise.resolve(jsonResponse({ data: { tenant_id: tenantId, project_id: activeProject.project_id, initial_edges: [{ from_step_id: "0", to_step_id: "1" }], sideflows: [{ step_id: "3b", status: "not_due" }] } }))
    if (url.endsWith("/steps")) return Promise.resolve(jsonResponse({ data: [{ ...activeRun, status: "in_progress", blocker: acceptedProjectRequested || secondProjectRequested ? "Keine" : "Freigabe der Themenstruktur fehlt", next_action: acceptedProjectRequested ? "Kickoff starten" : secondProjectRequested ? "Cluster pruefen" : "Informationsarchitektur pruefen" }] }))
    if (url.endsWith("/tasks")) return Promise.resolve(jsonResponse({ data: acceptedProjectRequested ? [] : [{ ...activeRun, task_id: secondProjectRequested ? "aufgabe-beta" : "aufgabe-welle-zwei", title: secondProjectRequested ? "Cluster pruefen" : "Themenstruktur pruefen", status: "offen", owner: "Heartweb Admin Operator", priority: "hoch", deadline: "2026-08-25", resolution: secondProjectRequested ? "Clusterliste pruefen" : "Pillar-Struktur pruefen", dependency: secondProjectRequested ? "Keine" : "Freigabe der Themenstruktur" }] }))
    if (url === `${projectPath}/artifacts/${activeArtifact.artifact_id}/content` && method === "GET") return Promise.resolve(jsonResponse({ artifact: activeArtifact, content_base64: "IyBUaGVtZW5zdHJ1a3R1cg==" }))
    if (url === `${projectPath}/artifacts/${createdArtifact.artifact_id}/validate` && method === "POST") return Promise.resolve(jsonResponse({ data: { result: "passed", report: "Maschinenpruefung bestanden" } }))
    if (url === `${projectPath}/artifacts/${activeArtifact.artifact_id}/validate` && method === "POST") return Promise.resolve(jsonResponse({ data: { result: "passed", report: "Maschinenpruefung bestanden" } }))
    if (url.endsWith("/artifacts") && method === "POST") {
      artifactSaved = true
      return Promise.resolve(jsonResponse({ data: createdArtifact }))
    }
    if (url.endsWith("/artifacts")) return Promise.resolve(jsonResponse({ data: acceptedProjectRequested ? [] : [activePreviousArtifact, activeArtifact] }))
    if (url.endsWith("/releases")) return Promise.resolve(jsonResponse({ data: [] }))
    if (url.endsWith("/artifact-revisions")) return Promise.resolve(jsonResponse({ artifacts: artifactSaved ? [previousArtifact, artifact, createdArtifact] : [previousArtifact, artifact] }))
    if (url.endsWith("/gates")) return Promise.resolve(jsonResponse({ data: acceptedProjectRequested ? [] : [{ ...activeRun, quality_gate_id: "GATE-1B", quality_gate_run_id: "qgr-1b-welle-zwei", artifact_id: activeArtifact.artifact_id, artifact_sha256: activeArtifact.content_sha256, artifact_revision: activeArtifact.revision, result: "passed", summary: "Maschinenpruefung bestanden", evidence: { struktur: "vollstaendig" }, findings: [], checker_version: "step-validation-service-1.0.0", checked_at: "2026-08-21T10:00:00Z" }] }))
    if (url.endsWith("/context-packages")) return Promise.resolve(jsonResponse({ data: acceptedProjectRequested ? [] : [{ ...activeRun, title: "Quellenpaket", finding: secondProjectRequested ? "Clusterquellen vollstaendig" : "Lokale Quellen vollstaendig" }] }))
    if (url.endsWith("/integrations/status")) return Promise.resolve(jsonResponse({ data: [{ tenant_id: tenantId, project_id: activeProject.project_id, name: "Notion", mode: "simuliert" }, { tenant_id: tenantId, project_id: activeProject.project_id, name: "n8n", mode: "simuliert" }] }))
    if (url.endsWith("/intake/preview")) return Promise.resolve(jsonResponse({ data: { preview_hash: "a".repeat(64), source_sha256: "b".repeat(64), reviewed: { tenant_id: tenantId, project_id: acceptedProjectId, project_name: acceptedProject.name, title: "Pflegedienst Alpha", project_v2: { version: 2 } }, missing_fields: [], eligible: true, previewed_at: "2026-08-21T10:00:00Z" } }))
    if (url.endsWith("/intake/accept")) {
      intakeAccepted = true
      return Promise.resolve(jsonResponse({ data: { tenant_id: tenantId, project_id: acceptedProjectId } }))
    }
    if (url.endsWith("/artifact-revisions/compare")) return Promise.resolve(jsonResponse({ left_artifact: artifact, right_artifact: createdArtifact, unified_diff: "+ Neue Themenstruktur" }))
    const body = requestBody(init)
    const previewAction = actionName(url, projectPath, "preview")
    if (method === "POST" && previewAction !== null && matchesIntent(body, previewAction, activeRun)) {
      if (previewAction === "request-waiver" && body !== null && isBlockedWaiver(body)) return Promise.resolve(jsonResponse({ allowed: false, blockers: [{ code: "GATE_OPEN", message: "Die Maschinenpruefung ist noch offen.", remediation: "Pruefung abschliessen und erneut versuchen." }], consequence: {}, intent: { action: previewAction, ...activeRun }, preview_hash: "blocked-preview" }))
      const result = actionResults[previewAction]
      return Promise.resolve(jsonResponse({ allowed: true, blockers: [], consequence: { result: result.result }, intent: { action: previewAction, ...activeRun }, preview_hash: result.previewHash }))
    }
    const confirmAction = actionName(url, projectPath, "confirm")
    if (method === "POST" && confirmAction !== null && matchesConfirmation(body, confirmAction, activeRun)) return Promise.resolve(jsonResponse({ canonical: { decision: confirmAction }, preview_hash: actionResults[confirmAction].previewHash, readback_urls: [projectPath], replay: false }))
    return Promise.reject(new Error(`Unerwartete Testanfrage: ${method} ${url}`))
  }
  return { fetch: vi.fn(handler), state }
}
