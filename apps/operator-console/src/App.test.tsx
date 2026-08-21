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
    expect(fixture.state.calls.some((call) => call.endsWith("GET /v1/tenants/tenant-welle-zwei/projects/projekt-beta-welle-zwei/runs/current"))).toBe(true)

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

  it("loads artifact content into a real editor, saves an immutable revision, compares it, and validates it", async () => {
    await renderConsole()
    fireEvent.click(screen.getByRole("link", { name: "Artefakte" }))
    fireEvent.click(screen.getByRole("button", { name: "outputs/themenstruktur.md, Revision 17" }))
    const editor = await screen.findByLabelText("Artefaktinhalt bearbeiten")
    expect(editor).toHaveValue("# Themenstruktur")
    fireEvent.change(editor, { target: { value: "# Neue Themenstruktur" } })
    fireEvent.click(within(screen.getByLabelText("Artefaktaktionen")).getByRole("button", { name: "Als neue Revision speichern" }))
    expect(await screen.findByText("Revision 18 wurde unveraenderlich gespeichert.")).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: "Revisionen vergleichen" }))
    expect(await screen.findByText("+ Neue Themenstruktur")).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: "Erneut pruefen" }))
    expect(await screen.findByText("Maschinenpruefung bestanden")).toBeInTheDocument()
  })

  it("keeps task context while filtering and sorting the compact queue", async () => {
    await renderConsole()
    fireEvent.click(screen.getByRole("link", { name: "Aufgaben" }))
    fireEvent.change(screen.getByLabelText("Status filtern"), { target: { value: "offen" } })
    fireEvent.click(screen.getByRole("button", { name: "Nach Prioritaet sortieren" }))
    fireEvent.click(screen.getByRole("button", { name: "Themenstruktur pruefen" }))

    expect(screen.getByText("Pillar-Struktur pruefen")).toBeInTheDocument()
    expect(screen.getByText("Freigabe der Themenstruktur")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Themenstruktur pruefen" })).toHaveAttribute("aria-pressed", "true")
  })

  it("previews illegal action remediation, confirms an allowed review, and renders canonical readback", async () => {
    const fixture = await renderConsole()
    fireEvent.click(screen.getByRole("link", { name: "Pruefungen und Freigaben" }))
    fireEvent.click(screen.getByRole("button", { name: "Ausnahme anfragen" }))
    fireEvent.change(screen.getByLabelText("Begruendung"), { target: { value: "Blockierte Ausnahme" } })
    fireEvent.change(screen.getByLabelText("Pruefanweisung fuer Ausnahme"), { target: { value: "Ausnahme pruefen" } })
    fireEvent.click(screen.getByRole("button", { name: "Vorschau fuer Ausnahme erstellen" }))
    expect(await screen.findByText("Pruefung abschliessen und erneut versuchen.")).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: "Freigabe vorbereiten" }))
    expect(await screen.findByText("Freigabe wird als menschliche Entscheidung gespeichert.")).toBeInTheDocument()
    await waitFor(() => expect(fixture.state.requestBodies.some((body) => body.includes("\"tenant_id\":\"tenant-welle-zwei\"") && body.includes("\"project_id\":\"projekt-welle-zwei\"") && body.includes("\"run_id\":\"lauf-20260821-a\"") && body.includes("\"step_id\":\"1b\"") && body.includes("\"expected_revision\":17"))).toBe(true))
    fireEvent.click(screen.getByRole("button", { name: "Freigabe bestaetigen" }))

    await waitFor(() => expect(fixture.state.calls.some((call) => call.endsWith("GET /v1/tenants/tenant-welle-zwei/projects/projekt-welle-zwei"))).toBe(true))
    expect(screen.getByText("Kanonischer Stand aktualisiert")).toBeInTheDocument()
  })

  it("labels local integration simulation and keeps delivery contract-gated without requests", async () => {
    const fixture = await renderConsole()
    fireEvent.click(screen.getByRole("link", { name: "Workflow" }))
    expect(screen.getByText("Notion: simuliert")).toBeInTheDocument()
    expect(screen.getByText("n8n: simuliert")).toBeInTheDocument()
    const callsBeforeDelivery = [...fixture.state.calls]
    const prohibitedDeliveryRequest = /\b(?:deliver(?:y|ies)|preview|create|exports?|downloads?|folders?|notion)\b/i
    fireEvent.click(screen.getByRole("link", { name: "Uebergabe und Export" }))
    expect(screen.getByRole("heading", { name: "Uebergabe und Export" })).toBeInTheDocument()
    expect(screen.getByText("Sprint 5E Liefervertraege sind noch nicht installiert.")).toBeInTheDocument()
    expect(fixture.state.calls).toEqual(callsBeforeDelivery)
    expect(fixture.state.calls.filter((call) => prohibitedDeliveryRequest.test(call))).toEqual([])
    expect(screen.queryByRole("button", { name: /Vorschau|Export|Download|Ordner|Notion/i })).not.toBeInTheDocument()
  })
})
