import { useEffect, useMemo, useState } from "react"
import type { OperatorApiClient } from "../api/client"
import type { ArtifactRecord } from "../generated/api-types"
import type { OperatorWorkspaceData } from "./useOperatorWorkspace"

type JsonValue = string | number | boolean | null | JsonObject | readonly JsonValue[]
interface JsonObject { readonly [key: string]: JsonValue }
type ReviewArtifactPayload = { readonly artifact: ArtifactRecord; readonly content: string }
type ArtifactSelection = { readonly kind: "ready"; readonly primary: ArtifactRecord; readonly supporting: ArtifactRecord } | { readonly kind: "blocked"; readonly message: string }
export type ReviewArtifactPayloadState = { readonly kind: "loading" } | { readonly kind: "ready"; readonly primary: ReviewArtifactPayload; readonly supporting: ReviewArtifactPayload } | { readonly kind: "blocked"; readonly message: string }

class ReviewArtifactPayloadError extends Error {
  public readonly name = "ReviewArtifactPayloadError"

  public constructor(message: string) { super(message) }
}

function isObject(value: unknown): value is Record<string, unknown> { return typeof value === "object" && value !== null && !Array.isArray(value) }
function isStep4(stepId: string): boolean { return stepId === "4a" || stepId === "4b" }
function belongsToCurrentRun(artifact: ArtifactRecord, data: OperatorWorkspaceData): boolean { return artifact.tenant_id === data.currentRun.tenant_id && artifact.project_id === data.currentRun.project_id && artifact.run_id === data.currentRun.run_id && artifact.step_id === data.currentRun.step_id }
function sameArtifact(expected: ArtifactRecord, actual: ArtifactRecord): boolean {
  const expectedParents = expected.parent_artifact_ids ?? []
  const actualParents = actual.parent_artifact_ids ?? []
  return expected.artifact_id === actual.artifact_id && expected.content_sha256 === actual.content_sha256 && expected.created_at === actual.created_at && expected.input_hash === actual.input_hash && expected.project_id === actual.project_id && expected.revision === actual.revision && expected.run_id === actual.run_id && expected.step_id === actual.step_id && expected.storage_key === actual.storage_key && expected.tenant_id === actual.tenant_id && expectedParents.length === actualParents.length && expectedParents.every((parent, index) => parent === actualParents[index])
}
function selectArtifacts(data: OperatorWorkspaceData): ArtifactSelection {
  const primary = data.current.artifact
  if (primary === null) return { kind: "blocked", message: "Die aktuelle kanonische Primaerrevision fehlt." }
  if (!isStep4(primary.step_id) || !belongsToCurrentRun(primary, data)) return { kind: "blocked", message: "Die aktuelle Primaerrevision ist nicht an den aktiven Schritt 4 gebunden." }
  const siblings = data.artifacts.filter((artifact) => artifact.artifact_id !== primary.artifact_id && artifact.revision === primary.revision && belongsToCurrentRun(artifact, data))
  if (siblings.length !== 1 || siblings[0] === undefined) return { kind: "blocked", message: "Zur aktuellen Primaerrevision fehlt genau ein identisch gebundenes unterstuetzendes Dokument." }
  return { kind: "ready", primary, supporting: siblings[0] }
}
function normalizedJson(value: unknown): JsonValue {
  if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "boolean") return value
  if (Array.isArray(value)) return value.map(normalizedJson)
  if (isObject(value)) return Object.fromEntries(Object.keys(value).sort().map((key): [string, JsonValue] => [key, normalizedJson(value[key])]))
  throw new ReviewArtifactPayloadError("Der geladene Dokumentinhalt enthaelt keinen gueltigen JSON-Wert.")
}
function decodeJsonObject(contentBase64: string): string {
  if (contentBase64 === "" || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(contentBase64)) throw new ReviewArtifactPayloadError("Der geladene Dokumentinhalt ist nicht gueltig Base64-kodiert.")
  let decoded: string
  try {
    const bytes = Uint8Array.from(atob(contentBase64), (character) => character.charCodeAt(0))
    decoded = new TextDecoder("utf-8", { fatal: true }).decode(bytes)
  } catch (error) {
    if (error instanceof TypeError || error instanceof DOMException) throw new ReviewArtifactPayloadError("Der geladene Dokumentinhalt ist kein gueltiges UTF-8.")
    throw error
  }
  let value: unknown
  try { value = JSON.parse(decoded) } catch (error) {
    if (error instanceof SyntaxError) throw new ReviewArtifactPayloadError("Der geladene Dokumentinhalt ist kein gueltiges JSON-Objekt.")
    throw error
  }
  if (!isObject(value)) throw new ReviewArtifactPayloadError("Der geladene Dokumentinhalt muss ein JSON-Objekt sein.")
  return JSON.stringify(normalizedJson(value), null, 2)
}
function errorMessage(error: unknown): string { return error instanceof Error ? error.message : "Die Review-Unterlagen konnten nicht geladen werden." }

export function useReviewArtifactPayload({ api, data }: { readonly api: Pick<OperatorApiClient, "getArtifactContent">; readonly data: OperatorWorkspaceData }): ReviewArtifactPayloadState {
  const selection = useMemo(() => selectArtifacts(data), [data])
  const [state, setState] = useState<ReviewArtifactPayloadState>({ kind: "loading" })

  useEffect(() => {
    if (selection.kind === "blocked") { setState(selection); return }
    const controller = new AbortController()
    setState({ kind: "loading" })
    const load = async (): Promise<void> => {
      try {
        const [primaryResponse, supportingResponse] = await Promise.all([api.getArtifactContent(data.projectId, selection.primary.artifact_id, controller.signal), api.getArtifactContent(data.projectId, selection.supporting.artifact_id, controller.signal)])
        if (!sameArtifact(selection.primary, primaryResponse.artifact)) throw new ReviewArtifactPayloadError("Der geladene Primaerinhalt ist nicht exakt an die aktuelle Revision gebunden.")
        if (!sameArtifact(selection.supporting, supportingResponse.artifact)) throw new ReviewArtifactPayloadError("Der geladene unterstuetzende Inhalt ist nicht exakt an die aktuelle Revision gebunden.")
        const primary: ReviewArtifactPayload = { artifact: selection.primary, content: decodeJsonObject(primaryResponse.content_base64) }
        const supporting: ReviewArtifactPayload = { artifact: selection.supporting, content: decodeJsonObject(supportingResponse.content_base64) }
        if (!controller.signal.aborted) setState({ kind: "ready", primary, supporting })
      } catch (error) {
        if (!controller.signal.aborted) setState({ kind: "blocked", message: errorMessage(error) })
      }
    }
    void load()
    return () => controller.abort()
  }, [api, data.projectId, selection])

  return state
}
