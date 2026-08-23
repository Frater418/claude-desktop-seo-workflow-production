import type { ArtifactPreflightResponse, DerivedView } from "../generated/api-types"
import { booleanAt, exactKeys, fail, list, object, positiveIntegerAt, sha256At, stringAt } from "./deliveryReadModelPrimitives"

type PreflightStepId = ArtifactPreflightResponse["step_id"]
type PreflightValidationMode = NonNullable<ArtifactPreflightResponse["validation_mode"]>
type EvidenceSummary = Readonly<Record<string, string | number | boolean>>

export type ArtifactDerivedViewRead = {
  readonly artifactId: DerivedView["artifact_id"]
  readonly name: DerivedView["name"]
  readonly content: DerivedView["content"]
}

export type LocalQualityGateRunRead = {
  readonly localQualityGateRunId: string
  readonly qualityGateId: string
  readonly result: "passed"
  readonly evidenceSummary: EvidenceSummary
  readonly findings: readonly string[]
}

export type ArtifactPreflightRead = {
  readonly artifactId: ArtifactPreflightResponse["artifact_id"]
  readonly artifactHash: ArtifactPreflightResponse["content_sha256"]
  readonly artifactRevision: ArtifactPreflightResponse["revision"]
  readonly stepId: PreflightStepId
  readonly validationMode: PreflightValidationMode
  readonly valid: true
  readonly derivedViews: readonly ArtifactDerivedViewRead[]
  readonly localQualityGateRuns: readonly LocalQualityGateRunRead[]
  readonly report: string
}

type PreflightIdentity = {
  readonly artifactId: string
  readonly artifactHash: string
  readonly artifactRevision: number
  readonly stepId: PreflightStepId
}

const PREFLIGHT_KEYS = ["artifact_id", "revision", "content_sha256", "step_id", "validation_mode", "valid", "quality_gate_runs", "derived_views"] as const
const DERIVED_VIEW_KEYS = ["artifact_id", "name", "content"] as const
const QUALITY_GATE_RUN_KEYS = ["quality_gate_run_id", "quality_gate_id", "human_gate_id", "tenant_id", "run_id", "step_id", "artifact_id", "artifact_sha256", "artifact_revision", "registry_version", "policy_version", "result", "evidence", "findings", "checked_at", "checker_version"] as const
const ARTIFACT_ID = /^artifact-[a-z0-9][a-z0-9-]{7,63}$/
const DERIVED_VIEW_NAME = /^[a-z0-9][a-z0-9.-]{0,127}$/

function artifactIdAt(value: Readonly<Record<string, unknown>>, key: string, subject: string): string {
  const artifactId = stringAt(value, key, subject)
  if (ARTIFACT_ID.test(artifactId)) return artifactId
  return fail(`keine gueltige Artefaktkennung ${key} in ${subject}`)
}

function stepIdAt(value: Readonly<Record<string, unknown>>, key: string, subject: string): PreflightStepId {
  const stepId = stringAt(value, key, subject)
  if (stepId === "4a" || stepId === "4b") return stepId
  return fail(`keine gueltige Schrittkennung ${key} in ${subject}`)
}

function validationModeAt(value: Readonly<Record<string, unknown>>): PreflightValidationMode {
  const validationMode = stringAt(value, "validation_mode", "der Artefaktvorpruefung")
  if (validationMode === "step_preflight") return validationMode
  return fail("keinen gueltigen Validierungsmodus in der Artefaktvorpruefung")
}

function evidenceSummaryAt(value: Readonly<Record<string, unknown>>): EvidenceSummary {
  const evidence = object(value["evidence"], "der lokalen QGR-Evidenz")
  const summary: Record<string, string | number | boolean> = {}
  for (const [key, entry] of Object.entries(evidence)) {
    if (typeof entry === "string" || typeof entry === "number" || typeof entry === "boolean") summary[key] = entry
    else fail("eine unlesbare lokale QGR-Evidenz")
  }
  return summary
}

function findingsAt(value: Readonly<Record<string, unknown>>): readonly string[] {
  return list(value["findings"], "den lokalen QGR-Findings").map((entry) => {
    if (typeof entry === "string") return entry
    return fail("unlesbare lokale QGR-Findings")
  })
}

