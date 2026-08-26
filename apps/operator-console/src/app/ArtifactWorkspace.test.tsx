import { afterEach, describe, expect, it, vi } from "vitest"
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react"
import type { ArtifactContentResponse, ArtifactRecord, ArtifactRevisionListResponse, DataEnvelope, GateContext } from "../generated/api-types"
import type { ReleaseRead } from "../api/readModels"
import type { ArtifactPreflightRead } from "../api/artifactPreflightReadModel"
import { ArtifactWorkspace } from "./ArtifactWorkspace"
import type { ArtifactRevisionApi, ArtifactRevisionData } from "./useArtifactRevision"
import { releasedArtifactRemediation, useArtifactRevision } from "./useArtifactRevision"

const hash = (character: string): string => character.repeat(64)
const olderPrimary: ArtifactRecord = { artifact_id: "artifact-step4a-primary-000", content_sha256: hash("d"), created_at: "2026-08-22T10:00:00Z", input_hash: hash("b"), project_id: "project-step4", revision: 16, run_id: "run-step4a", step_id: "4a", storage_key: "outputs/briefing.json", tenant_id: "tenant-step4" }
const olderSupporting: ArtifactRecord = { ...olderPrimary, artifact_id: "artifact-step4a-support-000", content_sha256: hash("e"), storage_key: "outputs/briefing-support.json" }
const primary: ArtifactRecord = { ...olderPrimary, artifact_id: "artifact-step4a-primary-001", content_sha256: hash("a"), created_at: "2026-08-23T10:00:00Z", parent_artifact_ids: [olderPrimary.artifact_id], revision: 17 }
const supporting: ArtifactRecord = { ...primary, artifact_id: "artifact-step4a-support-001", content_sha256: hash("c"), storage_key: "outputs/briefing-support.json" }
const savedPrimary: ArtifactRecord = { ...primary, artifact_id: "artifact-step4a-primary-002", content_sha256: hash("f"), parent_artifact_ids: [primary.artifact_id], revision: 18 }
const savedSupporting: ArtifactRecord = { ...supporting, artifact_id: "artifact-step4a-support-002", content_sha256: hash("0"), parent_artifact_ids: [primary.artifact_id], revision: 18 }
const currentData: ArtifactRevisionData = { projectId: primary.project_id, currentRun: { tenant_id: primary.tenant_id, project_id: primary.project_id, run_id: primary.run_id, step_id: "4a", expected_revision: primary.revision }, current: { artifact: primary } }
const initialRevisions: ArtifactRevisionListResponse = { artifacts: [olderPrimary, olderSupporting, primary, supporting] }
const savedRevisions: ArtifactRevisionListResponse = { artifacts: [...initialRevisions.artifacts, savedPrimary, savedSupporting] }
const gateContext: GateContext = { evidence_by_gate: { "GATE-4A-SEO": { content_complete: true, evidence_count: 2 } }, evidence_documents: [{ classification: "local_validation", evidence_id: "evidence-step4a-001", report_sha256: hash("a"), source: "operator-console", subject_content_sha256: hash("a"), tool: "step-validation-service" }] }
const primaryDocument = { briefing: "Canonical Step 4A content" }
const supportingDocument = { schema: { type: "FAQPage" } }
const bundle = { execution_identity: { step_id: "4a", revision: 18 } }

afterEach(() => cleanup())

