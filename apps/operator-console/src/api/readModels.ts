import type { ArtifactRecord, CurrentRunResponse, ReviewedIntake } from "../generated/api-types"

type JsonObject = Record<string, unknown>
type CurrentStepId = CurrentRunResponse["step_id"]
export type GateEvidence = Readonly<Record<string, string | number | boolean>>

export type ProjectSummary = { readonly tenantId: string; readonly projectId: string; readonly name: string; readonly customer: string; readonly currentStep: CurrentStepId; readonly progress: string; readonly blockerCount: number; readonly owner: string; readonly nextAction: string }
export type CurrentRun = CurrentRunResponse
export type WorkflowRead = { readonly tenantId: string; readonly projectId: string; readonly initialEdges: readonly WorkflowEdge[]; readonly sideflows: readonly WorkflowSideflow[] }
export type WorkflowEdge = { readonly fromStepId: string; readonly toStepId: string }
export type WorkflowSideflow = { readonly stepId: "3b"; readonly status: "not_due" }
export type RunRead = { readonly tenantId: string; readonly projectId: string; readonly runId: string; readonly stepId: CurrentStepId; readonly revision: number; readonly status: string }
export type StepRead = { readonly tenantId: string; readonly projectId: string; readonly runId: string; readonly stepId: CurrentStepId; readonly status: string; readonly blocker: string; readonly nextAction: string }
export type TaskRead = { readonly tenantId: string; readonly projectId: string; readonly runId: string; readonly stepId: CurrentStepId; readonly taskId: string; readonly title: string; readonly status: string; readonly owner: string; readonly priority: string; readonly deadline: string; readonly resolution: string; readonly dependency: string }
export type GateRead = { readonly tenantId: string; readonly projectId: string; readonly runId: string; readonly stepId: CurrentStepId; readonly qualityGateId: string; readonly qualityGateRunId: string; readonly artifactId: string; readonly artifactHash: string; readonly artifactRevision: number; readonly result: string; readonly summary: string; readonly evidence: GateEvidence; readonly findings: readonly string[]; readonly checkerVersion: string; readonly checkedAt: string }
export type ContextRead = { readonly tenantId: string; readonly projectId: string; readonly runId: string; readonly stepId: CurrentStepId; readonly title: string; readonly finding: string }
export type IntegrationRead = { readonly tenantId: string; readonly projectId: string; readonly name: string; readonly mode: string }
export type ArtifactValidationRead = { readonly result: string; readonly report: string }
export type IntakePreviewRead = { readonly previewHash: string; readonly sourceHash: string; readonly reviewed: ReviewedIntake; readonly title: string | null; readonly tenantId: string | null; readonly projectId: string | null; readonly projectName: string | null; readonly projectV2Present: boolean; readonly missingFields: readonly string[]; readonly eligible: boolean }
export type IntakeAcceptanceRead = { readonly tenantId: string; readonly projectId: string }
export type ReleaseRead = { readonly releaseId: string; readonly tenantId: string; readonly projectId: string; readonly runId: string; readonly stepId: CurrentStepId; readonly gateId: string; readonly artifactId: string; readonly artifactHash: string; readonly artifactRevision: number; readonly approvalId: string; readonly policyVersion: string; readonly releasedAt: string }

export class OperatorReadModelError extends Error {
  public readonly name = "OperatorReadModelError"

  public constructor(message: string) {
    super(message)
  }
}

function fail(message: string): never {
  throw new OperatorReadModelError(`Die lokale Operator-API hat ${message} geliefert.`)
}

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function object(value: unknown, subject: string): JsonObject {
  if (isObject(value)) return value
  return fail(`kein lesbares ${subject}`)
}

function data(value: unknown, subject: string): unknown {
  return object(value, subject)["data"] ?? fail(`kein Datenfeld fuer ${subject}`)
}

function stringAt(value: JsonObject, key: string, subject: string): string {
  const field = value[key]
  if (typeof field === "string" && field !== "") return field
  return fail(`kein lesbares Feld ${key} in ${subject}`)
}

