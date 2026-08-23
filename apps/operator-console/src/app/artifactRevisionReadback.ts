import type { ArtifactRecord, DataEnvelope } from "../generated/api-types"
import type { CurrentRun, ReleaseRead } from "../api/readModels"

export class ArtifactRevisionError extends Error {
  public readonly name = "ArtifactRevisionError"

  public constructor(message: string) { super(message) }
}

type OutputSet = { readonly primary: ArtifactRecord; readonly supporting: ArtifactRecord }
const recordKeys = ["artifact_id", "content_sha256", "contract_version", "created_at", "input_hash", "parent_artifact_ids", "producer_version", "project_id", "revision", "run_id", "step_id", "storage_key", "tenant_id"] as const

export function messageFor(error: unknown): string { return error instanceof Error ? error.message : "Die Artefaktrevision konnte nicht verarbeitet werden." }
export function isStep4(stepId: string): stepId is "4a" | "4b" { return stepId === "4a" || stepId === "4b" }
export function matchesCurrentRun(artifact: ArtifactRecord, currentRun: CurrentRun): boolean { return artifact.tenant_id === currentRun.tenant_id && artifact.project_id === currentRun.project_id && artifact.run_id === currentRun.run_id && artifact.step_id === currentRun.step_id }
export function sameParents(left: ArtifactRecord, right: ArtifactRecord): boolean {
  const leftParents = left.parent_artifact_ids ?? []
  const rightParents = right.parent_artifact_ids ?? []
  return leftParents.length === rightParents.length && leftParents.every((parent, index) => parent === rightParents[index])
}
export function assertCurrentRevisions(revisions: readonly ArtifactRecord[], currentRun: CurrentRun): void {
  if (revisions.some((artifact) => !matchesCurrentRun(artifact, currentRun))) throw new ArtifactRevisionError("Die Revisionsliste enthaelt ein Artefakt aus einem anderen Lauf.")
}
export function releasedArtifacts(releases: readonly ReleaseRead[], currentRun: CurrentRun): readonly string[] {
  return releases.filter((release) => release.tenantId === currentRun.tenant_id && release.projectId === currentRun.project_id && release.runId === currentRun.run_id && release.stepId === currentRun.step_id).map((release) => release.artifactId)
}
export function primaryLineage(revisions: readonly ArtifactRecord[], source: ArtifactRecord, savedPrimary: ArtifactRecord | null): readonly ArtifactRecord[] {
  const byId = new Map(revisions.map((artifact) => [artifact.artifact_id, artifact]))
  const ids = new Set<string>([source.artifact_id])
  let current = source
  while (current.parent_artifact_ids?.length === 1) {
    const parentId = current.parent_artifact_ids[0]
    if (parentId === undefined) break
    const parent = byId.get(parentId)
    if (parent === undefined || ids.has(parent.artifact_id)) break
    ids.add(parent.artifact_id)
    current = parent
  }
  if (savedPrimary !== null) ids.add(savedPrimary.artifact_id)
  return revisions.filter((artifact) => ids.has(artifact.artifact_id)).sort((left, right) => left.revision - right.revision || left.artifact_id.localeCompare(right.artifact_id))
}
export function supportingSibling(revisions: readonly ArtifactRecord[], primary: ArtifactRecord): ArtifactRecord {
  const siblings = revisions.filter((artifact) => artifact.artifact_id !== primary.artifact_id && artifact.revision === primary.revision && sameParents(artifact, primary))
  if (siblings.length !== 1 || siblings[0] === undefined) throw new ArtifactRevisionError("Zur ausgewaehlten Primaerrevision fehlt genau ein unterstuetzendes Dokument.")
  return siblings[0]
}
function isRecord(value: unknown): value is Record<string, unknown> { return typeof value === "object" && value !== null && !Array.isArray(value) }
function object(value: unknown): Record<string, unknown> { if (isRecord(value)) return value; throw new ArtifactRevisionError("Die kanonische Speicherantwort ist nicht lesbar.") }
function stringAt(value: Record<string, unknown>, key: string): string { const entry = value[key]; if (typeof entry === "string" && entry !== "") return entry; throw new ArtifactRevisionError("Die kanonische Speicherantwort ist unvollstaendig.") }
function record(value: unknown): ArtifactRecord {
  const parsed = object(value)
  if (Object.keys(parsed).some((key) => !recordKeys.some((allowed) => allowed === key))) throw new ArtifactRevisionError("Die kanonische Speicherantwort enthaelt unbekannte Artefaktfelder.")
  const revision = parsed["revision"]
  if (typeof revision !== "number" || !Number.isInteger(revision) || revision < 1) throw new ArtifactRevisionError("Die kanonische Speicherantwort ist unvollstaendig.")
  const parents = parsed["parent_artifact_ids"]
  const parentArtifactIds = Array.isArray(parents) ? parents.map((parent) => {
    if (typeof parent === "string" && parent !== "") return parent
    throw new ArtifactRevisionError("Die kanonische Speicherantwort enthaelt keine lesbare Elternlinie.")
  }) : undefined
  if (parents !== undefined && parentArtifactIds === undefined) throw new ArtifactRevisionError("Die kanonische Speicherantwort enthaelt keine lesbare Elternlinie.")
  return { artifact_id: stringAt(parsed, "artifact_id"), content_sha256: stringAt(parsed, "content_sha256"), created_at: stringAt(parsed, "created_at"), input_hash: stringAt(parsed, "input_hash"), project_id: stringAt(parsed, "project_id"), revision, run_id: stringAt(parsed, "run_id"), step_id: stringAt(parsed, "step_id"), storage_key: stringAt(parsed, "storage_key"), tenant_id: stringAt(parsed, "tenant_id"), ...(parentArtifactIds === undefined ? {} : { parent_artifact_ids: parentArtifactIds }) }
}
export function savedOutputSet(response: DataEnvelope): OutputSet {
  const data = object(response.data)
  if (Object.keys(data).length !== 1 || !("records" in data) || !Array.isArray(data["records"]) || data["records"].length !== 2) throw new ArtifactRevisionError("Die kanonische Speicherantwort hat kein geschlossenes Output-Set.")
  const primary = record(data["records"][0])
  const supporting = record(data["records"][1])
  return { primary, supporting }
}
function sameIdentity(left: ArtifactRecord, right: ArtifactRecord): boolean { return left.artifact_id === right.artifact_id && left.content_sha256 === right.content_sha256 && left.revision === right.revision }
export function verifiedOutputSet(saved: OutputSet, revisions: readonly ArtifactRecord[], parent: ArtifactRecord, currentRun: CurrentRun): OutputSet {
  const primary = revisions.find((artifact) => artifact.artifact_id === saved.primary.artifact_id)
  const supporting = revisions.find((artifact) => artifact.artifact_id === saved.supporting.artifact_id)
  if (primary === undefined || supporting === undefined) throw new ArtifactRevisionError("Das gespeicherte Output-Set fehlt im kanonischen Readback.")
  if (!matchesCurrentRun(primary, currentRun) || !matchesCurrentRun(supporting, currentRun) || !sameIdentity(primary, saved.primary) || !sameIdentity(supporting, saved.supporting)) throw new ArtifactRevisionError("Das gespeicherte Output-Set stimmt nicht mit dem kanonischen Readback ueberein.")
  if (primary.parent_artifact_ids?.includes(parent.artifact_id) !== true || primary.revision <= parent.revision || !sameParents(primary, supporting) || primary.revision !== supporting.revision || primary.artifact_id === supporting.artifact_id) throw new ArtifactRevisionError("Das gespeicherte Output-Set hat keine gueltige Primaer- und Nebenlinie.")
  return { primary, supporting }
}
