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
  await screen.findByRole("heading", { name: "Pflegedienst Alpha" })
  return fixture
}

function activateDisclosure(toggle: HTMLElement, key: "Enter" | " "): void {
  toggle.focus()
  fireEvent.keyDown(toggle, { key })
  fireEvent.keyUp(toggle, { key })
  fireEvent.click(toggle)
}

describe("Heartweb Admin Operator Console", () => {
  it("loads the canonical project into the German work shell without demo fallback", async () => {
    await renderConsole()

    const navigation = screen.getByRole("navigation", { name: "Hauptnavigation" })
    expect(within(navigation).getByRole("link", { name: "Projekte" })).toBeInTheDocument()
    expect(within(navigation).getByRole("link", { name: "Uebergabe und Export" })).toBeInTheDocument()
    expect(within(screen.getByRole("banner")).getByText("Aktiver Schritt")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Pflegedienst Alpha waehlen" })).toHaveAttribute("aria-current", "true")
    expect(within(screen.getByRole("banner")).getByText("Informationsarchitektur pruefen")).toBeInTheDocument()
    expect(within(screen.getByRole("region", { name: "Projekt waehlen" })).getByText("Informationsarchitektur pruefen")).toBeInTheDocument()
    expect(screen.queryByText(/demo|presentation/i)).not.toBeInTheDocument()
  })

  it("lists canonical projects, keeps the selected project marked, and reloads its canonical workspace", async () => {
    const fixture = await renderConsole()

    const betaProject = screen.getByRole("button", { name: "Pflegedienst Beta waehlen" })
    expect(betaProject).not.toHaveAttribute("aria-current")
    fireEvent.click(betaProject)

    expect(await screen.findByRole("heading", { name: "Pflegedienst Beta" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Pflegedienst Beta waehlen" })).toHaveAttribute("aria-current", "true")
    expect(within(screen.getByRole("banner")).getByText("Beta Pflege GmbH")).toBeInTheDocument()
    expect(fixture.state.calls.some((call) => call.endsWith("GET /v1/tenants/tenant-welle-zwei/projects/project-beta-welle-zwei/runs/current"))).toBe(true)

    fireEvent.click(screen.getByRole("link", { name: "Workflow" }))
    fireEvent.click(screen.getByRole("link", { name: "Projekte" }))
    expect(screen.getByRole("button", { name: "Pflegedienst Beta waehlen" })).toHaveAttribute("aria-current", "true")
  })

  it("operates the collapsible context by pointer, Enter, and Space without leaving collapsed controls in the keyboard flow", async () => {
    await renderConsole()

    const toggle = screen.getByRole("button", { name: "Kontext einklappen" })
    const contentId = toggle.getAttribute("aria-controls")
    expect(toggle).toHaveAttribute("aria-expanded", "true")
    expect(document.getElementById(contentId ?? "")).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Nachweise" })).toBeInTheDocument()

    toggle.focus()
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute("aria-expanded", "false")
    expect(document.activeElement).toBe(toggle)
    expect(document.getElementById(contentId ?? "")).not.toBeInTheDocument()
    expect(screen.queryByText("Technische Details")).not.toBeInTheDocument()

    activateDisclosure(toggle, "Enter")
    expect(toggle).toHaveAttribute("aria-expanded", "true")
    expect(screen.getByRole("heading", { name: "Feststellungen" })).toBeInTheDocument()

    activateDisclosure(toggle, " ")
    expect(toggle).toHaveAttribute("aria-expanded", "false")
  })

  it("shows the workflow route, exact gate result, and the separate 3b not-due sideflow", async () => {
    await renderConsole()
    fireEvent.click(screen.getByRole("link", { name: "Workflow" }))

    expect(screen.getByLabelText("Initiale Workflow-Schritte")).toHaveTextContent("011b1c234a4b")
    expect(screen.getByText("3b: noch nicht faellig")).toBeInTheDocument()
    expect(screen.getByText("Maschinenpruefung bestanden")).toBeInTheDocument()
  })

  it("previews pasted and selected Markdown intake, accepts reviewed corrections, and reads back canonical data", async () => {
    const fixture = await renderConsole()
    fireEvent.click(screen.getByRole("button", { name: "Projekt anlegen" }))
    const briefing = screen.getByLabelText("Markdown-Briefing")
    fireEvent.change(briefing, { target: { value: "# Pflege Alpha" } })
    fireEvent.change(screen.getByLabelText("Markdown-Datei"), { target: { files: [new File(["# Datei"], "briefing.md", { type: "text/markdown" })] } })
    fireEvent.click(screen.getByRole("button", { name: "Vorschau erstellen" }))
    await screen.findByDisplayValue("Pflegedienst Alpha")
    fireEvent.change(screen.getByLabelText("Projektname pruefen"), { target: { value: "Pflegedienst Alpha korrigiert" } })
    fireEvent.click(screen.getByRole("button", { name: "Intake verbindlich annehmen" }))

    await waitFor(() => expect(fixture.state.calls.some((call) => call.includes("POST /v1/tenants/tenant-welle-zwei/intake/accept"))).toBe(true))
    expect(screen.getByText("Schritt 0 bereit")).toBeInTheDocument()
  })

  it("loads a non-Step-4 artifact into the editor without offering the Step 4 preflight", async () => {
    await renderConsole()
    fireEvent.click(screen.getByRole("link", { name: "Artefakte" }))
    const loadArtifact = screen.getByRole("button", { name: "outputs/themenstruktur.md, Revision 17" })
    await waitFor(() => expect(loadArtifact).toBeEnabled())
    fireEvent.click(loadArtifact)
    const editor = await screen.findByLabelText("Artefaktinhalt bearbeiten")
    await waitFor(() => expect(editor).toHaveValue("# Themenstruktur"))
    expect(screen.queryByRole("button", { name: "Schritt 4 Preflight ausfuehren" })).toBeNull()
  })

  it("keeps task context while filtering and sorting the compact queue", async () => {
    await renderConsole()
    fireEvent.click(screen.getByRole("link", { name: "Aufgaben" }))
    fireEvent.change(screen.getByLabelText("Status filtern"), { target: { value: "open" } })
    fireEvent.click(screen.getByRole("button", { name: "Nach Prioritaet sortieren" }))
    fireEvent.click(screen.getByRole("button", { name: "Themenstruktur pruefen" }))

    expect(screen.getByText("Pillar-Struktur pruefen")).toBeInTheDocument()
    expect(screen.getByText("Freigabe der Themenstruktur")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Themenstruktur pruefen" })).toHaveAttribute("aria-pressed", "true")
  })

  it("previews illegal action remediation, confirms an allowed review, and renders canonical readback", async () => {
    const fixture = await renderConsole()
    fireEvent.click(screen.getByRole("link", { name: "Pruefungen und Freigaben" }))
    fireEvent.change(screen.getByLabelText("Entscheidung waehlen"), { target: { value: "request-waiver" } })
    fireEvent.change(screen.getByLabelText("Begruendung"), { target: { value: "Blockierte Ausnahme" } })
    fireEvent.change(screen.getByLabelText("Pruefanweisung fuer Ausnahme"), { target: { value: "Ausnahme pruefen" } })
    fireEvent.click(screen.getByRole("button", { name: "Vorschau fuer Ausnahme erstellen" }))
    expect(await screen.findByText("Pruefung abschliessen und erneut versuchen.")).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText("Entscheidung waehlen"), { target: { value: "approve" } })
    fireEvent.click(screen.getByRole("button", { name: "Freigabe vorbereiten" }))
    expect(await screen.findByText("Freigabe wird als menschliche Entscheidung gespeichert.")).toBeInTheDocument()
    await waitFor(() => expect(fixture.state.requestBodies.some((body) => body.includes("\"tenant_id\":\"tenant-welle-zwei\"") && body.includes("\"project_id\":\"project-welle-zwei\"") && body.includes("\"run_id\":\"lauf-20260821-a\"") && body.includes("\"step_id\":\"1b\"") && body.includes("\"expected_revision\":17"))).toBe(true))
    fireEvent.click(screen.getByRole("button", { name: "Freigabe bestaetigen" }))

    await waitFor(() => expect(fixture.state.calls.some((call) => call.endsWith("GET /v1/tenants/tenant-welle-zwei/projects/project-welle-zwei"))).toBe(true))
    expect(screen.getByText("Kanonischer Stand aktualisiert")).toBeInTheDocument()
  })

  it("activates the delivery route with checkpoint creation, canonical readback, and only the whole ZIP action", async () => {
    const fixture = await renderConsole()
    fireEvent.click(screen.getByRole("link", { name: "Workflow" }))
    expect(screen.getByText("Notion: Simulation")).toBeInTheDocument()
    expect(screen.getByText("n8n: Simulation")).toBeInTheDocument()
    fireEvent.click(screen.getByRole("link", { name: "Uebergabe und Export" }))

    expect(screen.getByRole("heading", { name: "Uebergabe und Export" })).toBeInTheDocument()
    expect(await screen.findByRole("heading", { name: "Checkpoint-Vorschau" })).toBeInTheDocument()
    const deliveryPath = "/v1/tenants/tenant-welle-zwei/projects/project-welle-zwei/delivery"
    expect(fixture.state.calls.filter((call) => call === `GET ${deliveryPath}/preview?scope=checkpoint`)).toHaveLength(1)
    expect(fixture.state.calls.filter((call) => call === `GET ${deliveryPath}/preview?scope=final`)).toHaveLength(1)
    expect(fixture.state.calls.filter((call) => call === `GET ${deliveryPath}/exports`)).toHaveLength(1)
    expect(screen.queryByText("Sprint 5E Liefervertraege sind noch nicht installiert.")).not.toBeInTheDocument()
    expect(screen.getByRole("navigation", { name: "Hauptnavigation" })).toBeInTheDocument()
    expect(screen.getByRole("banner")).toHaveTextContent("Pflegedienst Alpha")
    expect(screen.getByRole("heading", { name: "Kontext und Nachweise" })).toBeInTheDocument()

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
