import { afterEach, describe, expect, it, vi } from "vitest"
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import { createOperatorApiClient } from "../api/client"
import { parseGates } from "../api/readModels"
import type { CurrentRun, StepRead } from "../api/readModels"
import type { ActionConfirmResult, ActionIntent, ActionPreview, ArtifactRecord } from "../generated/api-types"
import type { OperatorWorkspaceData } from "./useOperatorWorkspace"
import { ReviewWorkspace } from "./ReviewWorkspace"

const currentRun: CurrentRun = { tenant_id: "tenant-review", project_id: "project-review", run_id: "run-review", step_id: "1b", expected_revision: 17 }
const firstArtifact: ArtifactRecord = { artifact_id: "artifact-review-17", tenant_id: currentRun.tenant_id, project_id: currentRun.project_id, run_id: currentRun.run_id, step_id: currentRun.step_id, revision: 17, content_sha256: "a".repeat(64), input_hash: "b".repeat(64), storage_key: "outputs/first.md", created_at: "2026-08-21T10:00:00Z" }
const latestArtifact: ArtifactRecord = { ...firstArtifact, artifact_id: "artifact-review-18", revision: 18, content_sha256: "c".repeat(64), storage_key: "outputs/latest.md" }

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

function gate(hash = latestArtifact.content_sha256) {
  return parseGates({ data: [{ tenant_id: currentRun.tenant_id, project_id: currentRun.project_id, run_id: currentRun.run_id, step_id: currentRun.step_id, quality_gate_id: "GATE-1B", quality_gate_run_id: "qgr-1b-evidence", artifact_id: latestArtifact.artifact_id, artifact_sha256: hash, artifact_revision: latestArtifact.revision, result: "passed", summary: "Pruefung bestanden", evidence: { source: "validiert" }, findings: ["Keine Abweichung"], checker_version: "checker-1.0", checked_at: "2026-08-21T10:00:00Z" }] }, currentRun.tenant_id, currentRun.project_id)
}

function data(api: ReturnType<typeof createOperatorApiClient>, gates = gate()): OperatorWorkspaceData {
  const step: StepRead = { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, runId: currentRun.run_id, stepId: currentRun.step_id, status: "in_progress", blocker: "Freigabe pruefen", nextAction: "Freigabe vorbereiten" }
  return { projectId: currentRun.project_id, project: { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, name: "Review Projekt", customer: "Review GmbH", currentStep: currentRun.step_id, progress: "3 von 8", blockerCount: 0, owner: "Heartweb Admin Operator", nextAction: "Freigabe vorbereiten" }, currentRun, run: { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, runId: currentRun.run_id, stepId: currentRun.step_id, revision: currentRun.expected_revision, status: "in_progress" }, workflow: { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, initialEdges: [], sideflows: [{ stepId: "3b", status: "not_due" }] }, steps: [step], tasks: [], artifacts: [firstArtifact, latestArtifact], gates, context: [], integrations: [], current: { step, gate: gates[0] ?? null, context: null, artifact: latestArtifact }, actionClient: api, reload: async (): Promise<void> => undefined }
}

function response(value: unknown): Response { return new Response(JSON.stringify(value), { headers: { "Content-Type": "application/json" } }) }
function preview(action: ActionIntent["action"], result: string): ActionPreview { return { allowed: true, blockers: [], consequence: { result }, intent: { action, ...currentRun }, preview_hash: `${action}-preview` } }
function confirm(action: ActionIntent["action"], replay = false): ActionConfirmResult { return { canonical: { action }, preview_hash: `${action}-preview`, readback_urls: [], replay } }

function renderReview(action: ActionIntent["action"], result: string, reload = vi.fn(async (): Promise<void> => undefined), gates = gate(), replay = false): { readonly reload: ReturnType<typeof vi.fn> } {
  const fetch: typeof globalThis.fetch = async (input, init) => {
    const url = input.toString()
    const body = typeof init?.body === "string" ? JSON.parse(init.body) : null
    if (url.endsWith(`/actions/${action}/preview`)) return response(preview(action, result))
    if (url.endsWith(`/actions/${action}/confirm`)) return response(confirm(action, replay))
    throw new Error(`Unexpected review request: ${url} ${JSON.stringify(body)}`)
  }
  vi.stubGlobal("fetch", fetch)
  const api = createOperatorApiClient({ baseUrl: "", tenantId: currentRun.tenant_id })
  render(<ReviewWorkspace api={api} data={data(api, gates)} onReadback={reload} />)
  return { reload }
}

function fillReview(reason: string, instructions: string, sections?: string, constraints?: string): void {
  fireEvent.change(screen.getByLabelText("Begruendung"), { target: { value: reason } })
  fireEvent.change(screen.getByLabelText("Anweisungen"), { target: { value: instructions } })
  if (sections !== undefined) fireEvent.change(screen.getByLabelText("Betroffene Abschnitte"), { target: { value: sections } })
  if (constraints !== undefined) fireEvent.change(screen.getByLabelText("Unveraenderliche Vorgaben"), { target: { value: constraints } })
}

