import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type { ArtifactRecord, ArtifactRevisionListResponse } from "../generated/api-types"
import type { OperatorApiClient } from "../api/client"
import type { CurrentRun, ReleaseRead } from "../api/readModels"
import { ArtifactRevisionError, assertCurrentRevisions, isStep4, matchesCurrentRun, messageFor, primaryLineage, releasedArtifacts, savedOutputSet, supportingSibling, verifiedOutputSet } from "./artifactRevisionReadback"
import { useStep4ArtifactPayload } from "./useStep4ArtifactPayload"

export const releasedArtifactRemediation = "Freigegebene Artefakte sind unveraenderlich. Starten Sie einen neuen Lauf statt dieses Artefakt zu bearbeiten."
export type ArtifactRevisionApi = Pick<OperatorApiClient, "compareArtifactRevisions" | "getArtifactContent" | "listArtifactRevisions" | "listReleases" | "saveArtifactRevision" | "validateArtifactRevision">
export type ArtifactRevisionData = { readonly projectId: string; readonly currentRun: CurrentRun; readonly current: { readonly artifact: ArtifactRecord | null } }
type PendingState = "idle" | "loading" | "content-loading" | "saving" | "readback"
type RevisionResult = { readonly content: string; readonly canLoadContent: boolean; readonly canSave: boolean; readonly comparisonArtifact: ArtifactRecord | null; readonly diff: string; readonly error: string | null; readonly isEditingLocked: boolean; readonly isContentLoading: boolean; readonly isReleased: boolean; readonly isSaving: boolean; readonly isReadbackPending: boolean; readonly isStep4: boolean; readonly newArtifact: ArtifactRecord | null; readonly parentArtifact: ArtifactRecord | null; readonly revisions: readonly ArtifactRecord[]; readonly supportingDocument: string; readonly bundle: string; readonly gateContext: string; readonly validation: string; readonly compare: () => Promise<void>; readonly loadContent: () => Promise<void>; readonly save: () => Promise<void>; readonly setContent: (content: string) => void; readonly setNewArtifactId: (artifactId: string) => void; readonly setParentArtifactId: (artifactId: string) => void; readonly setSupportingDocument: (value: string) => void; readonly setBundle: (value: string) => void; readonly setGateContext: (value: string) => void; readonly validate: () => Promise<void> }

function decoded(contentBase64: string): string { return atob(contentBase64) }
function validationMessage(views: readonly string[], qgrIds: readonly string[]): string { return `Lokale Schritt-Vorpruefung erfolgreich. Abgeleitete Ansichten: ${views.join(", ") || "keine"}. Lokale QGR-IDs: ${qgrIds.join(", ") || "keine"}. Kein QGR wurde gespeichert und keine externe Ausfuehrung wurde behauptet.` }

