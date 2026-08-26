import type { ArtifactRecord, CurrentRunResponse, ReviewedIntake } from "../generated/api-types"
import { parseGateStatus, parseIntegrationMode, parseRunStatus, parseTaskStatus } from "./statusLabels"
import type { GateStatus, IntegrationMode, RunStatus, StepStatus, TaskStatus } from "./statusLabels"

type JsonObject = Record<string, unknown>
type CurrentStepId = CurrentRunResponse["step_id"]
export type GateEvidence = Readonly<Record<string, string | number | boolean>>

export type ProjectSummary = { readonly tenantId: string; readonly projectId: string; readonly name: string; readonly customer: string; readonly currentStep: CurrentStepId; readonly progress: string; readonly blockerCount: number; readonly owner: string; readonly nextAction: string }
export type CurrentRun = CurrentRunResponse
export type WorkflowRead = { readonly tenantId: string; readonly projectId: string; readonly initialEdges: readonly WorkflowEdge[]; readonly sideflows: readonly WorkflowSideflow[] }
export type WorkflowEdge = { readonly fromStepId: string; readonly toStepId: string }
export type WorkflowSideflow = { readonly stepId: "3b"; readonly status: "not_due" }
export type RunRead = { readonly tenantId: string; readonly projectId: string; readonly runId: string; readonly stepId: CurrentStepId; readonly revision: number; readonly status: RunStatus }
export type StepRead = { readonly tenantId: string; readonly projectId: string; readonly runId: string; readonly stepId: CurrentStepId; readonly status: StepStatus; readonly blocker: string; readonly nextAction: string }
export type TaskRead = { readonly tenantId: string; readonly projectId: string; readonly runId: string; readonly stepId: CurrentStepId; readonly taskId: string; readonly title: string; readonly status: TaskStatus; readonly owner: string; readonly priority: string; readonly deadline: string; readonly resolution: string; readonly dependency: string }
export type GateRead = { readonly tenantId: string; readonly projectId: string; readonly runId: string; readonly stepId: CurrentStepId; readonly qualityGateId: string; readonly qualityGateRunId: string; readonly artifactId: string; readonly artifactHash: string; readonly artifactRevision: number; readonly result: GateStatus; readonly summary: string; readonly evidence: GateEvidence; readonly findings: readonly string[]; readonly checkerVersion: string; readonly checkedAt: string }
export type ContextRead = { readonly tenantId: string; readonly projectId: string; readonly runId: string; readonly stepId: CurrentStepId; readonly title: string; readonly finding: string }
export type IntegrationRead = { readonly tenantId: string; readonly projectId: string; readonly name: string; readonly mode: IntegrationMode }
export type IntakeGenerationSummaryRead = { readonly providerRunId: string; readonly modelId: string; readonly outputCharacters: number; readonly validationStages: readonly string[]; readonly normalizations: readonly string[] }
export type IntakePreviewRead = { readonly previewHash: string; readonly sourceHash: string; readonly reviewed: ReviewedIntake; readonly title: string | null; readonly tenantId: string | null; readonly projectId: string | null; readonly projectName: string | null; readonly projectV2Present: boolean; readonly missingFields: readonly string[]; readonly eligible: boolean; readonly generationSummary: IntakeGenerationSummaryRead | null }
export type IntakeAcceptanceRead = { readonly tenantId: string; readonly projectId: string }
export type AcceptedIntakeGenerationRead = { readonly providerRunId: string; readonly modelId: string; readonly promptId: string; readonly promptVersion: string; readonly finishedAt: string }
export type AcceptedIntakeRead = { readonly tenantId: string; readonly projectId: string; readonly title: string; readonly acceptedAt: string; readonly acceptedBy: string; readonly markdown: string; readonly sourceHash: string; readonly projectV2: Readonly<Record<string, unknown>>; readonly generation: AcceptedIntakeGenerationRead | null }
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

