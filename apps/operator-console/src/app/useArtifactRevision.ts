import { useCallback, useEffect, useMemo, useState } from "react"
import type { ArtifactRecord, ArtifactRevisionListResponse } from "../generated/api-types"
import type { OperatorApiClient } from "../api/client"
import type { CurrentRun, ReleaseRead } from "../api/readModels"

export const releasedArtifactRemediation = "Freigegebene Artefakte sind unveraenderlich. Starten Sie einen neuen Lauf statt dieses Artefakt zu bearbeiten."

export type ArtifactRevisionApi = Pick<OperatorApiClient, "compareArtifactRevisions" | "getArtifactContent" | "listArtifactRevisions" | "listReleases" | "saveArtifactRevision" | "validateArtifactRevision">

export type ArtifactRevisionData = {
  readonly projectId: string
  readonly currentRun: CurrentRun
  readonly current: { readonly artifact: ArtifactRecord | null }
}

type PendingState = "idle" | "loading" | "saving" | "readback"

class ArtifactRevisionError extends Error {
  public readonly name = "ArtifactRevisionError"

  public constructor(message: string) {
    super(message)
  }
}

function messageFor(error: unknown): string {
  return error instanceof Error ? error.message : "Die Artefaktrevision konnte nicht verarbeitet werden."
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function savedArtifact(response: { readonly data: unknown }): ArtifactRecord {
  if (!isRecord(response.data)) throw new ArtifactRevisionError("Die kanonische Speicherantwort ist nicht lesbar.")
  const value = response.data
  const stringValue = (field: string): string => {
    const fieldValue = value[field]
    if (typeof fieldValue === "string" && fieldValue !== "") return fieldValue
    throw new ArtifactRevisionError("Die kanonische Speicherantwort ist unvollstaendig.")
  }
  const revision = value["revision"]
  if (typeof revision !== "number" || !Number.isInteger(revision) || revision < 1) throw new ArtifactRevisionError("Die kanonische Speicherantwort ist unvollstaendig.")
  const parents = value["parent_artifact_ids"]
  const parentArtifactIds = Array.isArray(parents) ? parents.filter((parent): parent is string => typeof parent === "string" && parent !== "") : undefined
  if (parents !== undefined && (!Array.isArray(parents) || parentArtifactIds === undefined || parentArtifactIds.length !== parents.length)) throw new ArtifactRevisionError("Die kanonische Speicherantwort enthaelt keine lesbare Elternlinie.")
  return { artifact_id: stringValue("artifact_id"), content_sha256: stringValue("content_sha256"), created_at: stringValue("created_at"), input_hash: stringValue("input_hash"), project_id: stringValue("project_id"), revision, run_id: stringValue("run_id"), step_id: stringValue("step_id"), storage_key: stringValue("storage_key"), tenant_id: stringValue("tenant_id"), ...(parentArtifactIds === undefined ? {} : { parent_artifact_ids: parentArtifactIds }) }
}

function matchesCurrentRun(artifact: ArtifactRecord, currentRun: CurrentRun): boolean {
  return artifact.tenant_id === currentRun.tenant_id && artifact.project_id === currentRun.project_id && artifact.run_id === currentRun.run_id && artifact.step_id === currentRun.step_id
}

function assertCurrentRevisions(revisions: ArtifactRevisionListResponse, currentRun: CurrentRun): void {
  if (revisions.artifacts.some((artifact) => !matchesCurrentRun(artifact, currentRun))) throw new ArtifactRevisionError("Die Revisionsliste enthaelt ein Artefakt aus einem anderen Lauf.")
}

function releasedArtifacts(releases: readonly ReleaseRead[], currentRun: CurrentRun): readonly string[] {
  return releases.filter((release) => release.tenantId === currentRun.tenant_id && release.projectId === currentRun.project_id && release.runId === currentRun.run_id && release.stepId === currentRun.step_id).map((release) => release.artifactId)
}

function verifyReadback(saved: ArtifactRecord, readback: ArtifactRecord, parent: ArtifactRecord, currentRun: CurrentRun): void {
  if (!matchesCurrentRun(saved, currentRun) || !matchesCurrentRun(readback, currentRun)) throw new ArtifactRevisionError("Die gespeicherte Artefaktrevision ist nicht an den aktuellen Lauf gebunden.")
  if (readback.revision !== saved.revision || readback.content_sha256 !== saved.content_sha256) throw new ArtifactRevisionError("Die gespeicherte Artefaktrevision stimmt nicht mit dem kanonischen Readback ueberein.")
  if (readback.parent_artifact_ids?.includes(parent.artifact_id) !== true || readback.revision <= parent.revision) throw new ArtifactRevisionError("Die gespeicherte Artefaktrevision hat keine gueltige Elternlinie.")
}

export function useArtifactRevision({ api, data }: { readonly api: ArtifactRevisionApi; readonly data: ArtifactRevisionData }): {
  readonly content: string
  readonly canLoadContent: boolean
  readonly comparisonArtifact: ArtifactRecord | null
  readonly diff: string
  readonly error: string | null
  readonly isEditingLocked: boolean
  readonly isReleased: boolean
  readonly isSaving: boolean
  readonly isReadbackPending: boolean
  readonly newArtifact: ArtifactRecord | null
  readonly parentArtifact: ArtifactRecord | null
  readonly revisions: readonly ArtifactRecord[]
  readonly validation: string
  readonly compare: () => Promise<void>
  readonly loadContent: () => Promise<void>
  readonly save: () => Promise<void>
  readonly setContent: (content: string) => void
  readonly setNewArtifactId: (artifactId: string) => void
  readonly setParentArtifactId: (artifactId: string) => void
  readonly validate: () => Promise<void>
} {
  const [revisions, setRevisions] = useState<readonly ArtifactRecord[]>([])
  const [parentArtifactId, setParentArtifactId] = useState(data.current.artifact?.artifact_id ?? "")
  const [newArtifactId, setNewArtifactId] = useState("")
  const [content, setContent] = useState("")
  const [newArtifact, setNewArtifact] = useState<ArtifactRecord | null>(null)
  const [releasedIds, setReleasedIds] = useState<readonly string[]>([])
  const [pending, setPending] = useState<PendingState>("loading")
  const [error, setError] = useState<string | null>(null)
  const [diff, setDiff] = useState("")
  const [validation, setValidation] = useState("")
  const sourceArtifact = data.current.artifact
  const parentArtifact = useMemo(() => revisions.find((artifact) => artifact.artifact_id === parentArtifactId) ?? null, [parentArtifactId, revisions])
  const comparisonArtifact = useMemo(() => revisions.find((artifact) => artifact.artifact_id === newArtifactId) ?? null, [newArtifactId, revisions])
  const isReleased = parentArtifact !== null && releasedIds.includes(parentArtifact.artifact_id)
  const contentArtifact = parentArtifact ?? sourceArtifact
  const canLoadContent = contentArtifact !== null && !isReleased
  const isEditingLocked = parentArtifact === null || isReleased || pending !== "idle"

  useEffect(() => {
    if (sourceArtifact === null) {
      setRevisions([])
      setPending("idle")
      return
    }
    const controller = new AbortController()
    const load = async (): Promise<void> => {
      setPending("loading")
      setError(null)
      setNewArtifact(null)
      setNewArtifactId("")
      try {
        const releaseReadback = api.listReleases(data.projectId, controller.signal).then((releases) => releasedArtifacts(releases, data.currentRun))
        const [revisionResponse, releaseIds] = await Promise.all([api.listArtifactRevisions(data.projectId, data.currentRun.run_id, data.currentRun.step_id, controller.signal), releaseReadback])
        assertCurrentRevisions(revisionResponse, data.currentRun)
        const canonicalParent = revisionResponse.artifacts.find((artifact) => artifact.artifact_id === sourceArtifact.artifact_id)
        if (canonicalParent === undefined) throw new ArtifactRevisionError("Die aktuelle kanonische Artefaktrevision fehlt in der Revisionsliste.")
        if (!controller.signal.aborted) {
          setRevisions(revisionResponse.artifacts)
          setParentArtifactId(canonicalParent.artifact_id)
          setReleasedIds(releaseIds)
          setPending("idle")
        }
      } catch (loadError) {
        if (!controller.signal.aborted) {
          setRevisions([])
          setError(messageFor(loadError))
          setPending("idle")
        }
      }
    }
    void load()
    return () => controller.abort()
  }, [api, data.currentRun, data.projectId, sourceArtifact])

  const loadContent = useCallback(async (): Promise<void> => {
    if (contentArtifact === null || isReleased) return
    try {
      const response = await api.getArtifactContent(data.projectId, contentArtifact.artifact_id, new AbortController().signal)
      if (!matchesCurrentRun(response.artifact, data.currentRun) || response.artifact.artifact_id !== contentArtifact.artifact_id) throw new ArtifactRevisionError("Der kanonische Artefaktinhalt ist nicht an die ausgewaehlte Revision gebunden.")
      setContent(atob(response.content_base64))
      setError(null)
    } catch (loadError) {
      setError(messageFor(loadError))
    }
  }, [api, contentArtifact, data.currentRun, data.projectId, isReleased])

  const save = useCallback(async (): Promise<void> => {
    if (parentArtifact === null || content === "" || isEditingLocked) return
    setPending("saving")
    setError(null)
    setDiff("")
    setValidation("")
    try {
      const saved = savedArtifact(await api.saveArtifactRevision(data.projectId, { bundle: {}, expected_parent_revision: parentArtifact.revision, gate_context: { evidence_by_gate: {} }, idempotency_key: `artifact-revision-${Date.now()}`, primary_document: content, run_id: data.currentRun.run_id }, new AbortController().signal))
      setPending("readback")
      const readback = await api.listArtifactRevisions(data.projectId, data.currentRun.run_id, data.currentRun.step_id, new AbortController().signal)
      assertCurrentRevisions(readback, data.currentRun)
      const verified = readback.artifacts.find((artifact) => artifact.artifact_id === saved.artifact_id)
      if (verified === undefined) throw new ArtifactRevisionError("Die gespeicherte Artefaktrevision fehlt im kanonischen Readback.")
      verifyReadback(saved, verified, parentArtifact, data.currentRun)
      setRevisions(readback.artifacts)
      setNewArtifact(verified)
      setNewArtifactId(verified.artifact_id)
    } catch (saveError) {
      setError(messageFor(saveError))
    } finally {
      setPending("idle")
    }
  }, [api, content, data.currentRun, data.projectId, isEditingLocked, parentArtifact])

  const compare = useCallback(async (): Promise<void> => {
    if (parentArtifact === null || comparisonArtifact === null || parentArtifact.artifact_id === comparisonArtifact.artifact_id || pending !== "idle") return
    try {
      const result = await api.compareArtifactRevisions(data.projectId, { left_artifact_id: parentArtifact.artifact_id, right_artifact_id: comparisonArtifact.artifact_id }, new AbortController().signal)
      if (result.left_artifact.artifact_id !== parentArtifact.artifact_id || result.right_artifact.artifact_id !== comparisonArtifact.artifact_id) throw new ArtifactRevisionError("Der kanonische Revisionsvergleich stimmt nicht mit der Auswahl ueberein.")
      setDiff(result.unified_diff)
      setError(null)
    } catch (compareError) {
      setError(messageFor(compareError))
    }
  }, [api, comparisonArtifact, data.projectId, parentArtifact, pending])

  const validate = useCallback(async (): Promise<void> => {
    if (newArtifact === null || pending !== "idle") return
    try {
      const result = await api.validateArtifactRevision(data.projectId, newArtifact.artifact_id, { content_sha256: newArtifact.content_sha256, revision: newArtifact.revision }, new AbortController().signal)
      setValidation(result.report)
      setError(null)
    } catch (validationError) {
      setError(messageFor(validationError))
    }
  }, [api, data.projectId, newArtifact, pending])

  return { canLoadContent, comparisonArtifact, content, diff, error, isEditingLocked, isReadbackPending: pending === "readback", isReleased, isSaving: pending === "saving", newArtifact, parentArtifact, revisions, validation, compare, loadContent, save, setContent, setNewArtifactId, setParentArtifactId, validate }
}
