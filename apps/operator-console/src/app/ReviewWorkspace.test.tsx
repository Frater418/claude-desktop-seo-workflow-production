import { afterEach, describe, expect, it, vi } from "vitest"
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import { createOperatorApiClient } from "../api/client"
import { parseGates } from "../api/readModels"
import type { CurrentRun, GateRead, StepRead } from "../api/readModels"
import type { ActionConfirmResult, ActionIntent, ActionPreview, ArtifactContentResponse, ArtifactRecord } from "../generated/api-types"
import type { OperatorWorkspaceData } from "./useOperatorWorkspace"
import { ReviewWorkspace } from "./ReviewWorkspace"

const currentRun: CurrentRun = { tenant_id: "tenant-review", project_id: "project-review", run_id: "run-review", step_id: "4a", expected_revision: 18 }
const firstArtifact: ArtifactRecord = { artifact_id: "artifact-review-17", tenant_id: currentRun.tenant_id, project_id: currentRun.project_id, run_id: currentRun.run_id, step_id: currentRun.step_id, revision: 17, content_sha256: "a".repeat(64), input_hash: "b".repeat(64), storage_key: "outputs/first.json", created_at: "2026-08-21T10:00:00Z" }
const latestArtifact: ArtifactRecord = { ...firstArtifact, artifact_id: "artifact-review-primary-18", revision: 18, content_sha256: "c".repeat(64), storage_key: "outputs/latest.json" }
const supportingArtifact: ArtifactRecord = { ...latestArtifact, artifact_id: "artifact-review-z-support-18", content_sha256: "d".repeat(64), storage_key: "outputs/latest-support.json" }
const primaryDocument = { content: "Primaerdokument" }
const supportingDocument = { content: "Unterstuetzender Nachweis", provenance: "local simulated staging" }

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

function gate(artifact: ArtifactRecord = latestArtifact, hash = artifact.content_sha256): readonly GateRead[] {
  return parseGates({ data: [{ tenant_id: currentRun.tenant_id, project_id: currentRun.project_id, run_id: currentRun.run_id, step_id: currentRun.step_id, quality_gate_id: "GATE-4A", quality_gate_run_id: "qgr-4a-evidence", human_gate_id: "GATE-4A", registry_version: "1.0.0", policy_version: "1.0.0", artifact_id: artifact.artifact_id, artifact_sha256: hash, artifact_revision: artifact.revision, result: "passed", summary: "Pruefung bestanden", evidence: { source: "local simulated staging" }, findings: [{ code: "QG_NO_DEVIATION", severity: "info", message: "Keine Abweichung" }], checker_version: "checker-1.0", checked_at: "2026-08-21T10:00:00Z" }] }, currentRun.tenant_id, currentRun.project_id)
}

function data(api: ReturnType<typeof createOperatorApiClient>, gates = gate(), artifacts: readonly ArtifactRecord[] = [firstArtifact, latestArtifact, supportingArtifact], artifact: ArtifactRecord | null = latestArtifact): OperatorWorkspaceData {
  const step: StepRead = { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, runId: currentRun.run_id, stepId: currentRun.step_id, status: "in_progress", blocker: "Freigabe pruefen", nextAction: "Freigabe vorbereiten" }
  return { projectId: currentRun.project_id, project: { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, name: "Review Projekt", customer: "Review GmbH", currentStep: currentRun.step_id, progress: "3 von 8", blockerCount: 0, owner: "Heartweb Admin Operator", nextAction: "Freigabe vorbereiten" }, currentRun, run: { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, runId: currentRun.run_id, stepId: currentRun.step_id, revision: currentRun.expected_revision, status: "in_progress" }, workflow: { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, initialEdges: [], sideflows: [{ stepId: "3b", status: "not_due" }] }, steps: [step], tasks: [], artifacts, gates, context: [], integrations: [], current: { step, gate: gates[0] ?? null, context: null, artifact }, actionClient: api, reload: async (): Promise<void> => undefined }
}

