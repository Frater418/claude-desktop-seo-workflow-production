import { afterEach, describe, expect, it, vi } from "vitest"
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import { App } from "./App"
import { createOperatorApiFixture } from "./test/operatorApiFixture"

type JsonObject = Readonly<Record<string, unknown>>

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function object(value: string): JsonObject {
  const parsed: unknown = JSON.parse(value)
  if (isObject(parsed)) return parsed
  throw new Error("Expected JSON object")
}

function traceStarts(requestBodies: readonly string[]): readonly JsonObject[] {
  return requestBodies.map(object).filter((body) => body["schema_version"] === "1.0.0" && typeof body["scenario_id"] === "string" && typeof body["source"] === "string")
}

function stringAt(object: JsonObject, field: string): string {
  const value = object[field]
  if (typeof value === "string") return value
  throw new Error(`Expected ${field}`)
}

afterEach(() => {
  cleanup()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  window.history.replaceState({}, "", "/")
})

describe("Operator Console diagnostic session", () => {
  it("does not create a diagnostic trace before canonical workspace readiness", () => {
    // Given: a canonical API request that remains pending.
    const calls: string[] = []
    const pendingFetch: typeof fetch = (input) => {
      calls.push(input.toString())
      return new Promise<Response>(() => undefined)
    }
    vi.stubGlobal("fetch", pendingFetch)

    // When: the console is still loading.
    render(<App tenantId="tenant-welle-zwei" />)

    // Then: no diagnostic write is attempted.
    expect(screen.getByRole("heading", { name: "Lokale Arbeitsdaten werden geladen" })).toBeInTheDocument()
    expect(calls.some((call) => call.includes("diagnostic-traces"))).toBe(false)
  })

  it("starts the canonical trace from browser search configuration only after ready", async () => {
    // Given: the browser provides automated diagnostic configuration.
    const fixture = createOperatorApiFixture()
    vi.stubGlobal("fetch", fixture.fetch)
    window.history.replaceState({}, "", "/?diagnostic_source=automated&diagnostic_scenario=automated-m06")

    // When: the canonical workspace becomes ready without an App search override.
    render(<App tenantId="tenant-welle-zwei" />)
    await screen.findByRole("heading", { name: "Pflegedienst Alpha" })
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Diagnoseprotokoll aktiv."))

    // Then: its one start request uses canonical identity and second-normalized browser time.
    const start = traceStarts(fixture.state.requestBodies).at(0)
    if (start === undefined) throw new Error("Expected trace start")
    expect(stringAt(start, "tenant_id")).toBe("tenant-welle-zwei")
    expect(stringAt(start, "project_id")).toBe("project-welle-zwei")
    expect(stringAt(start, "run_id")).toBe("lauf-20260821-a")
    expect(stringAt(start, "source")).toBe("automated")
    expect(stringAt(start, "scenario_id")).toBe("automated-m06")
    expect(stringAt(start, "created_at")).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/)
  })

  it("fails visibly without API access for invalid explicit diagnostic query values", () => {
    // Given: an explicit invalid diagnostic source and scenario.
    const fixture = createOperatorApiFixture()
    vi.stubGlobal("fetch", fixture.fetch)

    // When: the invalid operator configuration is rendered.
    render(<App search="?diagnostic_source=scheduled&diagnostic_scenario=not/a-slug" tenantId="tenant-welle-zwei" />)

    // Then: the console fails closed before reading or writing the API.
    expect(screen.getByRole("heading", { name: "Operator-Konfiguration ungueltig" })).toBeInTheDocument()
    expect(fixture.state.calls).toHaveLength(0)
  })

  it("closes before starting each canonical project rollover and retains the original identity timestamp", async () => {
    // Given: a ready console with two canonical projects.
    const fixture = createOperatorApiFixture()
    vi.stubGlobal("fetch", fixture.fetch)
    render(<App search="?diagnostic_source=manual&diagnostic_scenario=manual-walkthrough" tenantId="tenant-welle-zwei" />)
    await screen.findByRole("heading", { name: "Pflegedienst Alpha" })
    await waitFor(() => expect(traceStarts(fixture.state.requestBodies)).toHaveLength(1))

    // When: the operator moves to the second project and back to the first.
    fireEvent.click(screen.getByRole("button", { name: "Pflegedienst Beta waehlen" }))
    await screen.findByRole("heading", { name: "Pflegedienst Beta" })
    await waitFor(() => expect(traceStarts(fixture.state.requestBodies)).toHaveLength(2))
    fireEvent.click(screen.getByRole("button", { name: "Pflegedienst Alpha waehlen" }))
    await screen.findByRole("heading", { name: "Pflegedienst Alpha" })
    await waitFor(() => expect(traceStarts(fixture.state.requestBodies)).toHaveLength(3))

    // Then: every new identity starts after its predecessor closes and the first identity retains its timestamp.
    const starts = traceStarts(fixture.state.requestBodies)
    const first = starts.at(0)
    const second = starts.at(1)
    const third = starts.at(2)
    if (first === undefined || second === undefined || third === undefined) throw new Error("Expected trace rollovers")
    expect([stringAt(first, "project_id"), stringAt(second, "project_id"), stringAt(third, "project_id")]).toEqual(["project-welle-zwei", "project-beta-welle-zwei", "project-welle-zwei"])
    expect([stringAt(first, "run_id"), stringAt(second, "run_id"), stringAt(third, "run_id")]).toEqual(["lauf-20260821-a", "lauf-beta-20260821", "lauf-20260821-a"])
    expect(stringAt(third, "created_at")).toBe(stringAt(first, "created_at"))
    const diagnosticCalls = fixture.state.calls.filter((call) => call.includes("/diagnostic-traces"))
    const firstClose = diagnosticCalls.findIndex((call) => call.endsWith("/close"))
    const secondStart = diagnosticCalls.findIndex((call, index) => index > firstClose && call.endsWith("/diagnostic-traces"))
    expect(firstClose).toBeGreaterThan(0)
    expect(secondStart).toBeGreaterThan(firstClose)
    expect(diagnosticCalls.filter((call) => call.endsWith("/close"))).toHaveLength(2)
  })
})