function nullableStringAt(value: JsonObject, key: string, subject: string): string | null {
  const field = value[key]
  if (field === null) return null
  if (typeof field === "string" && field !== "") return field
  return fail(`kein lesbares Feld ${key} in ${subject}`)
}

function nullableObjectAt(value: JsonObject, key: string, subject: string): JsonObject | null {
  const field = value[key]
  if (field === null) return null
  if (isObject(field)) return field
  return fail(`kein lesbares Feld ${key} in ${subject}`)
}

function booleanAt(value: JsonObject, key: string, subject: string): boolean {
  const field = value[key]
  if (typeof field === "boolean") return field
  return fail(`kein lesbares Feld ${key} in ${subject}`)
}

function stringsAt(value: JsonObject, key: string, subject: string): readonly string[] {
  const fields = list(value[key], subject)
  const parsed: string[] = []
  for (const field of fields) {
    if (typeof field !== "string" || field === "") return fail(`keine lesbare Liste ${key} in ${subject}`)
    parsed.push(field)
  }
  return parsed
}

function isGateEvidence(value: JsonObject): value is GateEvidence {
  return Object.values(value).every((entry) => typeof entry === "string" || typeof entry === "number" || typeof entry === "boolean")
}

function sha256At(value: JsonObject, key: string, subject: string): string {
  const hash = stringAt(value, key, subject)
  if (/^[a-f0-9]{64}$/.test(hash)) return hash
  return fail(`kein gueltiges Feld ${key} in ${subject}`)
}

function numberAt(value: JsonObject, key: string, subject: string): number {
  const field = value[key]
  if (typeof field === "number" && Number.isInteger(field) && field >= 0) return field
  return fail(`kein lesbares Feld ${key} in ${subject}`)
}

function positiveIntegerAt(value: JsonObject, key: string, subject: string): number {
  const field = value[key]
  if (typeof field === "number" && Number.isInteger(field) && field >= 1) return field
  return fail(`kein positiver ganzzahliger Wert ${key} in ${subject}`)
}

function list(value: unknown, subject: string): readonly unknown[] {
  if (Array.isArray(value)) return value
  return fail(`keine lesbare Liste fuer ${subject}`)
}

function stepId(value: string, subject: string): CurrentStepId {
  switch (value) {
    case "0": return "0"
    case "1": return "1"
    case "1b": return "1b"
    case "1c": return "1c"
    case "2": return "2"
    case "3": return "3"
    case "4a": return "4a"
    case "4b": return "4b"
    default: return fail(`eine ungueltige Schrittkennung in ${subject}`)
  }
}

function sideflowStepId(value: string): "3b" {
  if (value === "3b") return value
  return fail("eine ungueltige Schrittkennung im Workflow-Nebenlauf")
}

function sideflowStatus(value: string): "not_due" {
  if (value === "not_due") return value
  return fail("einen ungueltigen Status im Workflow-Nebenlauf")
}

function identity(value: JsonObject, subject: string, tenantId: string, projectId: string): { readonly tenantId: string; readonly projectId: string } {
  const recordTenantId = stringAt(value, "tenant_id", subject)
  const recordProjectId = stringAt(value, "project_id", subject)
  if (recordTenantId !== tenantId) return fail(`eine ungueltige Mandantenbindung in ${subject}`)
  if (recordProjectId !== projectId) return fail(`eine ungueltige Projektbindung in ${subject}`)
  return { tenantId: recordTenantId, projectId: recordProjectId }
}

function boundRun(value: JsonObject, subject: string, tenantId: string, projectId: string): { readonly tenantId: string; readonly projectId: string; readonly runId: string; readonly stepId: CurrentStepId } {
  const bound = identity(value, subject, tenantId, projectId)
  return { ...bound, runId: stringAt(value, "run_id", subject), stepId: stepId(stringAt(value, "step_id", subject), subject) }
}

export function parseProjectList(value: unknown, tenantId: string): readonly ProjectSummary[] {
  return list(data(value, "der Projektliste"), "der Projektliste").map((entry) => parseProjectData(entry, tenantId))
}

