import { afterEach, describe, expect, it, vi } from "vitest"
import { cleanup, render, screen, within } from "@testing-library/react"
import { App } from "./App"
import { createOperatorApiFixture } from "./test/operatorApiFixture"

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe("Operator workspace summary", () => {
  it("renders the canonical current run, step, blocker, and next action together", async () => {
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
  })
})
