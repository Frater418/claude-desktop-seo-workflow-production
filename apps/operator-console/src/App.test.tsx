import { afterEach, describe, expect, it, vi } from "vitest"
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react"
import { App } from "./App"
import { createOperatorApiFixture } from "./test/operatorApiFixture"

afterEach(() => {
  cleanup()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

async function renderConsole(): Promise<ReturnType<typeof createOperatorApiFixture>> {
  const fixture = createOperatorApiFixture()
  vi.stubGlobal("fetch", fixture.fetch)
  render(<App tenantId="tenant-welle-zwei" />)
  fireEvent.click(await screen.findByRole("button", { name: "Pflegedienst Alpha öffnen" }))
  await screen.findByRole("heading", { name: "Pflegedienst Alpha" })
  return fixture
}

describe("Heartweb Admin Operator Console", () => {
  it("loads the canonical project into the German work shell without demo fallback", async () => {
    await renderConsole()

    const projectNavigation = screen.getByRole("navigation", { name: "Projektverwaltung" })
    const activeNavigation = screen.getByRole("navigation", { name: "Aktives Projekt" })
    expect(within(projectNavigation).getByRole("button", { name: "Projektübersicht" })).toBeInTheDocument()
    expect(within(activeNavigation).getByRole("button", { name: "Uebergabe" })).toBeInTheDocument()
    expect(within(activeNavigation).getByRole("button", { name: "Projektablauf" })).toHaveAttribute("aria-current", "page")
    const projectHeader = screen.getByRole("heading", { name: "Pflegedienst Alpha" }).closest("header")
    if (projectHeader === null) throw new Error("project header missing")
    expect(within(projectHeader).getByText("Informationsarchitektur pruefen")).toBeInTheDocument()
    expect(within(screen.getByRole("region", { name: "Aktives Projekt" })).getByText("Pflegedienst Alpha")).toBeInTheDocument()
    expect(screen.queryByText(/demo|presentation/i)).not.toBeInTheDocument()
  })

  it("returns to the project overview and opens another canonical workspace", async () => {
    const fixture = await renderConsole()

    fireEvent.click(screen.getByRole("button", { name: "Projektübersicht" }))
    await screen.findByRole("heading", { name: "Projektübersicht" })
    const betaProject = screen.getByRole("button", { name: "Pflegedienst Beta öffnen" })
    fireEvent.click(betaProject)

    expect(await screen.findByRole("heading", { name: "Pflegedienst Beta" })).toBeInTheDocument()
    const betaHeader = screen.getByRole("heading", { name: "Pflegedienst Beta" }).closest("header")
    if (betaHeader === null) throw new Error("beta header missing")
    expect(within(betaHeader).getByText("Beta Pflege GmbH")).toBeInTheDocument()
    expect(fixture.state.calls.some((call) => call.endsWith("GET /v1/tenants/tenant-welle-zwei/projects/project-beta-welle-zwei/runs/current"))).toBe(true)

    fireEvent.click(screen.getByRole("button", { name: "Projektablauf" }))
    fireEvent.click(screen.getByRole("button", { name: "Projektübersicht" }))
    await screen.findByRole("heading", { name: "Projektübersicht" })
    expect(screen.getByRole("button", { name: "Pflegedienst Beta öffnen" })).toBeInTheDocument()
  })

  it("exposes supporting context through the native details disclosure", async () => {
    await renderConsole()

    const summary = screen.getByText("Nachweise und technische Ausführung")
    const details = summary.closest("details")
    if (details === null) throw new Error("supporting details missing")
    expect(details).not.toHaveAttribute("open")
    fireEvent.click(summary)
    expect(details).toHaveAttribute("open")
    expect(screen.getByRole("heading", { name: "Kontextpaket für Schritt 1b" })).toBeInTheDocument()
    fireEvent.click(summary)
    expect(details).not.toHaveAttribute("open")
  })

  it("shows the eight-step initial route and exact machine-gate result without placing 3B in the route", async () => {
    await renderConsole()
    fireEvent.click(screen.getByRole("button", { name: "Projektablauf" }))

    const route = screen.getByRole("list", { name: "Produktionsschritte" })
    expect(within(route).getAllByRole("listitem")).toHaveLength(8)
    expect(within(route).queryByText(/3B/i)).toBeNull()
    expect(screen.getByRole("heading", { name: "Bestanden" })).toBeInTheDocument()
    expect(screen.getByText("Maschinenprüfung für GATE-1B bestanden.")).toBeInTheDocument()
  })

  it("previews Markdown intake, requires full Project V2 review, and reads back canonical Step 0", async () => {
    const fixture = await renderConsole()
    fireEvent.click(screen.getByRole("button", { name: "Projektübersicht" }))
    await screen.findByRole("heading", { name: "Projektübersicht" })
    fireEvent.click(screen.getByRole("button", { name: "Neues Projekt anlegen" }))
    const briefing = screen.getByLabelText("Markdown-Briefing")
    fireEvent.change(briefing, { target: { value: "# Pflege Alpha" } })
    fireEvent.change(screen.getByLabelText("Markdown-Datei"), { target: { files: [new File(["# Datei"], "briefing.md", { type: "text/markdown" })] } })
    fireEvent.click(screen.getByRole("button", { name: "Project V2 erstellen" }))
    await screen.findByRole("heading", { name: "Project V2 prüfen" })
    fireEvent.click(screen.getByRole("button", { name: "Vollständigen Project-V2-Entwurf öffnen" }))
    await screen.findByRole("dialog", { name: "Project V2 prüfen" })
    fireEvent.click(screen.getByRole("button", { name: "Schließen" }))
    fireEvent.click(screen.getByRole("checkbox", { name: "Ich habe den vollständigen Project-V2-Entwurf geprüft." }))
    fireEvent.click(screen.getByRole("button", { name: "Projekt anlegen und Schritt 0 öffnen" }))

    await waitFor(() => expect(fixture.state.calls.some((call) => call.includes("POST /v1/tenants/tenant-welle-zwei/intake/accept"))).toBe(true))
    expect(await screen.findByRole("heading", { name: "Schritt 0: Projekt-Kickoff" })).toBeInTheDocument()
    expect(screen.getByText("Kickoff starten")).toBeInTheDocument()
  })

  it("loads a non-Step-4 artifact into the editor without offering the Step 4 preflight", async () => {
    await renderConsole()
    fireEvent.click(screen.getByRole("button", { name: /^Ergebnisse/ }))
    const loadArtifact = screen.getByRole("button", { name: "outputs/themenstruktur.md, Revision 17" })
    await waitFor(() => expect(loadArtifact).toBeEnabled())
    fireEvent.click(loadArtifact)
    const editor = await screen.findByLabelText("Ergebnisinhalt bearbeiten")
    await waitFor(() => expect(editor).toHaveValue("# Themenstruktur"))
    expect(screen.queryByRole("button", { name: "Schritt 4 Preflight ausführen" })).toBeNull()
  })

  it("keeps task context while filtering and sorting the compact queue", async () => {
    await renderConsole()
    fireEvent.click(screen.getByRole("button", { name: /^Aufgaben/ }))
    fireEvent.change(screen.getByLabelText("Status filtern"), { target: { value: "open" } })
    fireEvent.click(screen.getByRole("button", { name: "Nach Prioritaet sortieren" }))
    fireEvent.click(screen.getByRole("button", { name: "Themenstruktur pruefen" }))

    expect(screen.getByText("Pillar-Struktur pruefen")).toBeInTheDocument()
    expect(screen.getByText("Freigabe der Themenstruktur")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Themenstruktur pruefen" })).toHaveAttribute("aria-pressed", "true")
  })

  it("previews the current submit-for-gate lifecycle action and renders canonical readback", async () => {
    const fixture = await renderConsole()
    fireEvent.click(screen.getByRole("button", { name: "Einreichung prüfen" }))
    expect(await screen.findByText("Das Ergebnis wird zur fachlichen Pruefung eingereicht.")).toBeInTheDocument()
    await waitFor(() => expect(fixture.state.requestBodies.some((body) => body.includes("\"action\":\"submit-for-gate\"") && body.includes("\"tenant_id\":\"tenant-welle-zwei\"") && body.includes("\"project_id\":\"project-welle-zwei\"") && body.includes("\"run_id\":\"lauf-20260821-a\"") && body.includes("\"step_id\":\"1b\"") && body.includes("\"expected_revision\":17"))).toBe(true))
    fireEvent.click(screen.getByRole("button", { name: "Zur Prüfung einreichen" }))

    await waitFor(() => expect(fixture.state.calls.some((call) => call.endsWith("GET /v1/tenants/tenant-welle-zwei/projects/project-welle-zwei"))).toBe(true))
    expect(screen.getByText("Kanonischer Stand aktualisiert.")).toBeInTheDocument()
  })

  it("activates the delivery route with checkpoint creation, canonical readback, and only the whole ZIP action", async () => {
    const fixture = await renderConsole()
    fireEvent.click(screen.getByRole("button", { name: "Projektablauf" }))
    const executionDetails = screen.getByText("Nachweise und technische Ausführung").closest("details")
    if (executionDetails === null) throw new Error("execution details missing")
    fireEvent.click(screen.getByText("Nachweise und technische Ausführung"))
    expect(within(executionDetails).getByText("Notion")).toBeInTheDocument()
    expect(within(executionDetails).getAllByText("Simulation")).toHaveLength(2)
    fireEvent.click(screen.getByRole("button", { name: "Uebergabe" }))

    expect(screen.getByRole("heading", { name: "Uebergabe und Export" })).toBeInTheDocument()
    expect(await screen.findByRole("heading", { name: "Checkpoint-Vorschau" })).toBeInTheDocument()
    const deliveryPath = "/v1/tenants/tenant-welle-zwei/projects/project-welle-zwei/delivery"
    expect(fixture.state.calls.filter((call) => call === `GET ${deliveryPath}/preview?scope=checkpoint`)).toHaveLength(1)
    expect(fixture.state.calls.filter((call) => call === `GET ${deliveryPath}/preview?scope=final`)).toHaveLength(1)
    expect(fixture.state.calls.filter((call) => call === `GET ${deliveryPath}/exports`)).toHaveLength(1)
    expect(screen.queryByText("Sprint 5E Liefervertraege sind noch nicht installiert.")).not.toBeInTheDocument()
    expect(screen.getByRole("navigation", { name: "Aktives Projekt" })).toBeInTheDocument()
    const projectHeader = screen.getByRole("heading", { name: "Pflegedienst Alpha" }).closest("header")
    if (projectHeader === null) throw new Error("delivery project header missing")
    expect(projectHeader).toHaveTextContent("Pflegedienst Alpha")

    fireEvent.change(screen.getByLabelText("Exportumfang"), { target: { value: "checkpoint" } })
    fireEvent.change(screen.getByLabelText("Exportfolge"), { target: { value: "7" } })
    fireEvent.change(screen.getByLabelText("Quell-Snapshot-Revision"), { target: { value: "3" } })
    fireEvent.change(screen.getByLabelText("Paketrevision"), { target: { value: "2" } })
    fireEvent.change(screen.getByLabelText("Entwurfsrichtlinie"), { target: { value: "include_explicit_drafts" } })
    fireEvent.click(screen.getByLabelText("Copywriter"))
    fireEvent.change(screen.getByLabelText("Externe Kundenkennung"), { target: { value: "customer-delivery" } })
    fireEvent.change(screen.getByLabelText("Publikations-URLs"), { target: { value: "https://example.test/delivery" } })
    fireEvent.change(screen.getByLabelText("Notion-Implementierungsaufgaben"), { target: { value: JSON.stringify([{ task_id: "task-delivery-0001", assignment_id: "assignment-delivery-0001", title: "Landingpage pruefen", status: "not_started", comments: "", source_assignee: "Redaktion", priority: "high", deadline: "2026-09-01", role: "copywriter", dependencies: [], artifact_relations: [], notion_user_id: "notion-user-delivery-0001" }]) } })
    fireEvent.click(screen.getByRole("button", { name: "Export erstellen" }))

    await waitFor(() => expect(fixture.state.calls.filter((call) => call === `POST ${deliveryPath}/exports`)).toHaveLength(1))
    expect(fixture.state.deliveryCreates).toEqual([expect.objectContaining({ scope: "checkpoint", sourceSnapshotRevision: 3, packageRevision: 2 })])
    expect(fixture.state.requestBodies.filter((body) => body.includes("\"scope\":\"checkpoint\"") && body.includes("\"source_snapshot_revision\":3") && body.includes("\"package_revision\":2"))).toHaveLength(1)
    expect(fixture.state.calls.filter((call) => call.startsWith(`GET ${deliveryPath}/exports/delivery-export-`))).toHaveLength(1)
    expect(await screen.findByText("Export wurde erstellt und kanonisch gelesen.")).toBeInTheDocument()
    expect(screen.getByText("Ausgewaehlter Export")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Gesamtes ZIP herunterladen" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Notion-Uebergabe vorbereiten" })).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /Ordner|Copywriter.*herunterladen|Developer.*herunterladen|Notion.*herunterladen|n8n/i })).not.toBeInTheDocument()
  })
})