export function parseProject(value: unknown, tenantId: string, projectId: string): ProjectSummary {
  const parsed = parseProjectData(data(value, "dem Projekt"), tenantId)
  if (parsed.projectId !== projectId) return fail("eine ungueltige Projektbindung im Projekt")
  return parsed
}

function parseProjectData(value: unknown, tenantId: string): ProjectSummary {
  const record = object(value, "Projekt")
  const recordTenantId = stringAt(record, "tenant_id", "Projekt")
  if (recordTenantId !== tenantId) return fail("eine ungueltige Mandantenbindung im Projekt")
  return { tenantId: recordTenantId, projectId: stringAt(record, "project_id", "Projekt"), name: stringAt(record, "name", "Projekt"), customer: stringAt(record, "customer", "Projekt"), currentStep: stepId(stringAt(record, "current_step", "Projekt"), "Projekt"), progress: stringAt(record, "progress", "Projekt"), blockerCount: numberAt(record, "blocker_count", "Projekt"), owner: stringAt(record, "owner", "Projekt"), nextAction: stringAt(record, "next_action", "Projekt") }
}

export function parseCurrentRun(value: unknown, tenantId: string, projectId: string): CurrentRun {
  const record = object(value, "dem aktuellen Lauf")
  const bound = boundRun(record, "dem aktuellen Lauf", tenantId, projectId)
  return { tenant_id: bound.tenantId, project_id: bound.projectId, run_id: bound.runId, step_id: bound.stepId, expected_revision: positiveIntegerAt(record, "expected_revision", "dem aktuellen Lauf") }
}

export function parseRun(value: unknown, tenantId: string, projectId: string, runId: string): RunRead {
  const record = object(data(value, "dem Lauf"), "Lauf")
  const bound = boundRun(record, "dem Lauf", tenantId, projectId)
  if (bound.runId !== runId) return fail("eine ungueltige Laufbindung im Lauf")
  return { ...bound, revision: positiveIntegerAt(record, "revision", "Lauf"), status: stringAt(record, "status", "Lauf") }
}

export function parseWorkflow(value: unknown, tenantId: string, projectId: string): WorkflowRead {
  const record = object(data(value, "dem Workflow"), "Workflow")
  const bound = identity(record, "dem Workflow", tenantId, projectId)
  return { ...bound, initialEdges: list(record["initial_edges"], "Workflow-Kanten").map((entry) => { const edge = object(entry, "Workflow-Kante"); return { fromStepId: stringAt(edge, "from_step_id", "Workflow-Kante"), toStepId: stringAt(edge, "to_step_id", "Workflow-Kante") } }), sideflows: list(record["sideflows"], "Workflow-Nebenlaeufe").map((entry) => { const sideflow = object(entry, "Workflow-Nebenlauf"); return { stepId: sideflowStepId(stringAt(sideflow, "step_id", "Workflow-Nebenlauf")), status: sideflowStatus(stringAt(sideflow, "status", "Workflow-Nebenlauf")) } }) }
}

function parseBoundList<T>(value: unknown, subject: string, tenantId: string, projectId: string, parser: (record: JsonObject, bound: ReturnType<typeof boundRun>) => T): readonly T[] {
  return list(data(value, subject), subject).map((entry) => { const record = object(entry, subject); return parser(record, boundRun(record, subject, tenantId, projectId)) })
}

export function parseSteps(value: unknown, tenantId: string, projectId: string): readonly StepRead[] {
  return parseBoundList(value, "der Schrittliste", tenantId, projectId, (record, bound) => ({ ...bound, status: stringAt(record, "status", "Schritt"), blocker: stringAt(record, "blocker", "Schritt"), nextAction: stringAt(record, "next_action", "Schritt") }))
}

