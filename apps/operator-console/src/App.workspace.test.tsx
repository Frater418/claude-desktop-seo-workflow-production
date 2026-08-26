import { afterEach, describe, expect, it, vi } from "vitest"
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react"
import { App } from "./App"
import shellStyles from "./styles.css?inline"
import { createOperatorApiFixture } from "./test/operatorApiFixture"

const narrowShellStyles = shellStyles.slice(shellStyles.indexOf("@media (max-width: 850px)"), shellStyles.indexOf("@media (max-width: 520px)"))
const desktopShellStyles = shellStyles.slice(0, shellStyles.indexOf("@media (max-width: 850px)"))

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

async function openAlpha(): Promise<void> {
  fireEvent.click(await screen.findByRole("button", { name: "Pflegedienst Alpha öffnen" }))
  await screen.findByRole("heading", { name: "Pflegedienst Alpha" })
}

describe("Operator workspace summary", () => {
  it("renders the canonical current run, step, blocker, and next action inside a normal-flow narrow shell", async () => {
    // Given: a loaded canonical workspace with a current run and operational blocker.
    const fixture = createOperatorApiFixture()
    vi.stubGlobal("fetch", fixture.fetch)
    render(<App tenantId="tenant-welle-zwei" />)

    // When: the canonical project becomes ready in the operator shell.
    await openAlpha()

    // Then: the operator can read its current execution context without leaving the shell.
    const banner = screen.getByRole("heading", { name: "Pflegedienst Alpha" }).closest("header")
    if (banner === null) throw new Error("project header missing")
    expect(within(banner).getByText("Schritt 1B: Seitenarchitektur")).toBeInTheDocument()
    expect(within(banner).getByText("Informationsarchitektur pruefen")).toBeInTheDocument()
    expect(screen.getByText("Freigabe der Themenstruktur fehlt")).toBeInTheDocument()
    expect(screen.getByText("lauf-20260821-a")).toBeInTheDocument()
    const frame = document.querySelector(".workspace-frame")
    expect(frame?.children).toHaveLength(1)
    expect(frame?.firstElementChild).toHaveClass("workspace-main")
    expect(document.querySelector(".workspace-main")?.nextElementSibling).toBeNull()
    expect(desktopShellStyles).toMatch(/\.operator-shell\s*\{[^}]*grid-template-columns:\s*15rem minmax\(0, 1fr\);/)
    expect(narrowShellStyles).toMatch(/\.operator-shell\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\);/)
    expect(narrowShellStyles).toMatch(/\.side-navigation\s*\{[^}]*position:\s*static;[^}]*block-size:\s*auto;[^}]*overflow:\s*visible;/)
    expect(narrowShellStyles).toMatch(/body\s*\{[^}]*overflow-x:\s*hidden;[^}]*overflow-y:\s*auto;/)
    expect(narrowShellStyles).not.toMatch(/position:\s*(sticky|fixed)/)
    expect(shellStyles).toMatch(/\.route-action-footer\s*\{[^}]*border-block-start:/)
    expect(shellStyles).not.toMatch(/\.route-action-footer\s*\{[^}]*position:\s*(sticky|fixed)/)
  })

  it("preserves readable German and technical token boundaries in responsive fact layouts", () => {
    expect(narrowShellStyles).toMatch(/\.project-status, \.facts\s*\{[^}]*grid-template-columns:\s*repeat\(auto-fit, minmax\(min\(14rem, 100%\), 1fr\)\);/)
    expect(shellStyles).toMatch(/\.project-choice-facts\s*\{[^}]*grid-template-columns:\s*repeat\(2, minmax\(0, 1fr\)\);/)
    expect(shellStyles).toMatch(/\.machine-review\s*\{[^}]*border-inline-start:\s*var\(--space-1\) solid var\(--color-accent\);/)
    expect(shellStyles).toMatch(/\.technical-facts dd\s*\{[^}]*max-inline-size:\s*100%;[^}]*overflow-x:\s*auto;[^}]*white-space:\s*nowrap;/)
    expect(shellStyles).toMatch(/\.project-header dd, \.project-choice-heading > strong, \.project-choice-heading > span, \.project-choice-facts strong, \.facts strong, \.facts dd\s*\{[^}]*hyphens:\s*auto;[^}]*overflow-wrap:\s*normal;[^}]*word-break:\s*normal;/)
  })

  it("restores workspace scroll immediately and after paint only for route changes", async () => {
    const fixture = createOperatorApiFixture()
    vi.stubGlobal("fetch", fixture.fetch)
    const frameCallbacks = new Map<number, FrameRequestCallback>()
    const requestFrame = vi.fn((callback: FrameRequestCallback): number => {
      const frame = frameCallbacks.size + 1
      frameCallbacks.set(frame, callback)
      return frame
    })
    const cancelFrame = vi.fn((frame: number): void => { frameCallbacks.delete(frame) })
    vi.stubGlobal("requestAnimationFrame", requestFrame)
    vi.stubGlobal("cancelAnimationFrame", cancelFrame)
    const view = render(<App tenantId="tenant-welle-zwei" />)
    await openAlpha()
    const frame = document.querySelector<HTMLDivElement>(".workspace-frame")
    if (frame === null) throw new Error("workspace frame missing")

    frame.scrollTop = Number.MAX_SAFE_INTEGER
    view.rerender(<App tenantId="tenant-welle-zwei" />)
    expect(frame.scrollTop).toBe(Number.MAX_SAFE_INTEGER)

    fireEvent.click(screen.getByRole("button", { name: "Projektablauf" }))
    expect(frame.scrollTop).toBe(0)
    frame.scrollTop = Number.MAX_SAFE_INTEGER
    const latestFrame = Math.max(...frameCallbacks.keys())
    frameCallbacks.get(latestFrame)?.(performance.now())
    expect(frame.scrollTop).toBe(0)
    expect(screen.getByRole("heading", { name: "Schritt 1B: Seitenarchitektur" })).toBeInTheDocument()

    frame.scrollTop = Number.MAX_SAFE_INTEGER
    fireEvent.click(screen.getByRole("button", { name: "Projektübersicht" }))
    expect(frame.scrollTop).toBe(0)
    await screen.findByRole("heading", { name: "Projektübersicht" })
    fireEvent.click(screen.getByRole("button", { name: "Neues Projekt anlegen" }))
    expect(screen.getByRole("heading", { name: "Briefing in Project V2 umwandeln" })).toBeInTheDocument()
    expect(cancelFrame).toHaveBeenCalled()
    view.unmount()
    expect(cancelFrame).toHaveBeenCalledWith(expect.any(Number))
  })

  it("resets workspace scroll synchronously before canonical project selection", async () => {
    const fixture = createOperatorApiFixture()
    vi.stubGlobal("fetch", fixture.fetch)
    render(<App tenantId="tenant-welle-zwei" />)
    await openAlpha()
    const frame = document.querySelector<HTMLDivElement>(".workspace-frame")
    if (frame === null) throw new Error("workspace frame missing")

    frame.scrollTop = Number.MAX_SAFE_INTEGER
    fireEvent.click(screen.getByRole("button", { name: "Projektübersicht" }))

    expect(frame.scrollTop).toBe(0)
    await screen.findByRole("heading", { name: "Projektübersicht" })
    fireEvent.click(screen.getByRole("button", { name: "Pflegedienst Beta öffnen" }))
    await screen.findByRole("heading", { name: "Pflegedienst Beta" })
    expect(document.querySelector<HTMLDivElement>(".workspace-frame")?.scrollTop).toBe(0)
  })
})