function encoded(value: object): string { return btoa(JSON.stringify(value)) }
function preflight(): ArtifactPreflightRead { return { artifactId: savedPrimary.artifact_id, artifactHash: savedPrimary.content_sha256, artifactRevision: savedPrimary.revision, stepId: "4a", validationMode: "step_preflight", valid: true, derivedViews: [{ artifactId: savedPrimary.artifact_id, name: "copywriter-briefing", content: "Briefing content" }], localQualityGateRuns: [{ localQualityGateRunId: "qgr-4a-seo-aaaaaaaa", qualityGateId: "GATE-4A-SEO", result: "passed", evidenceSummary: { content_complete: true, evidence_count: 2 }, findings: [] }], report: "copywriter-briefing\nBriefing content" } }
function content(artifact: ArtifactRecord, document: object): ArtifactContentResponse { return { artifact, content_base64: encoded(document) } }
function createApi(responses: readonly ArtifactRevisionListResponse[] = [initialRevisions, savedRevisions], releases: readonly ReleaseRead[] = [], getContent: (artifactId: string) => Promise<ArtifactContentResponse> = async (artifactId) => artifactId === supporting.artifact_id ? content(supporting, supportingDocument) : content(primary, primaryDocument), saveResponse: DataEnvelope = { data: { records: [savedPrimary, savedSupporting] } }): { readonly api: ArtifactRevisionApi; readonly save: ReturnType<typeof vi.fn>; readonly validate: ReturnType<typeof vi.fn> } {
  let request = 0
  const save = vi.fn(async () => saveResponse)
  const validate = vi.fn(async () => preflight())
  const api = { getArtifactContent: vi.fn(async (_projectId, artifactId) => getContent(artifactId)), saveArtifactRevision: save, listArtifactRevisions: vi.fn(async () => responses[Math.min(request++, responses.length - 1)] ?? initialRevisions), listReleases: vi.fn(async () => releases), compareArtifactRevisions: vi.fn(async () => ({ left_artifact: primary, right_artifact: savedPrimary, unified_diff: "+ Briefing" })), validateArtifactRevision: validate } satisfies ArtifactRevisionApi
  return { api, save, validate }
}
async function renderEditor(api: ArtifactRevisionApi): Promise<void> { render(<ArtifactWorkspace api={api} data={currentData} />); await within(screen.getByLabelText("Ausgangsrevision")).findByRole("option", { name: "Revision 17" }) }
async function loadAndFill(): Promise<void> {
  fireEvent.click(screen.getByRole("button", { name: "outputs/briefing.json, Revision 17" }))
  await screen.findByDisplayValue(JSON.stringify(primaryDocument))
  fireEvent.change(screen.getByLabelText("Ergebnisinhalt bearbeiten"), { target: { value: JSON.stringify(primaryDocument) } })
  fireEvent.change(screen.getByLabelText("Unterstuetzendes registriertes Dokument"), { target: { value: JSON.stringify(supportingDocument) } })
  fireEvent.change(screen.getByLabelText("Operatives Preflight-Bundle"), { target: { value: JSON.stringify(bundle) } })
  fireEvent.change(screen.getByLabelText("Lokaler GateContext und Nachweise"), { target: { value: JSON.stringify(gateContext) } })
}
async function save(): Promise<void> { fireEvent.click(within(screen.getByLabelText("Ergebnisaktionen")).getByRole("button", { name: "Als neue Revision speichern" })); await screen.findByText("Revision 18 wurde unveraenderlich gespeichert.") }