function derivedViewAt(value: unknown, identity: PreflightIdentity): ArtifactDerivedViewRead {
  const view = object(value, "der abgeleiteten Ansicht")
  exactKeys(view, DERIVED_VIEW_KEYS, "der abgeleiteten Ansicht")
  const artifactId = artifactIdAt(view, "artifact_id", "der abgeleiteten Ansicht")
  if (artifactId !== identity.artifactId) fail("eine abgeleitete Ansicht mit fremder Artefaktbindung")
  const name = stringAt(view, "name", "der abgeleiteten Ansicht")
  if (!DERIVED_VIEW_NAME.test(name)) fail("einen ungueltigen Namen in der abgeleiteten Ansicht")
  const content = view["content"]
  if (typeof content !== "string") fail("keinen lesbaren Inhalt in der abgeleiteten Ansicht")
  return { artifactId, name, content }
}

function qualityGateRunAt(value: unknown, identity: PreflightIdentity): LocalQualityGateRunRead {
  const run = object(value, "dem lokalen Quality-Gate-Run")
  exactKeys(run, QUALITY_GATE_RUN_KEYS, "dem lokalen Quality-Gate-Run")
  const artifactId = artifactIdAt(run, "artifact_id", "dem lokalen Quality-Gate-Run")
  if (artifactId !== identity.artifactId || sha256At(run, "artifact_sha256", "dem lokalen Quality-Gate-Run") !== identity.artifactHash || positiveIntegerAt(run, "artifact_revision", "dem lokalen Quality-Gate-Run") !== identity.artifactRevision || stepIdAt(run, "step_id", "dem lokalen Quality-Gate-Run") !== identity.stepId) fail("einen lokalen Quality-Gate-Run ohne exakte Artefaktbindung")
  const result = stringAt(run, "result", "dem lokalen Quality-Gate-Run")
  if (result !== "passed") fail("einen nicht bestandenen lokalen Quality-Gate-Run in einer gueltigen Vorpruefung")
  stringAt(run, "human_gate_id", "dem lokalen Quality-Gate-Run")
  stringAt(run, "tenant_id", "dem lokalen Quality-Gate-Run")
  stringAt(run, "run_id", "dem lokalen Quality-Gate-Run")
  stringAt(run, "registry_version", "dem lokalen Quality-Gate-Run")
  stringAt(run, "policy_version", "dem lokalen Quality-Gate-Run")
  stringAt(run, "checked_at", "dem lokalen Quality-Gate-Run")
  stringAt(run, "checker_version", "dem lokalen Quality-Gate-Run")
  return { localQualityGateRunId: stringAt(run, "quality_gate_run_id", "dem lokalen Quality-Gate-Run"), qualityGateId: stringAt(run, "quality_gate_id", "dem lokalen Quality-Gate-Run"), result, evidenceSummary: evidenceSummaryAt(run), findings: findingsAt(run) }
}

export function parseArtifactPreflight(value: unknown): ArtifactPreflightRead {
  const response = object(value, "der Artefaktvorpruefung")
  exactKeys(response, PREFLIGHT_KEYS, "der Artefaktvorpruefung")
  const identity: PreflightIdentity = { artifactId: artifactIdAt(response, "artifact_id", "der Artefaktvorpruefung"), artifactHash: sha256At(response, "content_sha256", "der Artefaktvorpruefung"), artifactRevision: positiveIntegerAt(response, "revision", "der Artefaktvorpruefung"), stepId: stepIdAt(response, "step_id", "der Artefaktvorpruefung") }
  if (booleanAt(response, "valid", "der Artefaktvorpruefung") !== true) fail("keine gueltige Artefaktvorpruefung")
  const derivedViews = list(response["derived_views"], "den abgeleiteten Ansichten").map((entry) => derivedViewAt(entry, identity))
  const localQualityGateRuns = list(response["quality_gate_runs"], "den lokalen Quality-Gate-Runs").map((entry) => qualityGateRunAt(entry, identity))
  return { ...identity, validationMode: validationModeAt(response), valid: true, derivedViews, localQualityGateRuns, report: derivedViews.map((view) => `${view.name}\n${view.content}`).join("\n\n") }
}