function projectScopedRun(value: JsonObject, subject: string, tenantId: string, projectId: string): { readonly tenantId: string; readonly projectId: string; readonly runId: string; readonly stepId: CurrentStepId } {
  const recordTenantId = stringAt(value, "tenant_id", subject)
  if (recordTenantId !== tenantId) return fail(`eine ungueltige Mandantenbindung in ${subject}`)
  const storedProjectId = value["project_id"]
  if (storedProjectId !== undefined && (typeof storedProjectId !== "string" || storedProjectId !== projectId)) return fail(`eine ungueltige Projektbindung in ${subject}`)
  return { tenantId: recordTenantId, projectId, runId: stringAt(value, "run_id", subject), stepId: stepId(stringAt(value, "step_id", subject), subject) }
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
  return { ...bound, revision: positiveIntegerAt(record, "revision", "Lauf"), status: parseRunStatus(stringAt(record, "status", "Lauf")) ?? fail("einen ungueltigen Laufstatus in Lauf") }
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
  return parseBoundList(value, "der Schrittliste", tenantId, projectId, (record, bound) => ({ ...bound, status: parseRunStatus(stringAt(record, "status", "Schritt")) ?? fail("einen ungueltigen Laufstatus in Schritt"), blocker: stringAt(record, "blocker", "Schritt"), nextAction: stringAt(record, "next_action", "Schritt") }))
}

export function parseTasks(value: unknown, tenantId: string, projectId: string): readonly TaskRead[] {
  return parseBoundList(value, "der Aufgabenliste", tenantId, projectId, (record, bound) => ({ ...bound, taskId: stringAt(record, "task_id", "Aufgabe"), title: stringAt(record, "title", "Aufgabe"), status: parseTaskStatus(stringAt(record, "status", "Aufgabe")) ?? fail("einen ungueltigen Aufgabenstatus in Aufgabe"), owner: stringAt(record, "owner", "Aufgabe"), priority: stringAt(record, "priority", "Aufgabe"), deadline: stringAt(record, "deadline", "Aufgabe"), resolution: stringAt(record, "resolution", "Aufgabe"), dependency: stringAt(record, "dependency", "Aufgabe") }))
}

export function parseArtifacts(value: unknown, tenantId: string, projectId: string): readonly ArtifactRecord[] {
  return parseBoundList(value, "der Artefaktliste", tenantId, projectId, (record) => ({ artifact_id: stringAt(record, "artifact_id", "Artefakt"), content_sha256: stringAt(record, "content_sha256", "Artefakt"), created_at: stringAt(record, "created_at", "Artefakt"), input_hash: stringAt(record, "input_hash", "Artefakt"), ...(record["parent_artifact_ids"] === undefined ? {} : { parent_artifact_ids: stringsAt(record, "parent_artifact_ids", "Artefakt") }), project_id: stringAt(record, "project_id", "Artefakt"), revision: positiveIntegerAt(record, "revision", "Artefakt"), run_id: stringAt(record, "run_id", "Artefakt"), step_id: stringAt(record, "step_id", "Artefakt"), storage_key: stringAt(record, "storage_key", "Artefakt"), tenant_id: stringAt(record, "tenant_id", "Artefakt") }))
}

export function parseReleases(value: unknown, tenantId: string, projectId: string): readonly ReleaseRead[] {
  return list(data(value, "der Freigabeliste"), "der Freigabeliste").map((entry) => { const release = object(entry, "Freigabe"); const bound = boundRun(release, "Freigabe", tenantId, projectId); if (stringAt(release, "status", "Freigabe") !== "released") return fail("einen ungueltigen Status in Freigabe"); return { releaseId: stringAt(release, "release_id", "Freigabe"), ...bound, gateId: stringAt(release, "gate_id", "Freigabe"), artifactId: stringAt(release, "artifact_id", "Freigabe"), artifactHash: sha256At(release, "artifact_sha256", "Freigabe"), artifactRevision: positiveIntegerAt(release, "artifact_revision", "Freigabe"), approvalId: stringAt(release, "approval_id", "Freigabe"), policyVersion: stringAt(release, "policy_version", "Freigabe"), releasedAt: stringAt(release, "released_at", "Freigabe") } })
}

