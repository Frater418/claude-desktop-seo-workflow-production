import { afterEach, describe, expect, it, vi } from "vitest"
import type {
  DiagnosticTraceCloseRequest,
  DiagnosticTraceCloseResponse,
  DiagnosticTraceEntryResponse,
  DiagnosticTraceOperation,
  DiagnosticTraceStart,
  DiagnosticTraceStartResponse,
} from "../generated/api-types"
import { OperatorApiError } from "./operatorApiError"
import { createDiagnosticTraceClient, type DiagnosticTrace, type DiagnosticTraceClient } from "./diagnosticTraceClient"

afterEach(() => {
  vi.unstubAllGlobals()
})

function json(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), { status, headers: { "Content-Type": "application/json" } })
}

const start = {
  schema_version: "1.0.0",
  tenant_id: "tenant-acme",
  project_id: "project-alpha",
  run_id: "run-20260822",
  scenario_id: "scenario-operator-manual-m07",
  source: "manual",
  created_at: "2026-08-22T10:15:30Z",
} satisfies DiagnosticTraceStart

const traceResponse = {
  tenant_id: start.tenant_id,
  project_id: start.project_id,
  run_id: start.run_id,
  scenario_id: start.scenario_id,
  source: start.source,
  created_at: start.created_at,
  trace_id: "trace-0123456789abcdef0123456789abcdef",
  status: "active",
  replay: false,
} satisfies DiagnosticTraceStartResponse
const trace = { ...traceResponse, schema_version: start.schema_version } satisfies DiagnosticTrace

const entry = {
  operation_id: "operation-create-delivery-0001",
  occurred_at: "2026-08-22T10:16:00Z",
  action: "create_delivery",
  route: "/v1/tenants/tenant-acme/projects/project-alpha/delivery/exports",
  api_method: "POST",
  api_status: 201,
  expected_actions: ["create_delivery"],
  rendered_actions: ["create_delivery"],
  disabled_actions: [],
  evidence_references: [],
} satisfies DiagnosticTraceOperation

const closeRequest = {
  close_id: "close-diagnostic-trace-0001",
  closed_at: "2026-08-22T10:17:00Z",
} satisfies DiagnosticTraceCloseRequest

const closeResponse = {
  trace_id: trace.trace_id,
  ...closeRequest,
  status: "closed",
  replay: false,
  last_successful_operation_id: entry.operation_id,
  first_failing_operation_id: null,
} satisfies DiagnosticTraceCloseResponse

type ClientRequest = (client: DiagnosticTraceClient, signal: AbortSignal) => Promise<unknown>
type InvalidTraceResponse = {
  readonly label: string
  readonly request: ClientRequest
  readonly payload: unknown
}

const malformedTraceResponses: readonly InvalidTraceResponse[] = [
  { label: "create status", request: (client, signal) => client.create({ start, signal }), payload: { ...traceResponse, status: "closed" } },
  { label: "create trace ID", request: (client, signal) => client.create({ start, signal }), payload: { ...traceResponse, trace_id: "trace-invalid" } },
  { label: "append", request: (client, signal) => client.append({ trace, entry, signal }), payload: { trace_id: trace.trace_id, operation_id: entry.operation_id, sequence: "1", replay: false } },
  { label: "close", request: (client, signal) => client.close({ trace, request: closeRequest, signal, keepalive: false }), payload: { ...closeResponse, status: "active" } },
]

const mismatchedTraceResponses: readonly InvalidTraceResponse[] = [
  { label: "create tenant", request: (client, signal) => client.create({ start, signal }), payload: { ...traceResponse, tenant_id: "tenant-other" } },
  { label: "create project", request: (client, signal) => client.create({ start, signal }), payload: { ...traceResponse, project_id: "project-other" } },
  { label: "create run", request: (client, signal) => client.create({ start, signal }), payload: { ...traceResponse, run_id: "run-20260823" } },
  { label: "create scenario", request: (client, signal) => client.create({ start, signal }), payload: { ...traceResponse, scenario_id: "scenario-operator-manual-m08" } },
  { label: "create source", request: (client, signal) => client.create({ start, signal }), payload: { ...traceResponse, source: "automated" } },
  { label: "create timestamp", request: (client, signal) => client.create({ start, signal }), payload: { ...traceResponse, created_at: "2026-08-22T10:15:31Z" } },
  { label: "append trace", request: (client, signal) => client.append({ trace, entry, signal }), payload: { trace_id: "trace-fedcba9876543210fedcba9876543210", operation_id: entry.operation_id, sequence: 1, replay: false } },
  { label: "append operation", request: (client, signal) => client.append({ trace, entry, signal }), payload: { trace_id: trace.trace_id, operation_id: "operation-create-delivery-0002", sequence: 1, replay: false } },
  { label: "close trace", request: (client, signal) => client.close({ trace, request: closeRequest, signal, keepalive: false }), payload: { ...closeResponse, trace_id: "trace-fedcba9876543210fedcba9876543210" } },
  { label: "close ID", request: (client, signal) => client.close({ trace, request: closeRequest, signal, keepalive: false }), payload: { ...closeResponse, close_id: "close-diagnostic-trace-0002" } },
  { label: "close timestamp", request: (client, signal) => client.close({ trace, request: closeRequest, signal, keepalive: false }), payload: { ...closeResponse, closed_at: "2026-08-22T10:17:01Z" } },
]

