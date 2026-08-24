import { afterEach, describe, expect, it, vi } from "vitest"
import { cleanup, render, screen } from "@testing-library/react"
import { App } from "./App"
import { createOperatorApiFixture } from "./test/operatorApiFixture"

afterEach(() => {
  cleanup()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe("Operator Console configuration", () => {
  it("fails closed without a configured tenant and does not call the API", () => {
    const fixture = createOperatorApiFixture()
    vi.stubGlobal("fetch", fixture.fetch)

    render(<App />)

    expect(screen.getByRole("heading", { name: "Operator-Konfiguration unvollstaendig" })).toBeInTheDocument()
    expect(fixture.state.calls).toHaveLength(0)
  })
})
