import { afterEach, describe, expect, it, vi } from "vitest"
import { cleanup, render, screen } from "@testing-library/react"
import { App } from "./App"

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), { headers: { "Content-Type": "application/json" } })
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe("German API states", () => {
  it("shows a German loading state while canonical data is pending", () => {
    const pendingFetch: typeof fetch = () => new Promise<Response>(() => undefined)
    vi.stubGlobal("fetch", pendingFetch)

    render(<App tenantId="tenant-welle-zwei" />)

    expect(screen.getByRole("heading", { name: "Lokale Arbeitsdaten werden geladen" })).toBeInTheDocument()
  })

  it("shows a German empty state when the canonical project list is empty", async () => {
    const emptyFetch: typeof fetch = (input) => {
      const url = input.toString()
      if (url.endsWith("/readyz")) return Promise.resolve(jsonResponse({ data: { status: "ready" } }))
      if (url.endsWith("/projects")) return Promise.resolve(jsonResponse({ data: [] }))
      return Promise.reject(new Error(`Unerwartete Testanfrage: ${url}`))
    }
    vi.stubGlobal("fetch", emptyFetch)

    render(<App tenantId="tenant-welle-zwei" />)

    expect(await screen.findByRole("heading", { name: "Kein lokales Projekt vorhanden" })).toBeInTheDocument()
  })

  it("shows a German error state when the local API cannot be read", async () => {
    const failingFetch: typeof fetch = () => Promise.reject(new Error("Lokale Verbindung fehlgeschlagen."))
    vi.stubGlobal("fetch", failingFetch)

    render(<App tenantId="tenant-welle-zwei" />)

    expect(await screen.findByRole("heading", { name: "Lokale Operator-API nicht verfuegbar" })).toBeInTheDocument()
    expect(screen.getByText("Es werden keine Demo-Daten angezeigt.")).toBeInTheDocument()
  })
})