export function parseTasks(value: unknown, tenantId: string, projectId: string): readonly TaskRead[] {
  return parseBoundList(value, "der Aufgabenliste", tenantId, projectId, (record, bound) => ({ ...bound, taskId: stringAt(record, "task_id", "Aufgabe"), title: stringAt(record, "title", "Aufgabe"), status: stringAt(record, "status", "Aufgabe"), owner: stringAt(record, "owner", "Aufgabe"), priority: stringAt(record, "priority", "Aufgabe"), deadline: stringAt(record, "deadline", "Aufgabe"), resolution: stringAt(record, "resolution", "Aufgabe"), dependency: stringAt(record, "dependency", "Aufgabe") }))
}

export function parseArtifacts(value: unknown, tenantId: string, projectId: string): readonly ArtifactRecord[] {
  return parseBoundList(value, "der Artefaktliste", tenantId, projectId, (record) => ({ artifact_id: stringAt(record, "artifact_id", "Artefakt"), content_sha256: stringAt(record, "content_sha256", "Artefakt"), created_at: stringAt(record, "created_at", "Artefakt"), input_hash: stringAt(record, "input_hash", "Artefakt"), project_id: stringAt(record, "project_id", "Artefakt"), revision: positiveIntegerAt(record, "revision", "Artefakt"), run_id: stringAt(record, "run_id", "Artefakt"), step_id: stringAt(record, "step_id", "Artefakt"), storage_key: stringAt(record, "storage_key", "Artefakt"), tenant_id: stringAt(record, "tenant_id", "Artefakt") }))
}

export function parseReleases(value: unknown, tenantId: string, projectId: string): readonly ReleaseRead[] {
  return list(data(value, "der Freigabeliste"), "der Freigabeliste").map((entry) => { const release = object(entry, "Freigabe"); const bound = boundRun(release, "Freigabe", tenantId, projectId); if (stringAt(release, "status", "Freigabe") !== "released") return fail("einen ungueltigen Status in Freigabe"); return { releaseId: stringAt(release, "release_id", "Freigabe"), ...bound, gateId: stringAt(release, "gate_id", "Freigabe"), artifactId: stringAt(release, "artifact_id", "Freigabe"), artifactHash: sha256At(release, "artifact_sha256", "Freigabe"), artifactRevision: positiveIntegerAt(release, "artifact_revision", "Freigabe"), approvalId: stringAt(release, "approval_id", "Freigabe"), policyVersion: stringAt(release, "policy_version", "Freigabe"), releasedAt: stringAt(release, "released_at", "Freigabe") } })
}

export function parseGates(value: unknown, tenantId: string, projectId: string): readonly GateRead[] {
  return parseBoundList(value, "der Pruefliste", tenantId, projectId, (record, bound) => ({ ...bound, qualityGateId: stringAt(record, "quality_gate_id", "Pruefung"), qualityGateRunId: optionalString(record, "quality_gate_run_id"), artifactId: optionalString(record, "artifact_id"), artifactHash: optionalString(record, "artifact_sha256"), artifactRevision: optionalPositiveInteger(record, "artifact_revision"), result: stringAt(record, "result", "Pruefung"), summary: stringAt(record, "summary", "Pruefung"), evidence: optionalEvidence(record), findings: optionalStrings(record, "findings"), checkerVersion: optionalString(record, "checker_version"), checkedAt: optionalString(record, "checked_at") }))
}

function optionalString(value: JsonObject, key: string): string {
  return typeof value[key] === "string" ? value[key] : ""
}

function optionalPositiveInteger(value: JsonObject, key: string): number {
  return typeof value[key] === "number" && Number.isInteger(value[key]) && value[key] > 0 ? value[key] : 0
}

function optionalEvidence(value: JsonObject): GateEvidence {
  return isObject(value["evidence"]) && isGateEvidence(value["evidence"]) ? value["evidence"] : {}
}

function optionalStrings(value: JsonObject, key: string): readonly string[] {
  return Array.isArray(value[key]) && value[key].every((entry) => typeof entry === "string") ? value[key] : []
}

export function parseContext(value: unknown, tenantId: string, projectId: string): readonly ContextRead[] {
  return parseBoundList(value, "der Kontextliste", tenantId, projectId, (record, bound) => ({ ...bound, title: stringAt(record, "title", "Kontext"), finding: stringAt(record, "finding", "Kontext") }))
}