describe("ArtifactWorkspace Step 4 output set", () => {
  it("Given a Step 4 primary revision, when content loads, then it fetches and displays exactly one supporting sibling", async () => {
    const fixture = createApi()
    await renderEditor(fixture.api)
    await loadAndFill()
    expect(fixture.api.getArtifactContent).toHaveBeenCalledTimes(2)
    expect(fixture.api.getArtifactContent).toHaveBeenCalledWith(primary.project_id, primary.artifact_id, expect.any(AbortSignal))
    expect(fixture.api.getArtifactContent).toHaveBeenCalledWith(primary.project_id, supporting.artifact_id, expect.any(AbortSignal))
    expect(screen.getByLabelText("Unterstuetzendes registriertes Dokument")).toHaveValue(JSON.stringify(supportingDocument))
  })

  it("Given sibling records share revisions, when the revision selector renders, then it contains only the primary lineage", async () => {
    await renderEditor(createApi().api)
    expect(within(screen.getByLabelText("Ausgangsrevision")).getAllByRole("option")).toHaveLength(3)
  })

  it.each(["Ergebnisinhalt bearbeiten", "Unterstuetzendes registriertes Dokument", "Operatives Preflight-Bundle", "Lokaler GateContext und Nachweise"])("Given invalid %s JSON, when save is requested, then it shows an alert without an API call", async (label) => {
    const fixture = createApi()
    await renderEditor(fixture.api)
    await loadAndFill()
    fireEvent.change(screen.getByLabelText(label), { target: { value: "[]" } })
    fireEvent.click(screen.getByRole("button", { name: "Als neue Revision speichern" }))
    expect(await screen.findByRole("alert")).toHaveTextContent("JSON-Objekt")
    expect(fixture.save).not.toHaveBeenCalled()
  })

  it("Given parsed Step 4 materials, when saving completes, then it sends exact objects and verifies both immutable records", async () => {
    const fixture = createApi()
    await renderEditor(fixture.api)
    await loadAndFill()
    await save()
    expect(fixture.save).toHaveBeenCalledWith(primary.project_id, expect.objectContaining({ bundle, gate_context: gateContext, primary_document: primaryDocument, supporting_documents: [supportingDocument] }), expect.any(AbortSignal))
    expect(within(screen.getByLabelText("Neue Revision")).getAllByRole("option")).toHaveLength(4)
  })

  it("Given a malformed save envelope, when save returns, then it fails before claiming persistence", async () => {
    const fixture = createApi([initialRevisions], [], undefined, { data: { artifact_id: savedPrimary.artifact_id } })
    await renderEditor(fixture.api)
    await loadAndFill()
    fireEvent.click(screen.getByRole("button", { name: "Als neue Revision speichern" }))
    expect(await screen.findByRole("alert")).toHaveTextContent("Speicherantwort")
    expect(screen.queryByText("Revision 18 wurde unveraenderlich gespeichert.")).toBeNull()
  })

  it("Given a verified Step 4 output set, when local preflight is requested, then it sends all material and reports local views and QGR IDs", async () => {
    const fixture = createApi()
    await renderEditor(fixture.api)
    await loadAndFill()
    await save()
    fireEvent.click(screen.getByRole("button", { name: "Schritt 4 Preflight ausführen" }))
    await waitFor(() => expect(fixture.validate).toHaveBeenCalledWith(primary.project_id, savedPrimary.artifact_id, { bundle, content_sha256: savedPrimary.content_sha256, gate_context: gateContext, revision: savedPrimary.revision, supporting_documents: [supportingDocument] }, expect.any(AbortSignal)))
    expect(await screen.findByText(/Lokale Schritt-Vorpruefung erfolgreich/)).toBeInTheDocument()
    expect(screen.getByText(/copywriter-briefing/)).toBeInTheDocument()
    expect(screen.getByText(/qgr-4a-seo-aaaaaaaa/)).toBeInTheDocument()
  })

  it("Given invalid GateContext after save, when local preflight is requested, then it shows an alert without a validation call", async () => {
    const fixture = createApi()
    await renderEditor(fixture.api)
    await loadAndFill()
    await save()
    fireEvent.change(screen.getByLabelText("Lokaler GateContext und Nachweise"), { target: { value: "[]" } })
    fireEvent.click(screen.getByRole("button", { name: "Schritt 4 Preflight ausführen" }))
    expect(await screen.findByRole("alert")).toHaveTextContent("JSON-Objekt")
    expect(fixture.validate).not.toHaveBeenCalled()
  })

  it("Given a stale sibling response, when a newer primary selection is made, then the stale content cannot overwrite the editor", async () => {
    let resolveOlder: (value: ArtifactContentResponse) => void = () => undefined
    const olderResponse = new Promise<ArtifactContentResponse>((resolve) => { resolveOlder = resolve })
    const fixture = createApi([initialRevisions], [], async (artifactId) => artifactId === olderPrimary.artifact_id ? olderResponse : artifactId === olderSupporting.artifact_id ? content(olderSupporting, supportingDocument) : content(primary, primaryDocument))
    const { result } = renderHook(() => useArtifactRevision({ api: fixture.api, data: currentData }))
    await waitFor(() => expect(result.current.parentArtifact).toEqual(primary))
    act(() => result.current.setParentArtifactId(olderPrimary.artifact_id))
    const pendingLoad = result.current.loadContent()
    act(() => result.current.setParentArtifactId(primary.artifact_id))
    resolveOlder(content(olderPrimary, { briefing: "stale" }))
    await act(async () => pendingLoad)
    expect(result.current.content).toBe("")
  })

  it("Given a released Step 4 primary, when the editor opens, then its immutable lock remains active", async () => {
    const release: ReleaseRead = { releaseId: "release-step4a", tenantId: primary.tenant_id, projectId: primary.project_id, runId: primary.run_id, stepId: "4a", gateId: "GATE-4A-SEO", artifactId: primary.artifact_id, artifactHash: primary.content_sha256, artifactRevision: primary.revision, approvalId: "approval-step4a", policyVersion: "1.0.0", releasedAt: "2026-08-23T10:00:00Z" }
    await renderEditor(createApi([initialRevisions], [release]).api)
    expect(await screen.findByText(releasedArtifactRemediation)).toBeInTheDocument()
    expect(screen.getByLabelText("Ergebnisinhalt bearbeiten")).toBeDisabled()
  })
})
