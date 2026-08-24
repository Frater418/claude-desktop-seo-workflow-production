import { afterEach, describe, expect, it } from "vitest"
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import type {
  DiagnosticTraceCloseRequest,
  DiagnosticTraceCloseResponse,
  DiagnosticTraceEntryResponse,
  DiagnosticTraceOperation,
  DiagnosticTraceStart,
  DiagnosticTraceStartResponse,
} from "../generated/api-types"
import type { DiagnosticTrace, DiagnosticTraceClient } from "../api/diagnosticTraceClient"
import { OperatorApiError } from "../api/operatorApiError"
import { DiagnosticTraceProvider, DiagnosticTraceProviderError, DiagnosticTraceStatus, type DiagnosticTraceReporter, useDiagnosticTrace } from "./DiagnosticTraceProvider"

afterEach(cleanup)

const start = {
  schema_version: "1.0.0",
  tenant_id: "tenant-acme",
  project_id: "project-alpha",
  run_id: "run-0001",
  scenario_id: "scenario-operator-manual-m07",
  source: "manual",
  created_at: "2026-08-22T10:15:30Z",
} satisfies DiagnosticTraceStart

const successorStart = {
  ...start,
  project_id: "project-bravo",
  run_id: "run-0002",
  scenario_id: "scenario-operator-retry-m07",
  created_at: "2026-08-22T10:20:00Z",
} satisfies DiagnosticTraceStart

const trace = {
  ...start,
  trace_id: "trace-0123456789abcdef0123456789abcdef",
  status: "active",
  replay: false,
} satisfies DiagnosticTraceStartResponse

const successorTrace = {
  ...successorStart,
  trace_id: "trace-fedcba9876543210fedcba9876543210",
  status: "active",
  replay: false,
} satisfies DiagnosticTraceStartResponse

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

const successorCloseRequest = {
  close_id: "close-diagnostic-trace-0002",
  closed_at: "2026-08-22T10:21:00Z",
} satisfies DiagnosticTraceCloseRequest

function closeRequestFor(activeTrace: DiagnosticTrace): DiagnosticTraceCloseRequest {
  return activeTrace.trace_id === successorTrace.trace_id ? successorCloseRequest : closeRequest
}

const closeResponse = {
  trace_id: trace.trace_id,
  ...closeRequest,
  status: "closed",
  replay: false,
  last_successful_operation_id: entry.operation_id,
  first_failing_operation_id: null,
} satisfies DiagnosticTraceCloseResponse

const entryResponse = {
  trace_id: trace.trace_id,
  operation_id: entry.operation_id,
  sequence: 1,
  replay: false,
} satisfies DiagnosticTraceEntryResponse

function traceClient(overrides: Partial<DiagnosticTraceClient> = {}): DiagnosticTraceClient {
  return {
    create: overrides.create ?? (async () => trace),
    append: overrides.append ?? (async () => entryResponse),
    close: overrides.close ?? (async () => closeResponse),
  }
}

function ReporterControls(): JSX.Element {
  const reporter = useDiagnosticTrace()
  return <><button type="button" onClick={() => { void reporter.record(entry).then(() => undefined, () => undefined) }}>Eintrag schreiben</button><button type="button" onClick={() => { void reporter.close().then(() => undefined, () => undefined) }}>Trace schliessen</button><DiagnosticTraceStatus /></>
}

function MissingProviderConsumer(): JSX.Element {
  useDiagnosticTrace()
  return <p>Unzulaessig</p>
}

type ReporterCapture = { reporter: DiagnosticTraceReporter | null }

function CapturedReporter({ capture }: { readonly capture: ReporterCapture }): null {
  capture.reporter = useDiagnosticTrace()
  return null
}

function reporterFrom(capture: ReporterCapture): DiagnosticTraceReporter {
  if (capture.reporter === null) throw new DiagnosticTraceProviderError("ERROR_DIAGNOSTIC_TRACE_PROVIDER_MISSING")
  return capture.reporter
}