export function useArtifactRevision({ api, data }: { readonly api: ArtifactRevisionApi; readonly data: ArtifactRevisionData }): RevisionResult {
  const sourceArtifact = data.current.artifact
  const step4 = useStep4ArtifactPayload()
  const [allRevisions, setAllRevisions] = useState<readonly ArtifactRecord[]>([])
  const [parentArtifactId, setParentArtifactIdState] = useState(sourceArtifact?.artifact_id ?? "")
  const [newArtifactId, setNewArtifactId] = useState("")
  const [content, setContentState] = useState("")
  const [newArtifact, setNewArtifact] = useState<ArtifactRecord | null>(null)
  const [newSupportingArtifact, setNewSupportingArtifact] = useState<ArtifactRecord | null>(null)
  const [releasedIds, setReleasedIds] = useState<readonly string[]>([])
  const [pending, setPending] = useState<PendingState>("loading")
  const [error, setError] = useState<string | null>(null)
  const [diff, setDiff] = useState("")
  const [validation, setValidation] = useState("")
  const contentRef = useRef("")
  const versionRef = useRef(0)
  const selectedParentRef = useRef(sourceArtifact?.artifact_id ?? "")
  const contentControllerRef = useRef<AbortController | null>(null)
  const revisions = useMemo(() => sourceArtifact === null ? [] : primaryLineage(allRevisions, sourceArtifact, newArtifact), [allRevisions, newArtifact, sourceArtifact])
  const parentArtifact = useMemo(() => revisions.find((artifact) => artifact.artifact_id === parentArtifactId) ?? null, [parentArtifactId, revisions])
  const comparisonArtifact = useMemo(() => revisions.find((artifact) => artifact.artifact_id === newArtifactId) ?? null, [newArtifactId, revisions])
  const step4Enabled = sourceArtifact !== null && isStep4(sourceArtifact.step_id)
  const isReleased = parentArtifact !== null && releasedIds.includes(parentArtifact.artifact_id)
  const isEditingLocked = parentArtifact === null || isReleased || pending !== "idle"
  const canLoadContent = parentArtifact !== null && !isReleased && pending === "idle"
  const canSave = step4Enabled && content !== "" && !isEditingLocked
  const resetEditor = useCallback((): void => { contentControllerRef.current?.abort(); contentControllerRef.current = null; versionRef.current += 1; contentRef.current = ""; setContentState(""); step4.reset(); setDiff(""); setValidation(""); setError(null); setNewArtifact(null); setNewSupportingArtifact(null); setNewArtifactId("") }, [step4.reset])
  const setContent = useCallback((nextContent: string): void => { versionRef.current += 1; contentRef.current = nextContent; setContentState(nextContent) }, [])
  const setParentArtifactId = useCallback((artifactId: string): void => { resetEditor(); selectedParentRef.current = artifactId; setParentArtifactIdState(artifactId); setPending("idle") }, [resetEditor])

  useEffect(() => {
    resetEditor(); setAllRevisions([]); setReleasedIds([]); selectedParentRef.current = sourceArtifact?.artifact_id ?? ""; setParentArtifactIdState(sourceArtifact?.artifact_id ?? "")
    if (sourceArtifact === null) { setPending("idle"); return }
    const controller = new AbortController()
    const load = async (): Promise<void> => {
      setPending("loading")
      try {
        const releases = api.listReleases(data.projectId, controller.signal).then((value) => releasedArtifacts(value, data.currentRun))
        const [revisionResponse, releaseIds] = await Promise.all([api.listArtifactRevisions(data.projectId, data.currentRun.run_id, data.currentRun.step_id, controller.signal), releases])
        assertCurrentRevisions(revisionResponse.artifacts, data.currentRun)
        if (!revisionResponse.artifacts.some((artifact) => artifact.artifact_id === sourceArtifact.artifact_id)) throw new ArtifactRevisionError("Die aktuelle kanonische Primaerrevision fehlt in der Revisionsliste.")
        if (!controller.signal.aborted) { setAllRevisions(revisionResponse.artifacts); setReleasedIds(releaseIds); setPending("idle") }
      } catch (loadError) { if (!controller.signal.aborted) { setError(messageFor(loadError)); setPending("idle") } }
    }
    void load()
    return () => controller.abort()
  }, [api, data.currentRun, data.projectId, resetEditor, sourceArtifact])
  useEffect(() => () => contentControllerRef.current?.abort(), [])

  const loadContent = useCallback(async (): Promise<void> => {
    const primary = parentArtifact
    if (primary === null || selectedParentRef.current !== primary.artifact_id || isReleased) return
    contentControllerRef.current?.abort()
    const controller = new AbortController()
    const loadedVersion = versionRef.current
    contentControllerRef.current = controller
    setPending("content-loading")
    try {
      const supporting = step4Enabled ? supportingSibling(allRevisions, primary) : null
      const primaryResponse = api.getArtifactContent(data.projectId, primary.artifact_id, controller.signal)
      const supportingResponse = supporting === null ? null : api.getArtifactContent(data.projectId, supporting.artifact_id, controller.signal)
      const [loadedPrimary, loadedSupporting] = await Promise.all([primaryResponse, supportingResponse])
      if (!matchesCurrentRun(loadedPrimary.artifact, data.currentRun) || loadedPrimary.artifact.artifact_id !== primary.artifact_id || loadedPrimary.artifact.revision !== primary.revision) throw new ArtifactRevisionError("Der kanonische Primaerinhalt ist nicht an die ausgewaehlte Revision gebunden.")
      if (supporting !== null && (loadedSupporting === null || !matchesCurrentRun(loadedSupporting.artifact, data.currentRun) || loadedSupporting.artifact.artifact_id !== supporting.artifact_id || loadedSupporting.artifact.artifact_id === primary.artifact_id || loadedSupporting.artifact.revision !== primary.revision)) throw new ArtifactRevisionError("Der kanonische Unterstuetzungsinhalt ist nicht an die ausgewaehlte Revision gebunden.")
      if (controller.signal.aborted || contentControllerRef.current !== controller || versionRef.current !== loadedVersion || selectedParentRef.current !== primary.artifact_id) return
      const primaryContent = decoded(loadedPrimary.content_base64)
      setContent(primaryContent)
      if (loadedSupporting !== null) step4.setSupportingDocument(decoded(loadedSupporting.content_base64))
      setError(null)
    } catch (loadError) { if (!controller.signal.aborted && contentControllerRef.current === controller) setError(messageFor(loadError)) } finally { if (contentControllerRef.current === controller) { contentControllerRef.current = null; setPending("idle") } }
  }, [allRevisions, api, data.currentRun, data.projectId, isReleased, parentArtifact, setContent, step4, step4Enabled])

  const save = useCallback(async (): Promise<void> => {
    if (parentArtifact === null || !canSave) return
    let payload
    try { payload = step4.parse(contentRef.current) } catch (saveError) { setError(messageFor(saveError)); return }
    setPending("saving"); setError(null); setDiff(""); setValidation("")
    try {
      const saved = savedOutputSet(await api.saveArtifactRevision(data.projectId, { ...payload, expected_parent_revision: parentArtifact.revision, idempotency_key: `artifact-revision-${Date.now()}`, run_id: data.currentRun.run_id }, new AbortController().signal))
      setPending("readback")
      const readback: ArtifactRevisionListResponse = await api.listArtifactRevisions(data.projectId, data.currentRun.run_id, data.currentRun.step_id, new AbortController().signal)
      assertCurrentRevisions(readback.artifacts, data.currentRun)
      const verified = verifiedOutputSet(saved, readback.artifacts, parentArtifact, data.currentRun)
      setAllRevisions(readback.artifacts); setNewArtifact(verified.primary); setNewSupportingArtifact(verified.supporting); setNewArtifactId(verified.primary.artifact_id)
    } catch (saveError) { setError(messageFor(saveError)) } finally { setPending("idle") }
  }, [api, canSave, data.currentRun, data.projectId, parentArtifact, step4])

  const compare = useCallback(async (): Promise<void> => {
    if (parentArtifact === null || comparisonArtifact === null || parentArtifact.artifact_id === comparisonArtifact.artifact_id || pending !== "idle") return
    try { const result = await api.compareArtifactRevisions(data.projectId, { left_artifact_id: parentArtifact.artifact_id, right_artifact_id: comparisonArtifact.artifact_id }, new AbortController().signal); if (result.left_artifact.artifact_id !== parentArtifact.artifact_id || result.right_artifact.artifact_id !== comparisonArtifact.artifact_id) throw new ArtifactRevisionError("Der kanonische Revisionsvergleich stimmt nicht mit der Auswahl ueberein."); setDiff(result.unified_diff); setError(null) } catch (compareError) { setError(messageFor(compareError)) }
  }, [api, comparisonArtifact, data.projectId, parentArtifact, pending])
  const validate = useCallback(async (): Promise<void> => {
    if (!step4Enabled || newArtifact === null || newSupportingArtifact === null || pending !== "idle") return
    let request
    try { request = step4.validationRequest(contentRef.current, newArtifact.content_sha256, newArtifact.revision) } catch (validationError) { setError(messageFor(validationError)); return }
    try { const result = await api.validateArtifactRevision(data.projectId, newArtifact.artifact_id, request, new AbortController().signal); if (result.artifactId !== newArtifact.artifact_id || result.artifactHash !== newArtifact.content_sha256 || result.artifactRevision !== newArtifact.revision || result.stepId !== newArtifact.step_id) throw new ArtifactRevisionError("Die lokale Schritt-Vorpruefung ist nicht an die neue Primaerrevision gebunden."); setValidation(validationMessage(result.derivedViews.map((view) => view.name), result.localQualityGateRuns.map((run) => run.localQualityGateRunId))); setError(null) } catch (validationError) { setError(messageFor(validationError)) }
  }, [api, data.projectId, newArtifact, newSupportingArtifact, pending, step4, step4Enabled])
  return { content, canLoadContent, canSave, comparisonArtifact, diff, error, isEditingLocked, isContentLoading: pending === "content-loading", isReleased, isSaving: pending === "saving", isReadbackPending: pending === "readback", isStep4: step4Enabled, newArtifact, parentArtifact, revisions, supportingDocument: step4.supportingDocument, bundle: step4.bundle, gateContext: step4.gateContext, validation, compare, loadContent, save, setContent, setNewArtifactId, setParentArtifactId, setSupportingDocument: step4.setSupportingDocument, setBundle: step4.setBundle, setGateContext: step4.setGateContext, validate }
}
