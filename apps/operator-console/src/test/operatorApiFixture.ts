import { vi } from "vitest"

const tenantId = "tenant-welle-zwei"
const projectId = "project-welle-zwei"
const secondProjectId = "project-beta-welle-zwei"
const acceptedProjectId = "project-intake-welle-zwei"
const runId = "lauf-20260821-a"
const stepId = "1b"
const revision = 17
const deliveryHash = "f".repeat(64)
const actionResults = {
  approve: { result: "Freigabe wird als menschliche Entscheidung gespeichert.", previewHash: "approve-preview" },
  reject: { result: "Die Revision wird abgelehnt.", previewHash: "reject-preview" },
  "request-revision": { result: "Eine Revision wird angefordert.", previewHash: "revision-preview" },
  "request-input": { result: "Eine Eingabe wird angefordert.", previewHash: "input-preview" },
  escalate: { result: "Die Entscheidung wird eskaliert.", previewHash: "escalate-preview" },
  "request-waiver": { result: "Die Ausnahmeanfrage wird geprueft.", previewHash: "waiver-preview" },
  "submit-for-gate": { result: "Das Ergebnis wird zur fachlichen Pruefung eingereicht.", previewHash: "submit-preview" },
} as const

type ActionName = keyof typeof actionResults
type FixtureRun = { readonly tenant_id: string; readonly project_id: string; readonly run_id: string; readonly step_id: string; readonly expected_revision: number }
type FixtureDeliveryRole = "copywriter" | "developer"
type FixtureDeliveryCreate = { readonly resultId: string; readonly packageId: string; readonly exportId: string; readonly requestId: string; readonly projectId: string; readonly scope: "checkpoint"; readonly sourceSnapshotRevision: number; readonly packageRevision: number; readonly createdAt: string; readonly roles: readonly { readonly role: FixtureDeliveryRole; readonly manifestId: string }[]; readonly notionManifestId: string }
type FixtureState = { readonly calls: readonly string[]; readonly requestBodies: readonly string[]; readonly deliveryCreates: readonly FixtureDeliveryCreate[] }

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
    case "submit-for-gate": return "submit-for-gate"
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

function exactKeys(record: Record<string, unknown>, keys: readonly string[]): boolean {
  return Object.keys(record).length === keys.length && keys.every((key) => key in record)
}

function stringAt(record: Record<string, unknown>, key: string): string | null {
  const value = record[key]
  return typeof value === "string" && value !== "" ? value : null
}

function positiveInteger(value: unknown): number | null {
  return typeof value === "number" && Number.isInteger(value) && value > 0 ? value : null
}

function validIdentifier(value: string | null, prefix: string): value is string {
  return value !== null && value.startsWith(prefix) && /^[a-z][a-z0-9-]{2,127}$/.test(value)
}

function deliveryRole(value: unknown): FixtureDeliveryRole | null {
  switch (value) {
    case "copywriter": return value
    case "developer": return value
    default: return null
  }
}

function deliveryRolePackages(value: unknown): readonly { readonly role: FixtureDeliveryRole; readonly manifestId: string }[] | null {
  if (!Array.isArray(value) || value.length === 0) return null
  const packages: { role: FixtureDeliveryRole; manifestId: string }[] = []
  for (const item of value) {
    if (!isRecord(item) || !exactKeys(item, ["role", "role_handoff_manifest_id"])) return null
    const role = deliveryRole(item["role"])
    const manifestId = stringAt(item, "role_handoff_manifest_id")
    if (role === null || !validIdentifier(manifestId, "role-handoff-")) return null
    packages.push({ role, manifestId })
  }
  return new Set(packages.map((item) => item.role)).size === packages.length ? packages : null
}