function response(value: unknown): Response { return new Response(JSON.stringify(value), { headers: { "Content-Type": "application/json" } }) }
function encoded(value: object): string { return btoa(JSON.stringify(value)) }
function content(artifact: ArtifactRecord, document: object): ArtifactContentResponse { return { artifact, content_base64: encoded(document) } }
function preview(action: ActionIntent["action"], result: string | number): ActionPreview { return { allowed: true, blockers: [], consequence: { result }, intent: { action, ...currentRun }, preview_hash: `${action}-preview` } }
function confirm(action: ActionIntent["action"], replay = false): ActionConfirmResult { return { canonical: { action }, preview_hash: `${action}-preview`, readback_urls: [], replay } }

type ReviewFixture = { readonly action: ActionIntent["action"]; readonly result: string | number; readonly reload?: () => Promise<void>; readonly gates?: readonly GateRead[]; readonly artifacts?: readonly ArtifactRecord[]; readonly artifact?: ArtifactRecord | null; readonly getContent?: (artifactId: string) => Promise<ArtifactContentResponse> }

function renderReview(fixture: ReviewFixture) {
  const reload = fixture.reload ?? vi.fn(async (): Promise<void> => undefined)
  const artifacts = fixture.artifacts ?? [firstArtifact, latestArtifact, supportingArtifact]
  const getContent = fixture.getContent ?? (async (artifactId: string): Promise<ArtifactContentResponse> => {
    const artifact = artifacts.find((entry) => entry.artifact_id === artifactId)
    if (artifact === undefined) throw new Error(`Unexpected artifact content request: ${artifactId}`)
    return content(artifact, artifact.artifact_id === supportingArtifact.artifact_id ? supportingDocument : primaryDocument)
  })
  const contentRequests: string[] = []
  const fetch: typeof globalThis.fetch = async (input, init) => {
    const url = input.toString()
    const body = typeof init?.body === "string" ? JSON.parse(init.body) : null
    const artifactId = /\/artifacts\/([^/]+)\/content$/.exec(url)?.[1]
    if (artifactId !== undefined) { contentRequests.push(artifactId); return response(await getContent(artifactId)) }
    if (url.endsWith(`/actions/${fixture.action}/preview`)) return response(preview(fixture.action, fixture.result))
    if (url.endsWith(`/actions/${fixture.action}/confirm`)) return response(confirm(fixture.action))
    throw new Error(`Unexpected review request: ${url} ${JSON.stringify(body)}`)
  }
  vi.stubGlobal("fetch", fetch)
  const api = createOperatorApiClient({ baseUrl: "", tenantId: currentRun.tenant_id })
  const view = render(<ReviewWorkspace api={api} data={data(api, fixture.gates, artifacts, fixture.artifact)} onReadback={reload} />)
  return { api, contentRequests, reload, rerender: (nextData: OperatorWorkspaceData): void => view.rerender(<ReviewWorkspace api={api} data={nextData} onReadback={reload} />) }
}

function fillReview(reason: string, instructions: string, sections?: string, constraints?: string): void {
  fireEvent.change(screen.getByLabelText("Begruendung"), { target: { value: reason } })
  fireEvent.change(screen.getByLabelText("Anweisungen"), { target: { value: instructions } })
  if (sections !== undefined) fireEvent.change(screen.getByLabelText("Betroffene Abschnitte"), { target: { value: sections } })
  if (constraints !== undefined) fireEvent.change(screen.getByLabelText("Unveraenderliche Vorgaben"), { target: { value: constraints } })
}

async function expectPayloadBlock(fixture: ReviewFixture): Promise<void> {
  renderReview(fixture)
  expect(await screen.findByRole("alert")).toHaveTextContent("Review-Unterlagen blockiert")
  expect(screen.getByRole("button", { name: "Freigabe vorbereiten" })).toBeDisabled()
}

