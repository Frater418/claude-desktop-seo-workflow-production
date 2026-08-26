import { afterEach, describe, expect, it, vi } from "vitest"
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import { createOperatorApiClient, OperatorApiError } from "../api/client"
import type { OperatorApiClient } from "../api/client"
import type { CurrentRun, StepRead } from "../api/readModels"
import type { ActionConfirmResult, ActionIntent, ActionPreview } from "../generated/api-types"
import type { OperatorWorkspaceData } from "./useOperatorWorkspace"
import { WorkflowWorkspace } from "./WorkflowWorkspace"

type ActionClient = Pick<OperatorApiClient, "previewAdminAction" | "confirmAdminAction">
type WorkflowData = OperatorWorkspaceData & { readonly actionClient: ActionClient; readonly reload: () => Promise<void> }
type Deferred = { readonly promise: Promise<void>; readonly resolve: () => void }

const currentRun: CurrentRun = { tenant_id: "tenant-eindeutig", project_id: "project-eindeutig", run_id: "run-vorgaenger-20260821", step_id: "1b", expected_revision: 17 }

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function deferred(): Deferred {
  let release = (): void => undefined
  const promise = new Promise<void>((resolve) => { release = resolve })
  return { promise, resolve: release }
}

function data(actionClient: ActionClient, reload: () => Promise<void>): WorkflowData {
  const step: StepRead = { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, runId: currentRun.run_id, stepId: currentRun.step_id, status: "completed", blocker: "Keine", nextAction: "Naechsten Schritt starten" }
  return {
    projectId: currentRun.project_id,
    project: { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, name: "Pflegedienst Eindeutig", customer: "Eindeutig GmbH", currentStep: currentRun.step_id, progress: "3 von 8 Schritten", blockerCount: 0, owner: "Heartweb Admin Operator", nextAction: "Naechsten Schritt starten" },
    currentRun,
    run: { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, runId: currentRun.run_id, stepId: currentRun.step_id, revision: currentRun.expected_revision, status: "completed" },
    workflow: { tenantId: currentRun.tenant_id, projectId: currentRun.project_id, initialEdges: [], sideflows: [{ stepId: "3b", status: "not_due" }] },
    steps: [step], tasks: [], artifacts: [], gates: [], context: [], integrations: [], current: { step, gate: null, context: null, artifact: null }, actionClient, reload,
  }
}

function preview(overrides: Partial<ActionPreview> = {}): ActionPreview {
  return {
    allowed: true,
    blockers: [],
    consequence: { result: "Der Nachfolger wird kanonisch gestartet." },
    intent: { action: "start", tenant_id: currentRun.tenant_id, project_id: currentRun.project_id, run_id: "run-nachfolger-20260821", step_id: "1c", expected_revision: 1 },
    preview_hash: "a".repeat(64),
    ...overrides,
  }
}

function confirmation(replay = false): ActionConfirmResult {
  return { canonical: {}, preview_hash: "a".repeat(64), readback_urls: [], replay }
}