function deliveryCreate(body: Record<string, unknown> | null, activeProjectId: string): FixtureDeliveryCreate | null {
  if (body === null || !exactKeys(body, ["delivery_export_result_id", "delivery_package_id", "export_id", "export_request", "package_revision", "role_package_requests", "notion_import_request"]) || !isRecord(body["export_request"]) || !isRecord(body["notion_import_request"])) return null
  const exportRequest = body["export_request"]
  const notionRequest = body["notion_import_request"]
  if (!exactKeys(exportRequest, ["created_at", "delivery_export_request_id", "draft_inclusion_policy", "idempotency_key", "project_id", "requested_role_packages", "schema_version", "scope", "source_snapshot_revision", "tenant_id"]) || !exactKeys(notionRequest, ["customer_external_id", "implementation_tasks", "notion_import_manifest_id", "publication_registry"]) || !isRecord(notionRequest["publication_registry"])) return null
  const resultId = stringAt(body, "delivery_export_result_id")
  const packageId = stringAt(body, "delivery_package_id")
  const exportId = stringAt(body, "export_id")
  const requestId = stringAt(exportRequest, "delivery_export_request_id")
  const createdAt = stringAt(exportRequest, "created_at")
  const sourceSnapshotRevision = positiveInteger(exportRequest["source_snapshot_revision"])
  const packageRevision = positiveInteger(body["package_revision"])
  const roles = deliveryRolePackages(body["role_package_requests"])
  const requestedRoles = exportRequest["requested_role_packages"]
  const notionManifestId = stringAt(notionRequest, "notion_import_manifest_id")
  const registry = notionRequest["publication_registry"]
  if (createdAt === null) return null
  if (!validIdentifier(resultId, "delivery-export-result-") || !validIdentifier(packageId, "delivery-package-") || !validIdentifier(exportId, "delivery-export-") || !validIdentifier(requestId, "delivery-export-request-") || !validIdentifier(notionManifestId, "notion-import-") || sourceSnapshotRevision === null || packageRevision === null || roles === null || !Array.isArray(requestedRoles) || !Array.isArray(notionRequest["implementation_tasks"]) || notionRequest["implementation_tasks"].length === 0 || !exactKeys(registry, ["publication_registry_record_id", "urls"]) || !validIdentifier(stringAt(registry, "publication_registry_record_id"), "publication-registry-") || !Array.isArray(registry["urls"]) || registry["urls"].length === 0) return null
  const normalizedRoles: FixtureDeliveryRole[] = []
  for (const role of requestedRoles) { const parsedRole = deliveryRole(role); if (parsedRole === null) return null; normalizedRoles.push(parsedRole) }
  if (normalizedRoles.length !== roles.length || normalizedRoles.some((role, index) => role !== roles[index]?.role) || new Set(normalizedRoles).size !== normalizedRoles.length || exportRequest["tenant_id"] !== tenantId || exportRequest["project_id"] !== activeProjectId || exportRequest["scope"] !== "checkpoint" || exportRequest["schema_version"] !== "1.0.0" || exportRequest["draft_inclusion_policy"] !== "include_explicit_drafts" || !validIdentifier(stringAt(exportRequest, "idempotency_key"), "idem-") || !/^\d{4}-\d{2}-\d{2}T/.test(createdAt ?? "") || !validIdentifier(stringAt(notionRequest, "customer_external_id"), "customer-")) return null
  return { resultId, packageId, exportId, requestId, projectId: activeProjectId, scope: "checkpoint", sourceSnapshotRevision, packageRevision, createdAt, roles, notionManifestId }
}

function deliveryResult(request: FixtureDeliveryCreate): object {
  return { delivery_export_result_id: request.resultId, schema_version: "1.0.0", tenant_id: tenantId, project_id: request.projectId, delivery_export_request_id: request.requestId, export_id: request.exportId, delivery_package_id: request.packageId, source_snapshot_revision: request.sourceSnapshotRevision, replay_state: "created", export_path: `delivery/${request.exportId}/result.json`, zip_path: `delivery/${request.exportId}/archive.zip`, package_sha256: deliveryHash, zip_sha256: deliveryHash, zip_size_bytes: 2048, delivery_manifest: { manifest_id: request.packageId, relative_path: `delivery/${request.exportId}/manifest.json`, content_sha256: deliveryHash }, role_handoff_manifests: request.roles.map((item) => ({ manifest_id: item.manifestId, relative_path: `delivery/${request.exportId}/${item.role}.json`, content_sha256: deliveryHash })), notion_import_manifest: { manifest_id: request.notionManifestId, relative_path: `delivery/${request.exportId}/notion.json`, content_sha256: deliveryHash }, created_at: request.createdAt }
}