describe("DiagnosticTraceClient", () => {
  it("posts encoded create, append, and close requests while accepting first and replay responses", async () => {
    const responses = [
      json(traceResponse, 201),
      json({ ...traceResponse, replay: true }),
      json({ trace_id: trace.trace_id, operation_id: entry.operation_id, sequence: 1, replay: false }, 201),
      json({ trace_id: trace.trace_id, operation_id: entry.operation_id, sequence: 1, replay: true }),
      json(closeResponse),
    ]
    const fetch = vi.fn(() => Promise.resolve(responses.shift() ?? json({})))
    vi.stubGlobal("fetch", fetch)
    const signal = new AbortController().signal
    const client = createDiagnosticTraceClient({ baseUrl: "https://operator.example/" })

    await expect(client.create({ start, signal })).resolves.toEqual(trace)
    await expect(client.create({ start, signal })).resolves.toEqual({ ...trace, replay: true })
    await expect(client.append({ trace, entry, signal })).resolves.toEqual({ trace_id: trace.trace_id, operation_id: entry.operation_id, sequence: 1, replay: false })
    await expect(client.append({ trace, entry, signal })).resolves.toEqual({ trace_id: trace.trace_id, operation_id: entry.operation_id, sequence: 1, replay: true })
    await expect(client.close({ trace, request: closeRequest, signal, keepalive: true })).resolves.toEqual(closeResponse)

    const base = "https://operator.example/v1/tenants/tenant-acme/projects/project-alpha/diagnostic-traces"
    expect(fetch).toHaveBeenNthCalledWith(1, base, expect.objectContaining({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(start), signal }))
    expect(fetch).toHaveBeenNthCalledWith(3, `${base}/trace-0123456789abcdef0123456789abcdef/entries`, expect.objectContaining({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(entry), signal }))
    expect(fetch).toHaveBeenNthCalledWith(5, `${base}/trace-0123456789abcdef0123456789abcdef/close`, expect.objectContaining({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(closeRequest), signal, keepalive: true }))
  })

  it("preserves the stable ErrorEnvelope code on OperatorApiError", async () => {
    const fetch = vi.fn(() => Promise.resolve(json({ code: "ERROR_DIAGNOSTIC_TRACE_CONFLICT", message: "Die Diagnose-Trace ist bereits geschlossen." }, 409)))
    vi.stubGlobal("fetch", fetch)
    const client = createDiagnosticTraceClient({ baseUrl: "" })
    const rejected = client.append({ trace, entry, signal: new AbortController().signal })

    await expect(rejected).rejects.toBeInstanceOf(OperatorApiError)
    await expect(rejected).rejects.toMatchObject({ kind: "http", status: 409, code: "ERROR_DIAGNOSTIC_TRACE_CONFLICT", message: "Die Diagnose-Trace ist bereits geschlossen." })
  })

  for (const malformed of malformedTraceResponses) {
    it(`rejects an invalid successful ${malformed.label} payload as unparseable`, async () => {
      vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(json(malformed.payload))))
      const client = createDiagnosticTraceClient({ baseUrl: "" })

      await expect(malformed.request(client, new AbortController().signal)).rejects.toMatchObject({ kind: "unparseable", status: 200 })
    })
  }

  for (const mismatched of mismatchedTraceResponses) {
    it(`rejects a successful ${mismatched.label} response that is not bound to its request`, async () => {
      vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(json(mismatched.payload))))
      const client = createDiagnosticTraceClient({ baseUrl: "" })

      await expect(mismatched.request(client, new AbortController().signal)).rejects.toMatchObject({ kind: "unparseable", status: 200 })
    })
  }
})