export function parseIntegrations(value: unknown, tenantId: string, projectId: string): readonly IntegrationRead[] {
  return list(data(value, "dem Integrationsstatus"), "dem Integrationsstatus").map((entry) => { const record = object(entry, "Integration"); const bound = identity(record, "der Integration", tenantId, projectId); return { ...bound, name: stringAt(record, "name", "Integration"), mode: stringAt(record, "mode", "Integration") } })
}

export function parseArtifactValidation(value: unknown): ArtifactValidationRead {
  const record = object(data(value, "der Artefaktpruefung"), "Artefaktpruefung")
  return { result: stringAt(record, "result", "Artefaktpruefung"), report: stringAt(record, "report", "Artefaktpruefung") }
}

export function parseIntakePreview(value: unknown): IntakePreviewRead {
  const record = object(data(value, "der Intake-Vorschau"), "Intake-Vorschau")
  const reviewed = object(record["reviewed"], "gepruefte Intake-Vorschau")
  const canonicalReview: ReviewedIntake = { title: nullableStringAt(reviewed, "title", "gepruefte Intake-Vorschau"), tenant_id: nullableStringAt(reviewed, "tenant_id", "gepruefte Intake-Vorschau"), project_id: nullableStringAt(reviewed, "project_id", "gepruefte Intake-Vorschau"), project_name: nullableStringAt(reviewed, "project_name", "gepruefte Intake-Vorschau"), project_v2: nullableObjectAt(reviewed, "project_v2", "gepruefte Intake-Vorschau") }
  return { previewHash: sha256At(record, "preview_hash", "Intake-Vorschau"), sourceHash: sha256At(record, "source_sha256", "Intake-Vorschau"), reviewed: canonicalReview, title: canonicalReview.title ?? null, tenantId: canonicalReview.tenant_id ?? null, projectId: canonicalReview.project_id ?? null, projectName: canonicalReview.project_name ?? null, projectV2Present: canonicalReview.project_v2 !== null, missingFields: stringsAt(record, "missing_fields", "Intake-Vorschau"), eligible: booleanAt(record, "eligible", "Intake-Vorschau") }
}

export function parseIntakeAcceptance(value: unknown, tenantId: string): IntakeAcceptanceRead {
  const record = object(data(value, "der Intake-Annahme"), "Intake-Annahme")
  const acceptedTenantId = stringAt(record, "tenant_id", "Intake-Annahme")
  if (acceptedTenantId !== tenantId) return fail("eine ungueltige Mandantenbindung in der Intake-Annahme")
  return { tenantId: acceptedTenantId, projectId: stringAt(record, "project_id", "Intake-Annahme") }
}

export function validateCurrentEvidence(currentRun: CurrentRun, artifacts: readonly ArtifactRecord[], gates: readonly GateRead[]): void {
  for (const artifact of artifacts) if (artifact.run_id !== currentRun.run_id || artifact.step_id !== currentRun.step_id) fail("eine ungueltige Laufbindung im aktuellen Artefakt")
  for (const gate of gates) if (gate.runId !== currentRun.run_id || gate.stepId !== currentRun.step_id) fail("eine ungueltige Laufbindung in der aktuellen Pruefung")
}

export function selectCanonicalCurrentArtifact(currentRun: CurrentRun, artifacts: readonly ArtifactRecord[]): ArtifactRecord | null {
  const artifactIds = new Set<string>()
  const revisions = new Set<number>()
  let selected: ArtifactRecord | null = null
  for (const artifact of artifacts) {
    if (artifact.tenant_id !== currentRun.tenant_id || artifact.project_id !== currentRun.project_id || artifact.run_id !== currentRun.run_id || artifact.step_id !== currentRun.step_id) continue
    if (artifactIds.has(artifact.artifact_id) || revisions.has(artifact.revision)) return fail("einen mehrdeutigen aktuellen Artefaktstand")
    artifactIds.add(artifact.artifact_id)
    revisions.add(artifact.revision)
    if (selected === null || artifact.revision > selected.revision) selected = artifact
  }
  return selected
}
