import { afterEach, describe, expect, it, vi } from "vitest"
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import { createOperatorApiClient } from "../api/client"
import type { CurrentRun } from "../api/readModels"
import { IntakeWorkspace } from "./IntakeWorkspace"

type Deferred<T> = { readonly promise: Promise<T>; readonly resolve: (value: T) => void }
type Fixture = { readonly client: ReturnType<typeof createOperatorApiClient>; readonly acceptBodies: string[] }

const stepZero: CurrentRun = { tenant_id: "tenant-eindeutig", project_id: "projekt-neu", run_id: "lauf-null", step_id: "0", expected_revision: 1 }
const reviewed = { title: "Pflege Alpha aufnehmen", tenant_id: "tenant-eindeutig", project_id: "projekt-neu", project_name: "Pflegedienst Alpha", project_v2: { version: 2 } }

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function deferred<T>(): Deferred<T> {
  let release = (_value: T): void => undefined
  const promise = new Promise<T>((resolve) => { release = resolve })
  return { promise, resolve: release }
}

function preview(overrides: Partial<{ readonly reviewed: typeof reviewed | { readonly title: null; readonly tenant_id: null; readonly project_id: null; readonly project_name: null; readonly project_v2: null }; readonly missing_fields: readonly string[]; readonly eligible: boolean; readonly preview_hash: string; readonly source_sha256: string }> = {}): object {
  return { data: { reviewed, missing_fields: [], eligible: true, preview_hash: "a".repeat(64), source_sha256: "b".repeat(64), previewed_at: "2026-08-21T10:00:00Z", ...overrides } }
}

function fixture(previews: readonly object[]): Fixture {
  const acceptBodies: string[] = []
  let previewIndex = 0
  const fetch: typeof globalThis.fetch = async (input, init) => {
    const url = input.toString()
    if (url.endsWith("/intake/preview")) return new Response(JSON.stringify(previews[previewIndex++]), { headers: { "Content-Type": "application/json" } })
    if (url.endsWith("/intake/accept")) {
      if (typeof init?.body === "string") acceptBodies.push(init.body)
      return new Response(JSON.stringify({ data: { tenant_id: "tenant-eindeutig", project_id: "projekt-neu" } }), { headers: { "Content-Type": "application/json" } })
    }
    return new Response("{}", { status: 500, headers: { "Content-Type": "application/json" } })
  }
  vi.stubGlobal("fetch", fetch)
  return { client: createOperatorApiClient({ baseUrl: "", tenantId: "tenant-eindeutig" }), acceptBodies }
}

async function previewMarkdown(markdown: string): Promise<void> {
  fireEvent.change(screen.getByLabelText("Markdown-Briefing"), { target: { value: markdown } })
  fireEvent.click(screen.getByRole("button", { name: "Project V2 erstellen" }))
  await screen.findByRole("heading", { name: "Project V2 prüfen" })
}

async function confirmDraft(): Promise<void> {
  fireEvent.click(screen.getByRole("button", { name: "Vollständigen Project-V2-Entwurf öffnen" }))
  await screen.findByRole("dialog", { name: "Project V2 prüfen" })
  fireEvent.click(screen.getByRole("button", { name: "Schließen" }))
  fireEvent.click(screen.getByRole("checkbox", { name: "Ich habe den vollständigen Project-V2-Entwurf geprüft." }))
}

