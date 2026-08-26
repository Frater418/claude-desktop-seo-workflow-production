import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react"
import type { ReactNode } from "react"
import type { DiagnosticTraceCloseRequest, DiagnosticTraceOperation, DiagnosticTraceStart } from "../generated/api-types"
import type { DiagnosticTrace, DiagnosticTraceClient } from "../api/diagnosticTraceClient"
import { OperatorApiError } from "../api/operatorApiError"

type DiagnosticTraceProviderProps = {
  readonly client: DiagnosticTraceClient
  readonly start?: DiagnosticTraceStart | undefined
  readonly createCloseRequest: DiagnosticTraceCloseRequestFactory
  readonly children: ReactNode
}
export type DiagnosticTraceCloseRequestFactory = (trace: DiagnosticTrace) => DiagnosticTraceCloseRequest
type ActiveTrace = {
  readonly client: DiagnosticTraceClient
  readonly createCloseRequest: DiagnosticTraceCloseRequestFactory
  readonly closeRequest: DiagnosticTraceCloseRequest | null
  readonly identity: string
  readonly trace: DiagnosticTrace
  readonly isClosed: boolean
}
type DiagnosticTraceProviderErrorCode = "ERROR_DIAGNOSTIC_TRACE_NOT_ACTIVE" | "ERROR_DIAGNOSTIC_TRACE_PROVIDER_MISSING"
type TraceStatus =
  | { readonly kind: "starting"; readonly code?: string }
  | { readonly kind: "active" }
  | { readonly kind: "write-failed"; readonly code?: string }
  | { readonly kind: "close-failed"; readonly code?: string }
  | { readonly kind: "not-active"; readonly code: "ERROR_DIAGNOSTIC_TRACE_NOT_ACTIVE" }
  | { readonly kind: "closed" }

export type DiagnosticTraceReporter = {
  readonly record: (entry: DiagnosticTraceOperation) => Promise<void>
  readonly close: () => Promise<void>
  readonly canClose: boolean
  readonly statusKind: TraceStatus["kind"]
  readonly statusText: string
}

const DiagnosticTraceContext = createContext<DiagnosticTraceReporter | null>(null)

export class DiagnosticTraceProviderError extends Error {
  public readonly name = "DiagnosticTraceProviderError"

  public constructor(public readonly code: DiagnosticTraceProviderErrorCode) {
    super(code)
  }
}

function traceIdentity(start: DiagnosticTraceStart): string {
  return JSON.stringify([start.schema_version, start.tenant_id, start.project_id, start.run_id, start.scenario_id, start.source, start.created_at])
}

function diagnosticFailureCode(error: unknown): string | undefined {
  if (!(error instanceof OperatorApiError)) return undefined
  if (error.code !== undefined) return error.code
  switch (error.kind) {
    case "network":
      return "ERROR_DIAGNOSTIC_TRACE_NETWORK"
    case "unparseable":
      return "ERROR_DIAGNOSTIC_TRACE_UNPARSEABLE"
    case "http":
      return undefined
    default: {
      const unreachableKind: never = error.kind
      return unreachableKind
    }
  }
}

function failureStatus(kind: "starting" | "write-failed" | "close-failed", error: unknown): TraceStatus {
  const code = diagnosticFailureCode(error)
  switch (kind) {
    case "starting":
      return code === undefined ? { kind } : { kind, code }
    case "write-failed":
      return code === undefined ? { kind } : { kind, code }
    case "close-failed":
      return code === undefined ? { kind } : { kind, code }
    default: {
      const unreachableKind: never = kind
      return unreachableKind
    }
  }
}

function statusText(status: TraceStatus): string {
  switch (status.kind) {
    case "starting":
      return status.code === undefined ? "Diagnoseprotokoll wird gestartet." : `Diagnoseprotokoll konnte nicht gestartet werden. ${status.code}`
    case "active":
      return "Diagnoseprotokoll aktiv."
    case "write-failed":
      return status.code === undefined ? "Diagnoseeintrag konnte nicht geschrieben werden." : `Diagnoseeintrag konnte nicht geschrieben werden. ${status.code}`
    case "close-failed":
      return status.code === undefined ? "Diagnoseprotokoll konnte nicht geschlossen werden." : `Diagnoseprotokoll konnte nicht geschlossen werden. ${status.code}`
    case "not-active":
      return `Diagnoseprotokoll ist nicht aktiv. ${status.code}`
    case "closed":
      return "Diagnoseprotokoll geschlossen."
    default: {
      const unreachableStatus: never = status
      return unreachableStatus
    }
  }
}

function canClose(status: TraceStatus): boolean {
  switch (status.kind) {
    case "active":
    case "write-failed":
    case "close-failed":
      return true
    case "starting":
    case "not-active":
    case "closed":
      return false
    default: {
      const unreachableStatus: never = status
      return unreachableStatus
    }
  }
}