describe("DiagnosticTraceProvider", () => {
  it("fails visibly with a typed error when a reporter has no provider", () => {
    expect(() => render(<MissingProviderConsumer />)).toThrow(DiagnosticTraceProviderError)
  })

  it("rejects record and close before a trace is active with a stable code", async () => {
    const capture: ReporterCapture = { reporter: null }
    render(<DiagnosticTraceProvider client={traceClient()} createCloseRequest={closeRequestFor}><CapturedReporter capture={capture} /><DiagnosticTraceStatus /></DiagnosticTraceProvider>)
    const reporter = reporterFrom(capture)

    await expect(reporter.record(entry)).rejects.toMatchObject({ name: "DiagnosticTraceProviderError", code: "ERROR_DIAGNOSTIC_TRACE_NOT_ACTIVE" })
    await expect(reporter.close()).rejects.toMatchObject({ name: "DiagnosticTraceProviderError", code: "ERROR_DIAGNOSTIC_TRACE_NOT_ACTIVE" })
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Diagnoseprotokoll ist nicht aktiv. ERROR_DIAGNOSTIC_TRACE_NOT_ACTIVE"))
  })

  it("starts only from caller-supplied identity, records operations, and accepts an explicit replay close", async () => {
    const starts: Parameters<DiagnosticTraceClient["create"]>[0][] = []
    const appends: Parameters<DiagnosticTraceClient["append"]>[0][] = []
    const closes: Parameters<DiagnosticTraceClient["close"]>[0][] = []
    const client = traceClient({
      create: async (input) => { starts.push(input); return trace },
      append: async (input) => { appends.push(input); return entryResponse },
      close: async (input) => { closes.push(input); return { ...closeResponse, replay: true } },
    })
    const view = render(<DiagnosticTraceProvider client={client} createCloseRequest={closeRequestFor}><ReporterControls /></DiagnosticTraceProvider>)

    expect(starts).toHaveLength(0)
    view.rerender(<DiagnosticTraceProvider client={client} start={start} createCloseRequest={closeRequestFor}><ReporterControls /></DiagnosticTraceProvider>)
    await waitFor(() => expect(starts).toEqual([expect.objectContaining({ start, signal: expect.any(AbortSignal) })]))
    expect(screen.getByRole("status")).toHaveTextContent("Diagnoseprotokoll aktiv.")

    fireEvent.click(screen.getByRole("button", { name: "Eintrag schreiben" }))
    await waitFor(() => expect(appends).toEqual([expect.objectContaining({ trace, entry, signal: expect.any(AbortSignal) })]))
    fireEvent.click(screen.getByRole("button", { name: "Trace schliessen" }))
    await waitFor(() => expect(closes).toEqual([expect.objectContaining({ trace, request: closeRequest, signal: expect.any(AbortSignal), keepalive: false })]))
    expect(screen.getByRole("status")).toHaveTextContent("Diagnoseprotokoll geschlossen.")

    fireEvent.click(screen.getByRole("button", { name: "Trace schliessen" }))
    expect(closes).toHaveLength(1)
  })

  it("closes the old identity before starting another one and fails visibly rather than overlapping after a close error", async () => {
    const calls: string[] = []
    const client = traceClient({
      create: async ({ start: requestedStart }) => {
        calls.push(`create:${requestedStart.run_id}`)
        return requestedStart.run_id === start.run_id ? trace : successorTrace
      },
      close: async ({ trace: closingTrace }) => {
        calls.push(`close:${closingTrace.trace_id}`)
        return closeResponse
      },
    })
    const view = render(<DiagnosticTraceProvider client={client} start={start} createCloseRequest={closeRequestFor}><ReporterControls /></DiagnosticTraceProvider>)

    await waitFor(() => expect(calls).toEqual(["create:run-0001"]))
    view.rerender(<DiagnosticTraceProvider client={client} start={successorStart} createCloseRequest={closeRequestFor}><ReporterControls /></DiagnosticTraceProvider>)
    await waitFor(() => expect(calls).toEqual(["create:run-0001", "close:trace-0123456789abcdef0123456789abcdef", "create:run-0002"]))
    view.unmount()

    const closeFailure = Object.assign(new OperatorApiError({ kind: "http", status: 503, message: "Diagnose-Speicher nicht verfuegbar." }), { code: "ERROR_DIAGNOSTIC_TRACE_UNAVAILABLE" })
    const failedCalls: string[] = []
    const failingClient = traceClient({
      create: async ({ start: requestedStart }) => {
        failedCalls.push(`create:${requestedStart.run_id}`)
        return requestedStart.run_id === start.run_id ? trace : successorTrace
      },
      close: async ({ trace: closingTrace }) => {
        failedCalls.push(`close:${closingTrace.trace_id}`)
        throw closeFailure
      },
    })
    const failedView = render(<DiagnosticTraceProvider client={failingClient} start={start} createCloseRequest={closeRequestFor}><ReporterControls /></DiagnosticTraceProvider>)

    await waitFor(() => expect(failedCalls).toEqual(["create:run-0001"]))
    failedView.rerender(<DiagnosticTraceProvider client={failingClient} start={successorStart} createCloseRequest={closeRequestFor}><ReporterControls /></DiagnosticTraceProvider>)
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Diagnoseprotokoll konnte nicht geschlossen werden. ERROR_DIAGNOSTIC_TRACE_UNAVAILABLE"))
    expect(failedCalls).toEqual(["create:run-0001", "close:trace-0123456789abcdef0123456789abcdef"])
  })

  it("uses the same close request with keepalive on pagehide", async () => {
    const closes: Parameters<DiagnosticTraceClient["close"]>[0][] = []
    const client = traceClient({ close: async (input) => { closes.push(input); return closeResponse } })
    render(<DiagnosticTraceProvider client={client} start={start} createCloseRequest={closeRequestFor}><ReporterControls /></DiagnosticTraceProvider>)

    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Diagnoseprotokoll aktiv."))
    act(() => { window.dispatchEvent(new Event("pagehide")) })
    await waitFor(() => expect(closes).toEqual([expect.objectContaining({ trace, request: closeRequest, signal: expect.any(AbortSignal), keepalive: true })]))
  })

  it("renders German start, write, and close failures with stable codes instead of success", async () => {
    const failure = Object.assign(new OperatorApiError({ kind: "http", status: 503, message: "Diagnose-Speicher nicht verfuegbar." }), { code: "ERROR_DIAGNOSTIC_TRACE_UNAVAILABLE" })
    const startView = render(<DiagnosticTraceProvider client={traceClient({ create: async () => { throw failure } })} start={start} createCloseRequest={closeRequestFor}><ReporterControls /></DiagnosticTraceProvider>)

    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Diagnoseprotokoll konnte nicht gestartet werden. ERROR_DIAGNOSTIC_TRACE_UNAVAILABLE"))
    startView.unmount()
    const writeView = render(<DiagnosticTraceProvider client={traceClient({ append: async () => { throw failure } })} start={start} createCloseRequest={closeRequestFor}><ReporterControls /></DiagnosticTraceProvider>)
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Diagnoseprotokoll aktiv."))
    fireEvent.click(screen.getByRole("button", { name: "Eintrag schreiben" }))
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Diagnoseeintrag konnte nicht geschrieben werden. ERROR_DIAGNOSTIC_TRACE_UNAVAILABLE"))
    expect(screen.getByRole("status")).not.toHaveTextContent("Diagnoseprotokoll geschlossen.")
    writeView.unmount()
    render(<DiagnosticTraceProvider client={traceClient({ close: async () => { throw failure } })} start={start} createCloseRequest={closeRequestFor}><ReporterControls /></DiagnosticTraceProvider>)
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Diagnoseprotokoll aktiv."))
    fireEvent.click(screen.getByRole("button", { name: "Trace schliessen" }))
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Diagnoseprotokoll konnte nicht geschlossen werden. ERROR_DIAGNOSTIC_TRACE_UNAVAILABLE"))
    expect(screen.getByRole("status")).not.toHaveTextContent("Diagnoseprotokoll geschlossen.")
  })

  it("creates a close request only at first close and reuses it for pagehide retry", async () => {
    // Given: an active trace whose first close transport attempt fails.
    const closeFailure = new OperatorApiError({ kind: "network", message: "Diagnose-Speicher nicht verfuegbar.", status: 0 })
    const closeRequests: DiagnosticTrace[] = []
    const closes: Parameters<DiagnosticTraceClient["close"]>[0][] = []
    const client = traceClient({
      close: async (input) => {
        closes.push(input)
        if (closes.length === 1) throw closeFailure
        return { ...closeResponse, close_id: input.request.close_id, closed_at: input.request.closed_at }
      },
    })
    const createCloseRequest = (activeTrace: DiagnosticTrace): DiagnosticTraceCloseRequest => {
      closeRequests.push(activeTrace)
      return closeRequest
    }
    render(<DiagnosticTraceProvider client={client} start={start} createCloseRequest={createCloseRequest}><ReporterControls /></DiagnosticTraceProvider>)
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Diagnoseprotokoll aktiv."))
    expect(closeRequests).toEqual([])

    // When: the operator closes the trace and the browser later emits pagehide.
    fireEvent.click(screen.getByRole("button", { name: "Trace schliessen" }))
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Diagnoseprotokoll konnte nicht geschlossen werden. ERROR_DIAGNOSTIC_TRACE_NETWORK"))
    act(() => { window.dispatchEvent(new Event("pagehide")) })
    await waitFor(() => expect(closes).toHaveLength(2))

    // Then: first-close time generated one request object before transport and the retry reused it.
    expect(closeRequests).toEqual([trace])
    expect(closes.map((input) => input.request)).toEqual([closeRequest, closeRequest])
    expect(closes.map((input) => input.keepalive)).toEqual([false, true])
  })
})