describe("WorkflowWorkspace actions", () => {
  it("previews start with the canonical predecessor binding and confirms the original intent", async () => {
    const calls: { url: string; readonly body: unknown }[] = []
    const fetch: typeof globalThis.fetch = async (input, init) => {
      const url = input.toString()
      const body = typeof init?.body === "string" ? JSON.parse(init.body) : null
      calls.push({ url, body })
      if (url.endsWith("/actions/start/preview")) return new Response(JSON.stringify(preview()), { headers: { "Content-Type": "application/json" } })
      return new Response(JSON.stringify(confirmation()), { headers: { "Content-Type": "application/json" } })
    }
    vi.stubGlobal("fetch", fetch)
    const actionClient = createOperatorApiClient({ baseUrl: "", tenantId: currentRun.tenant_id })
    const reload = vi.fn(async (): Promise<void> => undefined)

    render(<WorkflowWorkspace data={data(actionClient, reload)} />)

    expect(screen.queryByRole("button", { name: "Nächsten Schritt anlegen" })).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: "Folgeschritt prüfen" }))
    await screen.findByText("Der Nachfolger wird kanonisch gestartet.")
    fireEvent.click(screen.getByRole("button", { name: "Nächsten Schritt anlegen" }))
    await waitFor(() => expect(reload).toHaveBeenCalledOnce())

    const expectedIntent: ActionIntent = { action: "start", tenant_id: "tenant-eindeutig", project_id: "project-eindeutig", run_id: "run-vorgaenger-20260821", step_id: "1b", expected_revision: 17 }
    expect(calls[0]).toMatchObject({ url: "/v1/tenants/tenant-eindeutig/projects/project-eindeutig/actions/start/preview", body: expectedIntent })
    expect(calls[1]).toMatchObject({ url: "/v1/tenants/tenant-eindeutig/projects/project-eindeutig/actions/start/confirm", body: { confirmed: true, intent: expectedIntent, preview_hash: "a".repeat(64) } })
    expect(calls.some((call) => call.url.includes("/commands/"))).toBe(false)
  })

  it("shows the exact blocker remediation and never confirms a blocked preview", async () => {
    const previewAdminAction = vi.fn(async (): Promise<ActionPreview> => preview({ allowed: false, blockers: [{ code: "ERR_GATE_REQUIRED", message: "Die Maschinenpruefung fehlt.", remediation: "Maschinenpruefung abschliessen und erneut versuchen." }] }))
    const confirmAdminAction = vi.fn(async (): Promise<ActionConfirmResult> => confirmation())

    render(<WorkflowWorkspace data={data({ previewAdminAction, confirmAdminAction }, async (): Promise<void> => undefined)} />)
    fireEvent.click(screen.getByRole("button", { name: "Folgeschritt prüfen" }))

    expect(await screen.findByText("Maschinenpruefung abschliessen und erneut versuchen.")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Nächsten Schritt anlegen" })).toBeNull()
    expect(confirmAdminAction).not.toHaveBeenCalled()
  })

  it("clears a stale confirmation, reloads, and requires a fresh preview", async () => {
    const previewAdminAction = vi.fn(async (): Promise<ActionPreview> => preview())
    const confirmAdminAction = vi.fn(async (): Promise<ActionConfirmResult> => { throw new OperatorApiError({ kind: "http", status: 409, message: "Kanonischer Stand ist veraltet." }) })
    const reload = vi.fn(async (): Promise<void> => undefined)

    render(<WorkflowWorkspace data={data({ previewAdminAction, confirmAdminAction }, reload)} />)
    fireEvent.click(screen.getByRole("button", { name: "Folgeschritt prüfen" }))
    await screen.findByRole("button", { name: "Nächsten Schritt anlegen" })
    fireEvent.click(screen.getByRole("button", { name: "Nächsten Schritt anlegen" }))

    expect(await screen.findByText("Kanonischer Stand wurde aktualisiert. Bitte Vorschau erneut erstellen.")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Nächsten Schritt anlegen" })).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: "Folgeschritt prüfen" }))
    await screen.findByRole("button", { name: "Nächsten Schritt anlegen" })
    expect(previewAdminAction).toHaveBeenCalledTimes(2)
    expect(confirmAdminAction).toHaveBeenCalledTimes(1)
  })

  it("renders canonical replay only after the awaited workspace reload", async () => {
    const reloadGate = deferred()
    const previewAdminAction = vi.fn(async (): Promise<ActionPreview> => preview())
    const confirmAdminAction = vi.fn(async (): Promise<ActionConfirmResult> => confirmation(true))
    const reload = vi.fn(() => reloadGate.promise)

    render(<WorkflowWorkspace data={data({ previewAdminAction, confirmAdminAction }, reload)} />)
    fireEvent.click(screen.getByRole("button", { name: "Folgeschritt prüfen" }))
    await screen.findByRole("button", { name: "Nächsten Schritt anlegen" })
    fireEvent.click(screen.getByRole("button", { name: "Nächsten Schritt anlegen" }))

    expect(await screen.findByText("Kanonischer Stand wird geladen.")).toBeInTheDocument()
    expect(screen.queryByText("Kanonische Wiederholung bestaetigt.")).toBeNull()
    reloadGate.resolve()
    expect(await screen.findByText("Kanonische Wiederholung bestaetigt.")).toBeInTheDocument()
  })
})