function deliveryRecord(request: FixtureDeliveryCreate): object {
  return { delivery_package_id: request.packageId, schema_version: "1.0.0", tenant_id: tenantId, project_id: request.projectId, export_id: request.exportId, scope: request.scope, source_snapshot_revision: request.sourceSnapshotRevision, source_records: [{ tenant_id: tenantId, project_id: request.projectId, source_kind: "project", source_record_id: request.projectId, source_revision: request.sourceSnapshotRevision, source_sha256: deliveryHash }], required_deliverables: [{ deliverable_id: "strategy", source_record_id: "artifact-welle-zwei", source_sha256: deliveryHash, package_path: `delivery/${request.exportId}/strategy.md`, release_status: "released" }], missing_deliverables: ["developer-handoff"], package_paths: [`delivery/${request.exportId}/strategy.md`, `delivery/${request.exportId}/archive.zip`], package_sha256: deliveryHash, zip_sha256: deliveryHash, role_packages: request.roles.map((item) => ({ role: item.role, role_handoff_manifest_id: item.manifestId, manifest_path: `delivery/${request.exportId}/${item.role}.json`, manifest_sha256: deliveryHash })), notion_import_manifest: { notion_import_manifest_id: request.notionManifestId, manifest_path: `delivery/${request.exportId}/notion.json`, manifest_sha256: deliveryHash }, created_at: request.createdAt, package_revision: request.packageRevision, derived_status: "archived", task_assignment_manifest_path: `delivery/${request.exportId}/tasks.json`, quality_summary: { summary_path: `delivery/${request.exportId}/quality.json`, content_sha256: deliveryHash }, export_manifest_path: `delivery/${request.exportId}/export.json`, checksums_path: `delivery/${request.exportId}/checksums.json` }
}