export function parseGates(value: unknown, tenantId: string, projectId: string): readonly GateRead[] {
  return list(data(value, "der Pruefliste"), "der Pruefliste").map((entry) => {
    const record = object(entry, "Pruefung")
    const bound = projectScopedRun(record, "der Pruefliste", tenantId, projectId)
    const result = parseGateStatus(stringAt(record, "result", "Pruefung")) ?? fail("einen ungueltigen Pruefstatus in Pruefung")
    const humanGateId = humanGateIdAt(record)
    stringAt(record, "registry_version", "Pruefung")
    stringAt(record, "policy_version", "Pruefung")
    return {
      ...bound,
      qualityGateId: stringAt(record, "quality_gate_id", "Pruefung"),
      qualityGateRunId: stringAt(record, "quality_gate_run_id", "Pruefung"),
      artifactId: stringAt(record, "artifact_id", "Pruefung"),
      artifactHash: sha256At(record, "artifact_sha256", "Pruefung"),
      artifactRevision: positiveIntegerAt(record, "artifact_revision", "Pruefung"),
      result,
      summary: gateSummary(humanGateId, result),
      evidence: gateEvidenceAt(record),
      findings: gateFindingsAt(record),
      checkerVersion: stringAt(record, "checker_version", "Pruefung"),
      checkedAt: stringAt(record, "checked_at", "Pruefung"),
    }
  })
}

function humanGateIdAt(value: JsonObject): string {
  const gateId = stringAt(value, "human_gate_id", "Pruefung")
  if (/^GATE-(0|1|1B|1C|2|3|3B|4A|4B)$/.test(gateId)) return gateId
  return fail("eine ungueltige Human-Gate-Kennung in Pruefung")
}

function gateSummary(humanGateId: string, result: GateStatus): string {
  if (result === "passed") return `Maschinenprüfung für ${humanGateId} bestanden.`
  if (result === "failed") return `Maschinenprüfung für ${humanGateId} fehlgeschlagen.`
  return `Maschinenprüfung für ${humanGateId} blockiert.`
}

function gateEvidenceAt(value: JsonObject): GateEvidence {
  const evidence = object(value["evidence"], "Nachweisen in Pruefung")
  if (Object.keys(evidence).length === 0 || !isGateEvidence(evidence)) return fail("keine lesbaren Nachweise in Pruefung")
  return evidence
}

function gateFindingsAt(value: JsonObject): readonly string[] {
  if (value["findings"] === undefined) return []
  return list(value["findings"], "Feststellungen in Pruefung").map((entry) => {
    const finding = object(entry, "Feststellung in Pruefung")
    const code = stringAt(finding, "code", "Feststellung in Pruefung")
    const severity = stringAt(finding, "severity", "Feststellung in Pruefung")
    if (!/^QG_[A-Z0-9_]+$/.test(code) || !["info", "warning", "error"].includes(severity)) return fail("eine ungueltige Feststellung in Pruefung")
    return stringAt(finding, "message", "Feststellung in Pruefung")
  })
}

function optionalString(value: JsonObject, key: string): string {
  return typeof value[key] === "string" ? value[key] : ""
}

function contextTitle(record: JsonObject, step: CurrentStepId): string {
  const stored = optionalString(record, "title")
  if (stored !== "") return stored
  stringAt(record, "context_package_id", "Kontext")
  return `Kontextpaket für Schritt ${step}`
}

function contextFinding(record: JsonObject): string {
  const stored = optionalString(record, "finding")
  if (stored !== "") return stored
  const sources = list(record["sources"], "den Quellen im Kontext")
  const targetRevision = positiveIntegerAt(record, "target_revision", "Kontext")
  const sourceLabel = sources.length === 1 ? "1 gebundene Quelle" : `${sources.length} gebundene Quellen`
  return `${sourceLabel} für Zielrevision ${targetRevision}.`
}

