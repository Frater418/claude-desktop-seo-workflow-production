import { useCallback, useState } from "react"
import type { ArtifactCandidateSaveRequest, ArtifactValidationRequest, GateContext, GateEvidenceDocument, JsonValue } from "../generated/api-types"

type JsonObject = {} & Record<string, JsonValue>
type Step4ArtifactPayload = Pick<ArtifactCandidateSaveRequest, "bundle" | "gate_context" | "primary_document" | "supporting_documents">

export class Step4ArtifactPayloadError extends Error {
  public readonly name = "Step4ArtifactPayloadError"

  public constructor(message: string) { super(message) }
}

function isObject(value: unknown): value is JsonObject { return typeof value === "object" && value !== null && !Array.isArray(value) }
function objectAt(value: unknown, subject: string): JsonObject { if (isObject(value)) return value; throw new Step4ArtifactPayloadError(`${subject} muss ein JSON-Objekt sein.`) }
function onlyKeys(value: JsonObject, keys: readonly string[], subject: string): void { if (Object.keys(value).some((key) => !keys.includes(key))) throw new Step4ArtifactPayloadError(`${subject} enthaelt ein unbekanntes Feld.`) }
function stringsAt(value: unknown, subject: string): readonly string[] {
  if (!Array.isArray(value) || value.some((entry) => typeof entry !== "string" || entry === "")) throw new Step4ArtifactPayloadError(`${subject} muss eine Liste nicht leerer Texte sein.`)
  return value
}
function jsonObject(text: string, subject: string): JsonObject {
  if (text.trim() === "") throw new Step4ArtifactPayloadError(`${subject} fehlt.`)
  try { return objectAt(JSON.parse(text), subject) } catch (error) {
    if (error instanceof Step4ArtifactPayloadError) throw error
    throw new Step4ArtifactPayloadError(`${subject} enthaelt kein lesbares JSON.`)
  }
}
function scalarMap(value: unknown, subject: string): Readonly<Record<string, string | number | boolean>> {
  const record = objectAt(value, subject)
  const parsed: Record<string, string | number | boolean> = {}
  for (const [key, entry] of Object.entries(record)) {
    if (typeof entry !== "string" && typeof entry !== "number" && typeof entry !== "boolean") throw new Step4ArtifactPayloadError(`${subject} darf nur Text, Zahlen oder Wahrheitswerte enthalten.`)
    parsed[key] = entry
  }
  if (Object.keys(parsed).length === 0) throw new Step4ArtifactPayloadError(`${subject} darf nicht leer sein.`)
  return parsed
}
function evidenceDocuments(value: unknown): readonly GateEvidenceDocument[] {
  if (!Array.isArray(value)) throw new Step4ArtifactPayloadError("evidence_documents muss eine Liste sein.")
  return value.map((entry) => {
    const document = objectAt(entry, "Ein Evidenzdokument")
    onlyKeys(document, ["classification", "evidence_id", "report_sha256", "source", "subject_content_sha256", "tool"], "Ein Evidenzdokument")
    const classification = document["classification"]
    if (classification !== "local_validation" && classification !== "local_simulated" && classification !== "external_report") throw new Step4ArtifactPayloadError("Ein Evidenzdokument hat keine gueltige Klassifizierung.")
    const field = (name: string): string => {
      const parsed = document[name]
      if (typeof parsed === "string" && parsed !== "") return parsed
      throw new Step4ArtifactPayloadError(`Ein Evidenzdokument hat kein lesbares Feld ${name}.`)
    }
    const reportSha256 = field("report_sha256")
    const subjectContentSha256 = field("subject_content_sha256")
    if (!/^[a-f0-9]{64}$/.test(reportSha256) || !/^[a-f0-9]{64}$/.test(subjectContentSha256)) throw new Step4ArtifactPayloadError("Ein Evidenzdokument hat keinen gueltigen SHA-256-Hash.")
    return { classification, evidence_id: field("evidence_id"), report_sha256: reportSha256, source: field("source"), subject_content_sha256: subjectContentSha256, tool: field("tool") }
  })
}
function gateContext(text: string): GateContext {
  const parsed = jsonObject(text, "Lokaler GateContext")
  onlyKeys(parsed, ["available_tools", "configured_tools", "evidence_by_gate", "evidence_documents", "not_applicable_decisions", "production", "site_status"], "Lokaler GateContext")
  const evidence = objectAt(parsed["evidence_by_gate"], "evidence_by_gate")
  const evidenceByGate: Record<string, Readonly<Record<string, string | number | boolean>>> = {}
  for (const [gateId, values] of Object.entries(evidence)) evidenceByGate[gateId] = scalarMap(values, `evidence_by_gate.${gateId}`)
  if (Object.keys(evidenceByGate).length === 0) throw new Step4ArtifactPayloadError("evidence_by_gate darf nicht leer sein.")
  const siteStatus = parsed["site_status"]
  if (siteStatus !== undefined && siteStatus !== null && siteStatus !== "existing_site" && siteStatus !== "non_existing_site") throw new Step4ArtifactPayloadError("site_status ist nicht gueltig.")
  const production = parsed["production"]
  if (production !== undefined && typeof production !== "boolean") throw new Step4ArtifactPayloadError("production muss ein Wahrheitswert sein.")
  const configuredTools = parsed["configured_tools"] === undefined ? undefined : stringsAt(parsed["configured_tools"], "configured_tools")
  const availableTools = parsed["available_tools"] === undefined ? undefined : stringsAt(parsed["available_tools"], "available_tools")
  const notApplicable = parsed["not_applicable_decisions"] === undefined ? undefined : Object.fromEntries(Object.entries(objectAt(parsed["not_applicable_decisions"], "not_applicable_decisions")).map(([key, value]) => [key, objectAt(value, `not_applicable_decisions.${key}`)]))
  return { evidence_by_gate: evidenceByGate, ...(parsed["evidence_documents"] === undefined ? {} : { evidence_documents: evidenceDocuments(parsed["evidence_documents"]) }), ...(configuredTools === undefined ? {} : { configured_tools: configuredTools }), ...(availableTools === undefined ? {} : { available_tools: availableTools }), ...(notApplicable === undefined ? {} : { not_applicable_decisions: notApplicable }), ...(production === undefined ? {} : { production }), ...(siteStatus === undefined ? {} : { site_status: siteStatus }) }
}