describe("ReviewWorkspace", () => {
  it("uses data.current.artifact as the primary even when the supporting ID sorts higher, then waits for both exact payloads", async () => {
    const fixture = renderReview({ action: "approve", result: "Freigabe gespeichert" })
    expect(screen.getByRole("button", { name: "Freigabe vorbereiten" })).toBeDisabled()
    expect(await screen.findByRole("region", { name: "Kanonisches Primaerdokument" })).toHaveTextContent("Primaerdokument")
    expect(screen.getByRole("heading", { name: "Exakte Schritt-4-Review-Unterlagen" }).closest(".step4-review-payload")).toBeInTheDocument()
    expect(screen.getByRole("region", { name: "Unterstuetzendes Dokument" })).toHaveTextContent("Unterstuetzender Nachweis")
    expect(screen.getByText("Lokale oder simulierte Nachweisquelle")).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole("button", { name: "Freigabe vorbereiten" })).toBeEnabled())
    expect(fixture.contentRequests).toEqual([latestArtifact.artifact_id, supportingArtifact.artifact_id])
    fireEvent.click(screen.getByRole("button", { name: "Freigabe vorbereiten" }))
    fireEvent.click(await screen.findByRole("button", { name: "Freigabe bestaetigen" }))
    await waitFor(() => expect(fixture.reload).toHaveBeenCalledOnce())
    expect(screen.getByText("Kanonischer Stand aktualisiert")).toBeInTheDocument()
  })

  it("keeps approval disabled while either exact Step 4 payload is still loading", async () => {
    let resolvePrimary: (value: ArtifactContentResponse) => void = () => undefined
    let resolveSupporting: (value: ArtifactContentResponse) => void = () => undefined
    const pendingPrimary = new Promise<ArtifactContentResponse>((resolve) => { resolvePrimary = resolve })
    const pendingSupporting = new Promise<ArtifactContentResponse>((resolve) => { resolveSupporting = resolve })
    renderReview({ action: "approve", result: "Freigabe gespeichert", getContent: async (artifactId) => artifactId === latestArtifact.artifact_id ? pendingPrimary : pendingSupporting })
    expect(screen.getByRole("button", { name: "Freigabe vorbereiten" })).toBeDisabled()
    resolvePrimary(content(latestArtifact, primaryDocument))
    expect(screen.getByRole("button", { name: "Freigabe vorbereiten" })).toBeDisabled()
    resolveSupporting(content(supportingArtifact, supportingDocument))
    await waitFor(() => expect(screen.getByRole("button", { name: "Freigabe vorbereiten" })).toBeEnabled())
  })

  it("blocks approval for missing, multiple, cross-bound, malformed, and non-object Step 4 payloads", async () => {
    await expectPayloadBlock({ action: "approve", result: "Freigabe gespeichert", artifacts: [firstArtifact, latestArtifact] })
    cleanup()
    await expectPayloadBlock({ action: "approve", result: "Freigabe gespeichert", artifacts: [firstArtifact, latestArtifact, supportingArtifact, { ...supportingArtifact, artifact_id: "artifact-review-second-support-18" }] })
    cleanup()
    await expectPayloadBlock({ action: "approve", result: "Freigabe gespeichert", getContent: async () => content({ ...latestArtifact, project_id: "other-project" }, primaryDocument) })
    cleanup()
    await expectPayloadBlock({ action: "approve", result: "Freigabe gespeichert", getContent: async () => ({ artifact: latestArtifact, content_base64: "not-base64" }) })
    cleanup()
    await expectPayloadBlock({ action: "approve", result: "Freigabe gespeichert", getContent: async () => ({ artifact: latestArtifact, content_base64: btoa("{") }) })
    cleanup()
    await expectPayloadBlock({ action: "approve", result: "Freigabe gespeichert", getContent: async () => ({ artifact: latestArtifact, content_base64: btoa("\xff") }) })
    cleanup()
    await expectPayloadBlock({ action: "approve", result: "Freigabe gespeichert", getContent: async () => ({ artifact: latestArtifact, content_base64: btoa("[]") }) })
  })

  it("does not let a stale primary response enable approval for a newer canonical artifact", async () => {
    const nextPrimary: ArtifactRecord = { ...latestArtifact, artifact_id: "artifact-review-primary-19", content_sha256: "e".repeat(64), revision: 19 }
    const nextSupporting: ArtifactRecord = { ...supportingArtifact, artifact_id: "artifact-review-z-support-19", content_sha256: "f".repeat(64), revision: 19 }
    let resolveStale: (value: ArtifactContentResponse) => void = () => undefined
    const stale = new Promise<ArtifactContentResponse>((resolve) => { resolveStale = resolve })
    const fixture = renderReview({ action: "approve", result: "Freigabe gespeichert", getContent: async (artifactId) => {
      if (artifactId === latestArtifact.artifact_id) return stale
      if (artifactId === nextPrimary.artifact_id) return content(nextPrimary, { content: "Aktuelles Primaerdokument" })
      if (artifactId === nextSupporting.artifact_id) return content(nextSupporting, supportingDocument)
      return content(supportingArtifact, supportingDocument)
    } })
    fixture.rerender(data(fixture.api, gate(nextPrimary), [nextPrimary, nextSupporting], nextPrimary))
    expect(screen.getByRole("button", { name: "Freigabe vorbereiten" })).toBeDisabled()
    await waitFor(() => expect(screen.getByRole("button", { name: "Freigabe vorbereiten" })).toBeEnabled())
    resolveStale(content(latestArtifact, { content: "Veraltetes Primaerdokument" }))
    await stale
    expect(screen.queryByText("Veraltetes Primaerdokument")).toBeNull()
  })

  it("Given a non-string consequence result, when an approval preview is ready, then the operator sees the approved action-consequence fallback", async () => {
    renderReview({ action: "approve", result: 17 })
    await waitFor(() => expect(screen.getByRole("button", { name: "Freigabe vorbereiten" })).toBeEnabled())
    fireEvent.click(screen.getByRole("button", { name: "Freigabe vorbereiten" }))
    expect(await screen.findByText("Folge der Aktion wurde vorbereitet.")).toBeInTheDocument()
    expect(screen.queryByText(/Serverfolge/)).toBeNull()
  })

  it("disables approval for missing or hash-mismatched gate evidence", () => {
    renderReview({ action: "approve", result: "Freigabe gespeichert", gates: gate(latestArtifact, "0".repeat(64)) })
    expect(screen.getByRole("button", { name: "Freigabe vorbereiten" })).toBeDisabled()
  })

  it("previews and confirms rejection and revision requests with their German labels", async () => {
    const reject = renderReview({ action: "reject", result: "Ablehnung gespeichert" })
    fireEvent.change(screen.getByLabelText("Entscheidung waehlen"), { target: { value: "reject" } }); fillReview("Grund", "Korrektur", "Einleitung", "Marke")
    fireEvent.click(screen.getByRole("button", { name: "Vorschau fuer Ablehnung erstellen" }))
    fireEvent.click(await screen.findByRole("button", { name: "Ablehnung bestaetigen" }))
    await waitFor(() => expect(reject.reload).toHaveBeenCalledOnce())
    cleanup()
    const revision = renderReview({ action: "request-revision", result: "Revision gespeichert" })
    fireEvent.change(screen.getByLabelText("Entscheidung waehlen"), { target: { value: "request-revision" } }); fillReview("Grund", "Korrektur", "Einleitung", "Marke")
    fireEvent.click(screen.getByRole("button", { name: "Vorschau fuer Revision erstellen" }))
    fireEvent.click(await screen.findByRole("button", { name: "Revision anfordern bestaetigen" }))
    await waitFor(() => expect(revision.reload).toHaveBeenCalledOnce())
  })

  it("requires typed request-input, escalation, and waiver fields before previews", () => {
    renderReview({ action: "approve", result: "Freigabe gespeichert" })
    fireEvent.change(screen.getByLabelText("Entscheidung waehlen"), { target: { value: "request-input" } })
    expect(screen.getByRole("button", { name: "Vorschau fuer Eingabe erstellen" })).toBeDisabled()
    fireEvent.change(screen.getByLabelText("Entscheidung waehlen"), { target: { value: "escalate" } })
    expect(screen.getByRole("button", { name: "Vorschau fuer Eskalation erstellen" })).toBeDisabled()
    fireEvent.change(screen.getByLabelText("Entscheidung waehlen"), { target: { value: "request-waiver" } })
    expect(screen.getByRole("button", { name: "Vorschau fuer Ausnahme erstellen" })).toBeDisabled()
  })

  it.each([
    ["request-input", "Eingabe anfordern", "Vorschau fuer Eingabe erstellen", "Eingabe anfordern bestaetigen"],
    ["escalate", "Eskalation vorbereiten", "Vorschau fuer Eskalation erstellen", "Eskalation bestaetigen"],
    ["request-waiver", "Ausnahme anfragen", "Vorschau fuer Ausnahme erstellen", "Ausnahmeanfrage bestaetigen"],
  ] as const)("previews, confirms, and reads back %s with its required operator input", async (action, selection, previewButton, confirmButton) => {
    const fixture = renderReview({ action, result: `${action} gespeichert` })
    fireEvent.change(screen.getByLabelText("Entscheidung waehlen"), { target: { value: action } })
    fireEvent.change(screen.getByLabelText("Begruendung"), { target: { value: "Operatorische Begruendung" } })
    if (action === "escalate") {
      fireEvent.change(screen.getByLabelText("Mindestens zwei Optionen"), { target: { value: "Option A\nOption B" } })
      fireEvent.change(screen.getByLabelText("Auswirkungen"), { target: { value: "Auswirkung pruefen" } })
    } else {
      fireEvent.change(screen.getByLabelText(action === "request-waiver" ? "Pruefanweisung fuer Ausnahme" : "Anweisungen"), { target: { value: "Naechsten kanonischen Schritt pruefen" } })
    }
    fireEvent.click(screen.getByRole("button", { name: previewButton }))
    expect(await screen.findByText(`${action} gespeichert`)).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: confirmButton }))
    await waitFor(() => expect(fixture.reload).toHaveBeenCalledOnce())
    expect(screen.getByText("Kanonischer Stand aktualisiert")).toBeInTheDocument()
  })

  it("clears stale confirmation and shows replay only after the reload resolves", async () => {
    const reload = vi.fn(async (): Promise<void> => undefined)
    const fetch: typeof globalThis.fetch = async (input) => {
      if (input.toString().endsWith("/actions/approve/preview")) return response(preview("approve", "Freigabe gespeichert"))
      if (input.toString().endsWith("/actions/approve/confirm")) return new Response(JSON.stringify({ message: "Kanonischer Stand ist veraltet." }), { status: 409, headers: { "Content-Type": "application/json" } })
      const artifactId = /\/artifacts\/([^/]+)\/content$/.exec(input.toString())?.[1]
      if (artifactId === latestArtifact.artifact_id) return response(content(latestArtifact, primaryDocument))
      if (artifactId === supportingArtifact.artifact_id) return response(content(supportingArtifact, supportingDocument))
      throw new Error(`Unexpected review request: ${input.toString()}`)
    }
    vi.stubGlobal("fetch", fetch)
    const api = createOperatorApiClient({ baseUrl: "", tenantId: currentRun.tenant_id })
    render(<ReviewWorkspace api={api} data={data(api)} onReadback={reload} />)
    await waitFor(() => expect(screen.getByRole("button", { name: "Freigabe vorbereiten" })).toBeEnabled())
    fireEvent.click(screen.getByRole("button", { name: "Freigabe vorbereiten" }))
    fireEvent.click(await screen.findByRole("button", { name: "Freigabe bestaetigen" }))
    expect(await screen.findByText("Kanonischer Stand wurde aktualisiert. Bitte Vorschau erneut erstellen.")).toBeInTheDocument()
    expect(screen.queryByText("Kanonischer Stand aktualisiert")).toBeNull()
  })
})