export function createOperatorApiFixture(): { readonly fetch: typeof fetch; readonly state: FixtureState } {
  const state: { calls: string[]; requestBodies: string[]; deliveryCreates: FixtureDeliveryCreate[] } = { calls: [], requestBodies: [], deliveryCreates: [] }
  const project = { tenant_id: tenantId, project_id: projectId, name: "Pflegedienst Alpha", customer: "Alpha Pflege GmbH", current_step: stepId, progress: "3 von 8 Schritten", blocker_count: 1, owner: "Heartweb Admin Operator", next_action: "Informationsarchitektur pruefen" }
  const currentRun = { tenant_id: tenantId, project_id: projectId, run_id: runId, step_id: stepId, expected_revision: revision }
  const secondProject = { tenant_id: tenantId, project_id: secondProjectId, name: "Pflegedienst Beta", customer: "Beta Pflege GmbH", current_step: "2", progress: "4 von 8 Schritten", blocker_count: 0, owner: "Heartweb Admin Operator", next_action: "Cluster pruefen" }
  const secondRun = { tenant_id: tenantId, project_id: secondProjectId, run_id: "lauf-beta-20260821", step_id: "2", expected_revision: 8 }
  const acceptedProject = { tenant_id: tenantId, project_id: acceptedProjectId, name: "Pflegedienst Alpha", customer: "Aufnahme GmbH", current_step: "0", progress: "0 von 8 Schritten", blocker_count: 0, owner: "Heartweb Admin Operator", next_action: "Kickoff starten" }
  const acceptedRun = { tenant_id: tenantId, project_id: acceptedProjectId, run_id: "lauf-intake-20260821", step_id: "0", expected_revision: 1 }
  const previousArtifact = { artifact_id: "artifact-welle-zwei-16", tenant_id: tenantId, project_id: projectId, run_id: runId, step_id: stepId, revision: 16, content_sha256: "d".repeat(64), input_hash: "e".repeat(64), storage_key: "outputs/themenstruktur.md", created_at: "2026-08-20T10:00:00Z" }
  const artifact = { artifact_id: "artifact-welle-zwei", tenant_id: tenantId, project_id: projectId, run_id: runId, step_id: stepId, revision, content_sha256: "a".repeat(64), input_hash: "b".repeat(64), storage_key: "outputs/themenstruktur.md", created_at: "2026-08-21T10:00:00Z", parent_artifact_ids: [previousArtifact.artifact_id] }
  const createdArtifact = { ...artifact, artifact_id: "artifact-welle-zwei-18", content_sha256: "c".repeat(64), parent_artifact_ids: [artifact.artifact_id], revision: 18 }
  const checkpointPreview = { scope: "checkpoint", policy_eligible: true, missing_deliverable_ids: ["developer-handoff"], errors: [], selected_deliverables: [{ artifact_id: "artifact-strategy-0001", content_sha256: deliveryHash, deliverable_id: "strategy", output_path: "outputs/strategy.md", release_status: "released", role: "copywriter", step_id: "1" }, { artifact_id: "artifact-design-0001", content_sha256: null, deliverable_id: "design", output_path: null, release_status: "draft", role: "developer", step_id: "1c" }] }
  const finalPreview = { ...checkpointPreview, scope: "final", policy_eligible: false, errors: [{ code: "ERR_FINAL_RELEASE", message: "Die finale Uebergabe braucht freigegebene Lieferobjekte." }] }
  const deliveryExports = new Map<string, FixtureDeliveryCreate>()
  let diagnosticTraceIndex = 0
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
    const deliveryPath = `${projectPath}/delivery`
    state.calls.push(`${method} ${url}`)
    if (typeof init?.body === "string") state.requestBodies.push(init.body)
    if (url.endsWith("/readyz")) return Promise.resolve(jsonResponse({ data: { status: "ready" } }))
    if (url.endsWith("/projects")) return Promise.resolve(jsonResponse({ data: intakeAccepted ? [project, secondProject, acceptedProject] : [project, secondProject] }))
    if (url.endsWith(`/projects/${activeProject.project_id}/runs/current`)) return Promise.resolve(jsonResponse(activeRun))
    if (url.endsWith(`/projects/${activeProject.project_id}/runs/${activeRun.run_id}`)) return Promise.resolve(jsonResponse({ data: { ...activeRun, revision: activeRun.expected_revision, status: "in_progress" } }))
    if (url.endsWith(`/projects/${activeProject.project_id}`)) return Promise.resolve(jsonResponse({ data: activeProject }))
    if (url.endsWith("/workflow")) return Promise.resolve(jsonResponse({ data: { tenant_id: tenantId, project_id: activeProject.project_id, initial_edges: [{ from_step_id: "0", to_step_id: "1" }], sideflows: [{ step_id: "3b", status: "not_due" }] } }))
    if (url.endsWith("/steps")) return Promise.resolve(jsonResponse({ data: [{ ...activeRun, status: "in_progress", blocker: acceptedProjectRequested || secondProjectRequested ? "Keine" : "Freigabe der Themenstruktur fehlt", next_action: acceptedProjectRequested ? "Kickoff starten" : secondProjectRequested ? "Cluster pruefen" : "Informationsarchitektur pruefen" }] }))
    if (url.endsWith("/tasks")) return Promise.resolve(jsonResponse({ data: acceptedProjectRequested ? [] : [{ ...activeRun, task_id: secondProjectRequested ? "aufgabe-beta" : "aufgabe-welle-zwei", title: secondProjectRequested ? "Cluster pruefen" : "Themenstruktur pruefen", status: "open", owner: "Heartweb Admin Operator", priority: "hoch", deadline: "2026-08-25", resolution: secondProjectRequested ? "Clusterliste pruefen" : "Pillar-Struktur pruefen", dependency: secondProjectRequested ? "Keine" : "Freigabe der Themenstruktur" }] }))
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
    if (url.endsWith("/gates")) return Promise.resolve(jsonResponse({ data: acceptedProjectRequested ? [] : [{ tenant_id: tenantId, run_id: activeRun.run_id, step_id: activeRun.step_id, quality_gate_id: "qg-step1b-contract", quality_gate_run_id: "qgr-1b-welle-zwei", human_gate_id: "GATE-1B", artifact_id: activeArtifact.artifact_id, artifact_sha256: activeArtifact.content_sha256, artifact_revision: activeArtifact.revision, registry_version: "1.1.0", policy_version: "1.1.0", result: "passed", evidence: { validator_result: "passed" }, findings: [{ code: "QG_STEP1B_VALID", severity: "info", message: "Die Seitenarchitektur erfüllt den Vertrag." }], checker_version: "step-validation-service-1.0.0", checked_at: "2026-08-21T10:00:00Z" }] }))
    if (url.endsWith("/context-packages")) return Promise.resolve(jsonResponse({ data: acceptedProjectRequested ? [] : [{ tenant_id: tenantId, project_id: activeProject.project_id, run_id: activeRun.run_id, step_id: activeRun.step_id, context_package_id: `context-${activeProject.project_id}`, target_revision: activeRun.expected_revision, sources: [{ source_id: "official-prompt" }, { source_id: "output-contract" }, { source_id: "project-v2" }] }] }))
    if (url.endsWith("/integrations/status")) return Promise.resolve(jsonResponse({ data: [{ tenant_id: tenantId, project_id: activeProject.project_id, name: "Notion", mode: "simulated" }, { tenant_id: tenantId, project_id: activeProject.project_id, name: "n8n", mode: "simulated" }] }))
    if (method === "GET" && url.endsWith("/intake")) return Promise.resolve(jsonResponse({ data: { tenant_id: tenantId, project_id: activeProject.project_id, reviewed: { title: activeProject.name, tenant_id: tenantId, project_id: activeProject.project_id, project_name: activeProject.name, project_v2: {} }, accepted_at: "2026-08-21T10:00:00Z", accepted_by: "Heartweb Admin Operator", markdown: `# ${activeProject.name}`, source_sha256: "c".repeat(64), generation: null } }))
    if (url.endsWith("/intake/preview")) return Promise.resolve(jsonResponse({ data: { preview_hash: "a".repeat(64), source_sha256: "b".repeat(64), reviewed: { tenant_id: tenantId, project_id: acceptedProjectId, project_name: acceptedProject.name, title: "Pflegedienst Alpha", project_v2: { version: 2 } }, missing_fields: [], eligible: true, previewed_at: "2026-08-21T10:00:00Z" } }))
    if (url.endsWith("/intake/accept")) {
      intakeAccepted = true
      return Promise.resolve(jsonResponse({ data: { tenant_id: tenantId, project_id: acceptedProjectId } }))
    }
    if (url.endsWith("/artifact-revisions/compare")) return Promise.resolve(jsonResponse({ left_artifact: artifact, right_artifact: createdArtifact, unified_diff: "+ Neue Themenstruktur" }))
    if (method === "GET" && url === `${deliveryPath}/preview?scope=checkpoint`) return Promise.resolve(jsonResponse(checkpointPreview))
    if (method === "GET" && url === `${deliveryPath}/preview?scope=final`) return Promise.resolve(jsonResponse(finalPreview))
    if (method === "GET" && url === `${deliveryPath}/exports`) return Promise.resolve(jsonResponse({ data: [...deliveryExports.values()].map(deliveryResult) }))
    const body = requestBody(init)
    if (method === "POST" && url.endsWith("/diagnostic-traces") && body !== null) {
      diagnosticTraceIndex += 1
      return Promise.resolve(jsonResponse({ tenant_id: body["tenant_id"], project_id: body["project_id"], run_id: body["run_id"], scenario_id: body["scenario_id"], source: body["source"], created_at: body["created_at"], trace_id: `trace-${String(diagnosticTraceIndex).padStart(32, "0")}`, status: "active", replay: false }))
    }
    const entryTrace = /\/diagnostic-traces\/(trace-[a-f0-9]{32})\/entries$/.exec(url)?.[1]
    if (method === "POST" && entryTrace !== undefined && body !== null) return Promise.resolve(jsonResponse({ trace_id: entryTrace, operation_id: body["operation_id"], sequence: 1, replay: false }))
    const closeTrace = /\/diagnostic-traces\/(trace-[a-f0-9]{32})\/close$/.exec(url)?.[1]
    if (method === "POST" && closeTrace !== undefined && body !== null) return Promise.resolve(jsonResponse({ trace_id: closeTrace, close_id: body["close_id"], closed_at: body["closed_at"], status: "closed", replay: false, last_successful_operation_id: null, first_failing_operation_id: null }))
    const createdDelivery = deliveryCreate(body, activeProject.project_id)
    if (method === "POST" && url === `${deliveryPath}/exports` && createdDelivery !== null) {
      deliveryExports.set(createdDelivery.exportId, createdDelivery)
      state.deliveryCreates.push(createdDelivery)
      return Promise.resolve(jsonResponse(deliveryResult(createdDelivery)))
    }
    const storedDelivery = [...deliveryExports.values()].find((item) => url === `${deliveryPath}/exports/${item.exportId}`)
    if (method === "GET" && storedDelivery !== undefined) return Promise.resolve(jsonResponse(deliveryRecord(storedDelivery)))
    const downloadDelivery = [...deliveryExports.values()].find((item) => url === `${deliveryPath}/exports/${item.exportId}/download`)
    if (method === "GET" && downloadDelivery !== undefined) return Promise.resolve(new Response(new Blob(["fixture-zip"]), { headers: { "Content-Disposition": `attachment; filename="${downloadDelivery.exportId}.zip"`, ETag: "delivery-fixture-etag" } }))
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