describe("ReviewWorkspace", () => {
  it("uses the highest exact artifact and gate binding for approval then waits for canonical readback", async () => {
    const { reload } = renderReview("approve", "Freigabe gespeichert")
    expect(screen.getByText("latest.md, Revision 18")).toBeInTheDocument()
    expect(screen.getByText("source: validiert")).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: "Freigabe vorbereiten" }))
    expect(await screen.findByRole("button", { name: "Freigabe bestaetigen" })).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: "Freigabe bestaetigen" }))
    await waitFor(() => expect(reload).toHaveBeenCalledOnce())
    expect(screen.getByText("Kanonischer Stand aktualisiert")).toBeInTheDocument()
  })

  it("disables approval for missing or hash-mismatched gate evidence", () => {
    const api = createOperatorApiClient({ baseUrl: "", tenantId: currentRun.tenant_id })
    render(<ReviewWorkspace api={api} data={data(api, gate("d".repeat(64)))} onReadback={async (): Promise<void> => undefined} />)
    expect(screen.getByRole("button", { name: "Freigabe vorbereiten" })).toBeDisabled()
  })

  it("previews and confirms rejection and revision requests with their German labels", async () => {
    const reject = renderReview("reject", "Ablehnung gespeichert")
    fireEvent.click(screen.getByRole("button", { name: "Ablehnung vorbereiten" })); fillReview("Grund", "Korrektur", "Einleitung", "Marke")
    fireEvent.click(screen.getByRole("button", { name: "Vorschau fuer Ablehnung erstellen" }))
    fireEvent.click(await screen.findByRole("button", { name: "Ablehnung bestaetigen" }))
    await waitFor(() => expect(reject.reload).toHaveBeenCalledOnce())
    cleanup()
    const revision = renderReview("request-revision", "Revision gespeichert")
    fireEvent.click(screen.getByRole("button", { name: "Revision anfordern" })); fillReview("Grund", "Korrektur", "Einleitung", "Marke")
    fireEvent.click(screen.getByRole("button", { name: "Vorschau fuer Revision erstellen" }))
    fireEvent.click(await screen.findByRole("button", { name: "Revision anfordern bestaetigen" }))
    await waitFor(() => expect(revision.reload).toHaveBeenCalledOnce())
  })

  it("requires typed request-input, escalation, and waiver fields before previews", () => {
    const api = createOperatorApiClient({ baseUrl: "", tenantId: currentRun.tenant_id })
    render(<ReviewWorkspace api={api} data={data(api)} onReadback={async (): Promise<void> => undefined} />)
    fireEvent.click(screen.getByRole("button", { name: "Eingabe anfordern" }))
    expect(screen.getByRole("button", { name: "Vorschau fuer Eingabe erstellen" })).toBeDisabled()
    fireEvent.click(screen.getByRole("button", { name: "Eskalation vorbereiten" }))
    expect(screen.getByRole("button", { name: "Vorschau fuer Eskalation erstellen" })).toBeDisabled()
    fireEvent.click(screen.getByRole("button", { name: "Ausnahme anfragen" }))
    expect(screen.getByRole("button", { name: "Vorschau fuer Ausnahme erstellen" })).toBeDisabled()
  })

  it.each([
    ["request-input", "Eingabe anfordern", "Vorschau fuer Eingabe erstellen", "Eingabe anfordern bestaetigen"],
    ["escalate", "Eskalation vorbereiten", "Vorschau fuer Eskalation erstellen", "Eskalation bestaetigen"],
    ["request-waiver", "Ausnahme anfragen", "Vorschau fuer Ausnahme erstellen", "Ausnahmeanfrage bestaetigen"],
  ] as const)("previews, confirms, and reads back %s with its required operator input", async (action, selection, previewButton, confirmButton) => {
    // Given: an allowed canonical outcome action with exact artifact and gate evidence.
    const { reload } = renderReview(action, `${action} gespeichert`)
    fireEvent.click(screen.getByRole("button", { name: selection }))
    fireEvent.change(screen.getByLabelText("Begruendung"), { target: { value: "Operatorische Begruendung" } })
    if (action === "escalate") {
      fireEvent.change(screen.getByLabelText("Mindestens zwei Optionen"), { target: { value: "Option A\nOption B" } })
      fireEvent.change(screen.getByLabelText("Auswirkungen"), { target: { value: "Auswirkung pruefen" } })
    } else {
      fireEvent.change(screen.getByLabelText(action === "request-waiver" ? "Pruefanweisung fuer Ausnahme" : "Anweisungen"), { target: { value: "Naechsten kanonischen Schritt pruefen" } })
    }

    // When: the operator creates and confirms the action preview.
    fireEvent.click(screen.getByRole("button", { name: previewButton }))
    expect(await screen.findByText(`${action} gespeichert`)).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: confirmButton }))

    // Then: canonical readback completes for every supported review outcome.
    await waitFor(() => expect(reload).toHaveBeenCalledOnce())
    expect(screen.getByText("Kanonischer Stand aktualisiert")).toBeInTheDocument()
  })

  it("clears stale confirmation and shows replay only after the reload resolves", async () => {
    const reload = vi.fn(async (): Promise<void> => undefined)
    const fetch: typeof globalThis.fetch = async (input) => {
      if (input.toString().endsWith("/actions/approve/preview")) return response(preview("approve", "Freigabe gespeichert"))
      return new Response(JSON.stringify({ message: "Kanonischer Stand ist veraltet." }), { status: 409, headers: { "Content-Type": "application/json" } })
    }
    vi.stubGlobal("fetch", fetch)
    const api = createOperatorApiClient({ baseUrl: "", tenantId: currentRun.tenant_id })
    render(<ReviewWorkspace api={api} data={data(api)} onReadback={reload} />)
    fireEvent.click(screen.getByRole("button", { name: "Freigabe vorbereiten" }))
    fireEvent.click(await screen.findByRole("button", { name: "Freigabe bestaetigen" }))
    expect(await screen.findByText("Kanonischer Stand wurde aktualisiert. Bitte Vorschau erneut erstellen.")).toBeInTheDocument()
    expect(screen.queryByText("Kanonischer Stand aktualisiert")).toBeNull()
  })
})