export function parseContext(value: unknown, tenantId: string, projectId: string): readonly ContextRead[] {
  return parseBoundList(value, "der Kontextliste", tenantId, projectId, (record, bound) => ({ ...bound, title: contextTitle(record, bound.stepId), finding: contextFinding(record) }))
}

export function parseIntegrations(value: unknown, tenantId: string, projectId: string): readonly IntegrationRead[] {
  return list(data(value, "dem Integrationsstatus"), "dem Integrationsstatus").map((entry) => { const record = object(entry, "Integration"); const bound = identity(record, "der Integration", tenantId, projectId); return { ...bound, name: stringAt(record, "name", "Integration"), mode: parseIntegrationMode(stringAt(record, "mode", "Integration")) ?? fail("einen ungueltigen Integrationsmodus in Integration") } })
}

export function parseIntakePreview(value: unknown): IntakePreviewRead {
  const record = object(data(value, "der Intake-Vorschau"), "Intake-Vorschau")
  const reviewed = object(record["reviewed"], "gepruefte Intake-Vorschau")
  const canonicalReview: ReviewedIntake = { title: nullableStringAt(reviewed, "title", "gepruefte Intake-Vorschau"), tenant_id: nullableStringAt(reviewed, "tenant_id", "gepruefte Intake-Vorschau"), project_id: nullableStringAt(reviewed, "project_id", "gepruefte Intake-Vorschau"), project_name: nullableStringAt(reviewed, "project_name", "gepruefte Intake-Vorschau"), project_v2: nullableObjectAt(reviewed, "project_v2", "gepruefte Intake-Vorschau") }
  const summaryValue = record["generation_summary"]
  const generationSummary = summaryValue === null || summaryValue === undefined ? null : (() => {
    const summary = object(summaryValue, "AI-Laufzusammenfassung")
    return { providerRunId: stringAt(summary, "provider_run_id", "AI-Laufzusammenfassung"), modelId: stringAt(summary, "model_id", "AI-Laufzusammenfassung"), outputCharacters: numberAt(summary, "output_characters", "AI-Laufzusammenfassung"), validationStages: stringsAt(summary, "validation_stages", "AI-Laufzusammenfassung"), normalizations: stringsAt(summary, "normalizations", "AI-Laufzusammenfassung") }
  })()
  return { previewHash: sha256At(record, "preview_hash", "Intake-Vorschau"), sourceHash: sha256At(record, "source_sha256", "Intake-Vorschau"), reviewed: canonicalReview, title: canonicalReview.title ?? null, tenantId: canonicalReview.tenant_id ?? null, projectId: canonicalReview.project_id ?? null, projectName: canonicalReview.project_name ?? null, projectV2Present: canonicalReview.project_v2 !== null, missingFields: stringsAt(record, "missing_fields", "Intake-Vorschau"), eligible: booleanAt(record, "eligible", "Intake-Vorschau"), generationSummary }
}

export function parseIntakeAcceptance(value: unknown, tenantId: string): IntakeAcceptanceRead {
  const record = object(data(value, "der Intake-Annahme"), "Intake-Annahme")
  const acceptedTenantId = stringAt(record, "tenant_id", "Intake-Annahme")
  if (acceptedTenantId !== tenantId) return fail("eine ungueltige Mandantenbindung in der Intake-Annahme")
  return { tenantId: acceptedTenantId, projectId: stringAt(record, "project_id", "Intake-Annahme") }
}