export function useStep4ArtifactPayload(): {
  readonly supportingDocument: string
  readonly bundle: string
  readonly gateContext: string
  readonly setSupportingDocument: (value: string) => void
  readonly setBundle: (value: string) => void
  readonly setGateContext: (value: string) => void
  readonly reset: () => void
  readonly parse: (primaryDocument: string) => Step4ArtifactPayload
  readonly validationRequest: (primaryDocument: string, contentSha256: string, revision: number) => ArtifactValidationRequest
} {
  const [supportingDocument, setSupportingDocument] = useState("")
  const [bundle, setBundle] = useState("")
  const [context, setGateContext] = useState("")
  const reset = useCallback((): void => { setSupportingDocument(""); setBundle(""); setGateContext("") }, [])
  const parse = useCallback((primaryDocument: string): Step4ArtifactPayload => ({ primary_document: jsonObject(primaryDocument, "Primaeres Artefakt"), supporting_documents: [jsonObject(supportingDocument, "Unterstuetzendes registriertes Dokument")], bundle: jsonObject(bundle, "Operatives Preflight-Bundle"), gate_context: gateContext(context) }), [bundle, context, supportingDocument])
  const validationRequest = useCallback((primaryDocument: string, contentSha256: string, revision: number): ArtifactValidationRequest => {
    const payload = parse(primaryDocument)
    return { bundle: payload.bundle, content_sha256: contentSha256, gate_context: payload.gate_context, revision, supporting_documents: payload.supporting_documents ?? [] }
  }, [parse])
  return { supportingDocument, bundle, gateContext: context, setSupportingDocument, setBundle, setGateContext, reset, parse, validationRequest }
}