export function DiagnosticTraceProvider({ client, start, createCloseRequest, children }: DiagnosticTraceProviderProps): JSX.Element {
  const [status, setStatus] = useState<TraceStatus>({ kind: "starting" })
  const activeTraceRef = useRef<ActiveTrace | null>(null)
  const mountedRef = useRef(true)
  const queueRef = useRef<Promise<void>>(Promise.resolve())
  const startIdentity = start === undefined ? null : traceIdentity(start)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  const setVisibleStatus = useCallback((nextStatus: TraceStatus): void => {
    if (mountedRef.current) setStatus(nextStatus)
  }, [])
  const enqueue = useCallback((operation: () => Promise<void>): Promise<void> => {
    const queued = queueRef.current.then(operation, operation)
    queueRef.current = queued
    return queued
  }, [])
  const closeActive = useCallback(async (keepalive: boolean): Promise<boolean> => {
    const activeTrace = activeTraceRef.current
    if (activeTrace === null || activeTrace.isClosed) return true
    const request = activeTrace.closeRequest ?? activeTrace.createCloseRequest(activeTrace.trace)
    const traceWithCloseRequest = { ...activeTrace, closeRequest: request }
    activeTraceRef.current = traceWithCloseRequest
    try {
      await traceWithCloseRequest.client.close({ trace: traceWithCloseRequest.trace, request, signal: new AbortController().signal, keepalive })
      activeTraceRef.current = { ...traceWithCloseRequest, isClosed: true }
      setVisibleStatus({ kind: "closed" })
      return true
    } catch (error) {
      setVisibleStatus(failureStatus("close-failed", error))
      return false
    }
  }, [setVisibleStatus])
  const synchronizeTrace = useCallback(async (): Promise<void> => {
    const activeTrace = activeTraceRef.current
    if (start === undefined || startIdentity === null) {
      await closeActive(false)
      return
    }
    if (activeTrace !== null && activeTrace.identity === startIdentity) return
    if (!(await closeActive(false))) return
    setVisibleStatus({ kind: "starting" })
    try {
      const trace = await client.create({ start, signal: new AbortController().signal })
      activeTraceRef.current = {
        client,
        createCloseRequest,
        closeRequest: null,
        identity: startIdentity,
        trace,
        isClosed: false,
      }
      setVisibleStatus({ kind: "active" })
    } catch (error) {
      setVisibleStatus(failureStatus("starting", error))
    }
  }, [client, closeActive, createCloseRequest, setVisibleStatus, start, startIdentity])

  useEffect(() => {
    void enqueue(synchronizeTrace)
  }, [enqueue, synchronizeTrace])

  const record = useCallback((entry: DiagnosticTraceOperation): Promise<void> => enqueue(async () => {
    const activeTrace = activeTraceRef.current
    if (activeTrace === null || activeTrace.isClosed) {
      const error = new DiagnosticTraceProviderError("ERROR_DIAGNOSTIC_TRACE_NOT_ACTIVE")
      setVisibleStatus({ kind: "not-active", code: "ERROR_DIAGNOSTIC_TRACE_NOT_ACTIVE" })
      throw error
    }
    try {
      await activeTrace.client.append({ trace: activeTrace.trace, entry, signal: new AbortController().signal })
      setVisibleStatus({ kind: "active" })
    } catch (error) {
      setVisibleStatus(failureStatus("write-failed", error))
    }
  }), [enqueue, setVisibleStatus])
  const close = useCallback((): Promise<void> => enqueue(async () => {
    if (activeTraceRef.current === null || activeTraceRef.current.isClosed) {
      const error = new DiagnosticTraceProviderError("ERROR_DIAGNOSTIC_TRACE_NOT_ACTIVE")
      setVisibleStatus({ kind: "not-active", code: "ERROR_DIAGNOSTIC_TRACE_NOT_ACTIVE" })
      throw error
    }
    await closeActive(false)
  }), [closeActive, enqueue, setVisibleStatus])

  useEffect(() => {
    const closeOnPageHide = (): void => {
      void enqueue(async () => {
        await closeActive(true)
      })
    }
    window.addEventListener("pagehide", closeOnPageHide)
    return () => window.removeEventListener("pagehide", closeOnPageHide)
  }, [closeActive, enqueue])

  useEffect(() => () => {
    void enqueue(async () => {
      await closeActive(true)
    })
  }, [closeActive, enqueue])

  const reporter = useMemo<DiagnosticTraceReporter>(() => ({ canClose: canClose(status), close, record, statusKind: status.kind, statusText: statusText(status) }), [close, record, status])
  return <DiagnosticTraceContext.Provider value={reporter}>{children}</DiagnosticTraceContext.Provider>
}

export function useDiagnosticTrace(): DiagnosticTraceReporter {
  const reporter = useContext(DiagnosticTraceContext)
  if (reporter === null) throw new DiagnosticTraceProviderError("ERROR_DIAGNOSTIC_TRACE_PROVIDER_MISSING")
  return reporter
}

export function DiagnosticTraceStatus(): JSX.Element {
  const reporter = useDiagnosticTrace()
  return <section aria-label="Automatische Diagnose" className="diagnostic-trace-status" data-state={reporter.statusKind}><p role="status">{reporter.statusText}</p><p>Die technische Aktionshistorie wird automatisch geführt. Es ist keine Bedienung erforderlich.</p></section>
}