describe("IntakeWorkspace", () => {
  it("renders every canonical preview field without creating a local correction", async () => {
    // Given: a complete canonical server preview.
    const { client } = fixture([preview()])
    render(<IntakeWorkspace api={client} onAccepted={async (): Promise<CurrentRun> => stepZero} />)

    // When: Markdown is previewed.
    await previewMarkdown("# Pflege Alpha aufnehmen")

    // Then: the server-reviewed title, identities, Project V2, eligibility, and missing fields are shown.
    expect(screen.getByText("Pflege Alpha aufnehmen")).toBeInTheDocument()
    expect(screen.getByText("tenant-eindeutig")).toBeInTheDocument()
    expect(screen.getByText("projekt-neu")).toBeInTheDocument()
    expect(screen.getByText("Pflegedienst Alpha")).toBeInTheDocument()
    expect(screen.getByText("Schema-validierter Entwurf vorhanden")).toBeInTheDocument()
    expect(screen.getByText("Entwurf vollständig")).toBeInTheDocument()
    expect(screen.getByText("Keine fehlenden Angaben.")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Vollständigen Project-V2-Entwurf öffnen" })).toBeEnabled()
  })

  it("lists all server-reported missing fields and blocks an ineligible acceptance", async () => {
    // Given: a preview whose canonical review has every required field missing.
    const missing = { title: null, tenant_id: null, project_id: null, project_name: null, project_v2: null }
    const { client } = fixture([preview({ reviewed: missing, missing_fields: ["title", "tenant_id", "project_id", "project_name", "project_v2"], eligible: false })])
    render(<IntakeWorkspace api={client} onAccepted={async (): Promise<CurrentRun> => stepZero} />)

    // When: the source is previewed.
    await previewMarkdown("Unvollstaendig")

    // Then: every missing canonical field is visible and acceptance is disabled.
    for (const field of ["title", "tenant_id", "project_id", "project_name", "project_v2"]) expect(screen.getByText(field)).toBeInTheDocument()
    expect(screen.getByText("Angaben fehlen")).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Projektanlage noch gesperrt" })).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Projekt anlegen und Schritt 0 öffnen" })).toBeNull()
  })

  it("invalidates a stale preview and sends the exact latest server review and hashes", async () => {
    // Given: two distinct canonical previews for two Markdown sources.
    const secondReview = { ...reviewed, title: "Pflege Beta aufnehmen", project_id: "projekt-beta", project_name: "Pflegedienst Beta" }
    const { client, acceptBodies } = fixture([preview(), preview({ reviewed: secondReview, preview_hash: "c".repeat(64), source_sha256: "d".repeat(64) })])
    const onAccepted = vi.fn(async (): Promise<CurrentRun> => stepZero)
    render(<IntakeWorkspace api={client} onAccepted={onAccepted} />)
    await previewMarkdown("# Erste Quelle")

    // When: the source changes and the operator creates a fresh preview before accepting.
    fireEvent.change(screen.getByLabelText("Markdown-Briefing"), { target: { value: "# Zweite Quelle" } })
    expect(screen.getByRole("button", { name: "Projekt anlegen und Schritt 0 öffnen" })).toBeDisabled()
    fireEvent.click(screen.getByRole("button", { name: "Project V2 erstellen" }))
    await screen.findByText("Pflege Beta aufnehmen")
    await confirmDraft()
    fireEvent.click(screen.getByRole("button", { name: "Projekt anlegen und Schritt 0 öffnen" }))

    // Then: acceptance binds only the latest source, review, and hash values.
    await waitFor(() => expect(onAccepted).toHaveBeenCalledWith("projekt-neu"))
    expect(JSON.parse(acceptBodies[0] ?? "{}")).toEqual({ confirmed: true, markdown: "# Zweite Quelle", preview_hash: "c".repeat(64), source_sha256: "d".repeat(64), reviewed: secondReview })
  })

  it("waits for the selected project reload before confirming Step 0 readiness", async () => {
    // Given: acceptance succeeds while canonical project selection is still pending.
    const reload = deferred<CurrentRun>()
    const { client } = fixture([preview()])
    render(<IntakeWorkspace api={client} onAccepted={async (): Promise<CurrentRun> => reload.promise} />)
    await previewMarkdown("# Pflege Alpha aufnehmen")

    // When: the operator accepts the reviewed source.
    await confirmDraft()
    fireEvent.click(screen.getByRole("button", { name: "Projekt anlegen und Schritt 0 öffnen" }))

    // Then: no readiness claim appears before the canonical Step 0 reload completes.
    expect(await screen.findByText("Der Kundenordner wird angelegt und Schritt 0 wird geladen.")).toBeInTheDocument()
    expect(screen.queryByText("Projekt angelegt. Schritt 0 ist bereit.")).toBeNull()
    reload.resolve(stepZero)
    expect(await screen.findByText("Projekt angelegt. Schritt 0 ist bereit.")).toBeInTheDocument()
  })

  it("withholds readiness when the canonical project run is not Step 0", async () => {
    // Given: acceptance selects a project whose canonical run remains in a later step.
    const laterRun: CurrentRun = { ...stepZero, step_id: "1" }
    const { client } = fixture([preview()])
    render(<IntakeWorkspace api={client} onAccepted={async (): Promise<CurrentRun> => laterRun} />)
    await previewMarkdown("# Pflege Alpha aufnehmen")

    // When: the accepted project reload completes.
    await confirmDraft()
    fireEvent.click(screen.getByRole("button", { name: "Projekt anlegen und Schritt 0 öffnen" }))

    // Then: only the canonical-step remediation is presented.
    expect(await screen.findByText("Das Projekt wurde angelegt, aber der kanonische Projektlauf ist nicht in Schritt 0.")).toBeInTheDocument()
    expect(screen.queryByText("Projekt angelegt. Schritt 0 ist bereit.")).toBeNull()
  })

  it("shows a canonical reload failure without reporting readiness", async () => {
    // Given: acceptance succeeds but the selected project cannot be reloaded.
    const { client } = fixture([preview()])
    render(<IntakeWorkspace api={client} onAccepted={async (): Promise<CurrentRun> => Promise.reject(new Error("Kanonischer Readback fehlgeschlagen."))} />)
    await previewMarkdown("# Pflege Alpha aufnehmen")

    // When: the operator accepts the reviewed source.
    await confirmDraft()
    fireEvent.click(screen.getByRole("button", { name: "Projekt anlegen und Schritt 0 öffnen" }))

    // Then: readiness stays absent and acceptance remains disabled.
    expect(await screen.findByText("Kanonischer Readback fehlgeschlagen.")).toBeInTheDocument()
    expect(screen.queryByText("Projekt angelegt. Schritt 0 ist bereit.")).toBeNull()
    expect(screen.getByRole("button", { name: "Projekt anlegen und Schritt 0 öffnen" })).toBeDisabled()
  })
})
