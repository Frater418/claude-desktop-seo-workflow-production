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

describe("Operator workspace summary", () => {
  it("renders the canonical current run, step, blocker, and next action inside a normal-flow narrow shell", async () => {
    // Given: a loaded canonical workspace with a current run and operational blocker.
    const fixture = createOperatorApiFixture()
    vi.stubGlobal("fetch", fixture.fetch)
    render(<App tenantId="tenant-welle-zwei" />)

    // When: the canonical project becomes ready in the operator shell.
    await screen.findByRole("heading", { name: "Pflegedienst Alpha" })

    // Then: the operator can read its current execution context without leaving the shell.
    const banner = screen.getByRole("banner")
    expect(within(banner).getByText("1b")).toBeInTheDocument()
    expect(within(banner).getByText("Informationsarchitektur pruefen")).toBeInTheDocument()
    expect(screen.getByText("Abhaengigkeit: Freigabe der Themenstruktur fehlt")).toBeInTheDocument()
    expect(screen.getByText("lauf-20260821-a")).toBeInTheDocument()
    expect(document.querySelector(".workspace-frame")?.firstElementChild).toHaveClass("workspace-main")
    expect(document.querySelector(".workspace-frame")?.lastElementChild).toHaveClass("evidence-panel")
    expect(document.querySelector(".workspace-main")?.nextElementSibling).toHaveClass("evidence-panel")
    expect(desktopShellStyles).toMatch(/\.operator-shell\s*\{[^}]*grid-template-columns:\s*minmax\(13rem, 17rem\) minmax\(0, 1fr\);/)
    expect(narrowShellStyles).toMatch(/\.operator-shell\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\);[^}]*grid-template-rows:\s*auto minmax\(0, 1fr\);[^}]*block-size:\s*100dvh;[^}]*overflow:\s*hidden;/)
    expect(narrowShellStyles).toMatch(/\.side-navigation nav\s*\{[^}]*display:\s*flex;[^}]*flex-wrap:\s*wrap;[^}]*overflow:\s*visible;/)
    expect(narrowShellStyles).toMatch(/\.shell-main\s*\{[^}]*grid-template-rows:\s*auto minmax\(0, 1fr\) auto;[^}]*min-block-size:\s*0;/)
    expect(narrowShellStyles).toMatch(/\.workspace-frame\s*\{[^}]*display:\s*block;[^}]*min-block-size:\s*0;[^}]*overflow-anchor:\s*none;[^}]*overflow-x:\s*hidden;[^}]*overflow-y:\s*auto;/)
    expect(narrowShellStyles).not.toMatch(/\.workspace-frame\s*\{[^}]*grid-template-(columns|rows):/)
    expect(narrowShellStyles).toMatch(/\.workspace-frame\s*\{[^}]*overflow-anchor:\s*none;/)
    expect(narrowShellStyles).toMatch(/body\s*\{[^}]*overflow:\s*hidden;/)
    expect(narrowShellStyles).not.toMatch(/position:\s*(sticky|fixed)/)
    expect(shellStyles).toMatch(/\.route-action-footer\s*\{[^}]*border-block-start:/)
    expect(shellStyles).not.toMatch(/\.route-action-footer\s*\{[^}]*position:\s*(sticky|fixed)/)
    expect(narrowShellStyles).not.toMatch(/white-space:\s*nowrap/)
  })

  it("preserves readable German and technical token boundaries in responsive fact layouts", () => {
    expect(narrowShellStyles).toMatch(/\.project-status, \.facts, \.project-choice-facts\s*\{[^}]*grid-template-columns:\s*repeat\(auto-fit, minmax\(min\(16rem, 100%\), 1fr\)\);/)
    expect(shellStyles).toMatch(/\.gate-report \.facts\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\);/)
    expect(shellStyles).toMatch(/\.task-detail \.facts > div:nth-child\(6\) dd, \.gate-report \.facts > div:nth-child\(4\) dd, \.gate-report \.facts > div:nth-child\(5\) dd, \.gate-report details dd, \.technical-facts dd\s*\{[^}]*display:\s*block;[^}]*max-inline-size:\s*100%;[^}]*overflow-x:\s*auto;[^}]*white-space:\s*nowrap;/)
    expect(shellStyles).toMatch(/\.project-header dd, \.project-choice-heading > strong, \.project-choice-heading > span, \.project-choice-facts strong, \.facts strong, \.facts dd, \.context-group p, \.context-group li\s*\{[^}]*hyphens:\s*auto;[^}]*overflow-wrap:\s*normal;[^}]*word-break:\s*normal;/)
    expect(shellStyles).not.toMatch(/overflow-wrap:\s*anywhere/)
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
    await screen.findByRole("heading", { name: "Pflegedienst Alpha" })
    const frame = document.querySelector<HTMLDivElement>(".workspace-frame")
    if (frame === null) throw new Error("workspace frame missing")

    frame.scrollTop = Number.MAX_SAFE_INTEGER
    view.rerender(<App tenantId="tenant-welle-zwei" />)
    expect(frame.scrollTop).toBe(Number.MAX_SAFE_INTEGER)

    fireEvent.click(screen.getByRole("link", { name: "Workflow" }))
    expect(frame.scrollTop).toBe(0)
    frame.scrollTop = Number.MAX_SAFE_INTEGER
    const latestFrame = Math.max(...frameCallbacks.keys())
    frameCallbacks.get(latestFrame)?.(performance.now())
    expect(frame.scrollTop).toBe(0)
    expect(screen.getByRole("heading", { name: "Aktiver Arbeitsschritt" })).toBeInTheDocument()

    frame.scrollTop = Number.MAX_SAFE_INTEGER
    fireEvent.click(screen.getByRole("button", { name: "Projekt anlegen" }))
    expect(frame.scrollTop).toBe(0)
    expect(screen.getByRole("heading", { name: "Projekt anlegen" })).toBeInTheDocument()
    expect(cancelFrame).toHaveBeenCalled()
    view.unmount()
    expect(cancelFrame).toHaveBeenCalledWith(expect.any(Number))
  })

  it("resets workspace scroll synchronously before canonical project selection", async () => {
    const fixture = createOperatorApiFixture()
    vi.stubGlobal("fetch", fixture.fetch)
    render(<App tenantId="tenant-welle-zwei" />)
    await screen.findByRole("heading", { name: "Pflegedienst Alpha" })
    const frame = document.querySelector<HTMLDivElement>(".workspace-frame")
    if (frame === null) throw new Error("workspace frame missing")

    frame.scrollTop = Number.MAX_SAFE_INTEGER
    fireEvent.click(screen.getByRole("button", { name: "Pflegedienst Beta waehlen" }))

    expect(frame.scrollTop).toBe(0)
    await screen.findByRole("heading", { name: "Pflegedienst Beta" })
  })
})