export function parseAcceptedIntake(value: unknown, tenantId: string, projectId: string): AcceptedIntakeRead {
  const record = object(data(value, "dem angenommenen Briefing"), "Angenommenes Briefing")
  const bound = identity(record, "dem angenommenen Briefing", tenantId, projectId)
  const reviewed = object(record["reviewed"], "geprueftem Briefing")
  const reviewedTenantId = stringAt(reviewed, "tenant_id", "geprueftem Briefing")
  const reviewedProjectId = stringAt(reviewed, "project_id", "geprueftem Briefing")
  if (reviewedTenantId !== tenantId || reviewedProjectId !== projectId) return fail("eine ungueltige Projektbindung im geprueften Briefing")
  const projectV2 = object(reviewed["project_v2"], "Project V2 im angenommenen Briefing")
  const generationValue = record["generation"]
  const generation = generationValue === null || generationValue === undefined ? null : (() => {
    const generated = object(generationValue, "AI-Laufnachweis")
    return {
      providerRunId: stringAt(generated, "provider_run_id", "AI-Laufnachweis"),
      modelId: stringAt(generated, "model_id", "AI-Laufnachweis"),
      promptId: stringAt(generated, "prompt_id", "AI-Laufnachweis"),
      promptVersion: stringAt(generated, "prompt_version", "AI-Laufnachweis"),
      finishedAt: stringAt(generated, "finished_at", "AI-Laufnachweis"),
    }
  })()
  return {
    ...bound,
    title: stringAt(reviewed, "title", "geprueftem Briefing"),
    acceptedAt: stringAt(record, "accepted_at", "angenommenem Briefing"),
    acceptedBy: stringAt(record, "accepted_by", "angenommenem Briefing"),
    markdown: stringAt(record, "markdown", "angenommenem Briefing"),
    sourceHash: sha256At(record, "source_sha256", "angenommenem Briefing"),
    projectV2,
    generation,
  }
}

export function validateCurrentEvidence(currentRun: CurrentRun, artifacts: readonly ArtifactRecord[], gates: readonly GateRead[]): void {
  for (const artifact of artifacts) if (artifact.run_id === currentRun.run_id && artifact.step_id !== currentRun.step_id) fail("eine ungueltige Schrittbindung im aktuellen Artefakt")
  for (const gate of gates) if (gate.runId === currentRun.run_id && gate.stepId !== currentRun.step_id) fail("eine ungueltige Schrittbindung in der aktuellen Pruefung")
}

export function selectCanonicalCurrentArtifact(currentRun: CurrentRun, artifacts: readonly ArtifactRecord[], gates: readonly GateRead[]): ArtifactRecord | null {
  const artifactIds = new Set<string>()
  const currentArtifacts: ArtifactRecord[] = []
  for (const artifact of artifacts) {
    if (artifact.tenant_id !== currentRun.tenant_id || artifact.project_id !== currentRun.project_id || artifact.run_id !== currentRun.run_id || artifact.step_id !== currentRun.step_id) continue
    if (artifactIds.has(artifact.artifact_id)) return fail("einen mehrdeutigen aktuellen Artefaktstand")
    artifactIds.add(artifact.artifact_id)
    currentArtifacts.push(artifact)
  }
  if (currentArtifacts.length === 0) return null
  const maximumRevision = Math.max(...currentArtifacts.map((artifact) => artifact.revision))
  const currentOutputSet = currentArtifacts.filter((artifact) => artifact.revision === maximumRevision)
  if (currentOutputSet.length === 1) return currentOutputSet[0] ?? fail("einen ungueltigen aktuellen Artefaktstand")
  if (currentOutputSet.length !== 2 || (currentRun.step_id !== "4a" && currentRun.step_id !== "4b")) return fail("einen mehrdeutigen aktuellen Artefaktstand")
  const boundGates = gates.filter((gate) =>
    gate.tenantId === currentRun.tenant_id
    && gate.projectId === currentRun.project_id
    && gate.runId === currentRun.run_id
    && gate.stepId === currentRun.step_id
    && currentOutputSet.some((artifact) => artifact.artifact_id === gate.artifactId && artifact.content_sha256 === gate.artifactHash && artifact.revision === gate.artifactRevision),
  )
  if (boundGates.length !== 1) return fail("eine mehrdeutige aktuelle Pruefbindung")
  const boundGate = boundGates[0] ?? fail("eine ungueltige aktuelle Pruefbindung")
  return currentOutputSet.find((artifact) => artifact.artifact_id === boundGate.artifactId && artifact.content_sha256 === boundGate.artifactHash && artifact.revision === boundGate.artifactRevision) ?? fail("eine ungueltige aktuelle Pruefbindung")
}
