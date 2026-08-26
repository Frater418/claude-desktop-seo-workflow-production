import { useCallback, useMemo, useRef } from "react"
import type { DiagnosticTraceCloseRequest, DiagnosticTraceStart } from "./generated/api-types"
import { createDiagnosticTraceClient, type DiagnosticTrace } from "./api/diagnosticTraceClient"
import { createOperatorApiClient } from "./api/client"
import type { CurrentRun } from "./api/readModels"
import { DiagnosticTraceProvider } from "./app/DiagnosticTraceProvider"
import { OperatorShell } from "./app/OperatorShell"
import { ProjectStart } from "./app/ProjectStart"
import { useOperatorWorkspace } from "./app/useOperatorWorkspace"

type AppProps = { readonly baseUrl?: string; readonly search?: string; readonly tenantId?: string }
type DiagnosticSessionConfig = { readonly scenarioId: string; readonly source: DiagnosticTraceStart["source"] }
type ConfiguredAppProps = { readonly baseUrl: string; readonly diagnosticConfig: DiagnosticSessionConfig; readonly tenantId: string }
type DiagnosticSession = { readonly createCloseRequest: (trace: DiagnosticTrace) => DiagnosticTraceCloseRequest; readonly start: DiagnosticTraceStart | undefined }

const canonicalScenarioSlug = /^[a-z][a-z0-9-]{2,127}$/
const configurationMessages = {
  ERROR_DIAGNOSTIC_PARAMETER_DUPLICATE: "Ein Diagnoseparameter darf nur einmal gesetzt sein.",
  ERROR_DIAGNOSTIC_SCENARIO_INVALID: "diagnostic_scenario muss ein kanonischer Slug sein.",
  ERROR_DIAGNOSTIC_SOURCE_INVALID: "diagnostic_source muss manual oder automated sein.",
} as const

type DiagnosticConfigurationErrorCode = keyof typeof configurationMessages

export class DiagnosticConfigurationError extends Error {
  public readonly name = "DiagnosticConfigurationError"

  public constructor(public readonly code: DiagnosticConfigurationErrorCode) {
    super(configurationMessages[code])
  }
}

function diagnosticParameter(parameters: URLSearchParams, name: string): string | null {
  const values = parameters.getAll(name)
  if (values.length === 0) return null
  if (values.length === 1) return values.at(0) ?? null
  throw new DiagnosticConfigurationError("ERROR_DIAGNOSTIC_PARAMETER_DUPLICATE")
}

function diagnosticConfig(search: string): DiagnosticSessionConfig {
  const parameters = new URLSearchParams(search)
  const source = diagnosticParameter(parameters, "diagnostic_source")
  const scenarioId = diagnosticParameter(parameters, "diagnostic_scenario")
  let parsedSource: DiagnosticTraceStart["source"]
  switch (source) {
    case null:
      parsedSource = "manual"
      break
    case "manual":
    case "automated":
      parsedSource = source
      break
    default:
      throw new DiagnosticConfigurationError("ERROR_DIAGNOSTIC_SOURCE_INVALID")
  }
  if (scenarioId !== null && !canonicalScenarioSlug.test(scenarioId)) throw new DiagnosticConfigurationError("ERROR_DIAGNOSTIC_SCENARIO_INVALID")
  return { scenarioId: scenarioId ?? "manual-walkthrough", source: parsedSource }
}

function utcSeconds(date: Date): string {
  return date.toISOString().replace(/\.\d{3}Z$/, "Z")
}

function canonicalIdentity(run: CurrentRun): string {
  return [run.tenant_id, run.project_id, run.run_id].join("\u0000")
}

function closeId(trace: DiagnosticTrace, closedAt: string): string {
  return `close-${trace.trace_id.slice("trace-".length)}-${closedAt.replace(/\D/g, "")}`
}

function useDiagnosticSession(config: DiagnosticSessionConfig, currentRun: CurrentRun | null): DiagnosticSession {
  const createdAtByIdentity = useRef(new Map<string, string>())
  const closeRequestsByTraceId = useRef(new Map<string, DiagnosticTraceCloseRequest>())
  const createCloseRequest = useCallback((trace: DiagnosticTrace): DiagnosticTraceCloseRequest => {
    const existing = closeRequestsByTraceId.current.get(trace.trace_id)
    if (existing !== undefined) return existing
    const closedAt = utcSeconds(new Date())
    const request = { close_id: closeId(trace, closedAt), closed_at: closedAt } satisfies DiagnosticTraceCloseRequest
    closeRequestsByTraceId.current.set(trace.trace_id, request)
    return request
  }, [])
  const start = useMemo<DiagnosticTraceStart | undefined>(() => {
    if (currentRun === null) return undefined
    const identity = canonicalIdentity(currentRun)
    const createdAt = createdAtByIdentity.current.get(identity) ?? utcSeconds(new Date())
    createdAtByIdentity.current.set(identity, createdAt)
    return { created_at: createdAt, project_id: currentRun.project_id, run_id: currentRun.run_id, scenario_id: config.scenarioId, schema_version: "1.0.0", source: config.source, tenant_id: currentRun.tenant_id }
  }, [config, currentRun])
  return { createCloseRequest, start }
}

function ConfiguredApp({ baseUrl, diagnosticConfig: configuration, tenantId }: ConfiguredAppProps): JSX.Element {
  const api = useMemo(() => createOperatorApiClient({ baseUrl, tenantId }), [baseUrl, tenantId])
  const diagnosticClient = useMemo(() => createDiagnosticTraceClient({ baseUrl }), [baseUrl])
  const workspace = useOperatorWorkspace(api)
  const state = workspace.state
  const currentRun = state.kind === "ready" ? state.data.currentRun : null
  const diagnosticSession = useDiagnosticSession(configuration, currentRun)
  if (state.kind === "loading") return <main className="api-status"><p className="eyebrow">Heartweb Admin Operator</p><h1>Lokale Arbeitsdaten werden geladen</h1><p>Projekt, Workflow, Aufgaben und Nachweise werden aus der lokalen Operator-API gelesen.</p></main>
  if (state.kind === "empty") return <ProjectStart api={api} onAccepted={workspace.selectProject} onProjectDeleted={async () => workspace.reload()} />
  if (state.kind === "overview") return <ProjectStart api={api} onAccepted={workspace.selectProject} onProjectDeleted={async () => workspace.reload()} onOpenProject={workspace.selectProject} projects={workspace.projects} />
  if (state.kind === "error") return <main className="api-status"><p className="eyebrow">Heartweb Admin Operator</p><h1>{state.title}</h1><p>{state.message}</p><p>Es werden keine Demo-Daten angezeigt und keine Projektdaten verändert.</p><button className="button-primary" type="button" onClick={() => { void workspace.reload().catch(() => undefined) }}>Erneut laden</button></main>
  return <DiagnosticTraceProvider client={diagnosticClient} createCloseRequest={diagnosticSession.createCloseRequest} start={diagnosticSession.start}><OperatorShell api={api} data={state.data} onDeselectProject={workspace.deselectProject} onRefresh={workspace.reload} /></DiagnosticTraceProvider>
}

export function App({ baseUrl, search, tenantId }: AppProps): JSX.Element {
  const configuredTenantId = tenantId ?? import.meta.env["VITE_OPERATOR_TENANT_ID"]
  if (configuredTenantId === undefined || configuredTenantId === "") return <main className="api-status"><p className="eyebrow">Heartweb Admin Operator</p><h1>Operator-Konfiguration unvollstaendig</h1><p>VITE_OPERATOR_TENANT_ID muss gesetzt sein, bevor die lokale Operator-API gelesen wird.</p></main>
  try {
    return <ConfiguredApp baseUrl={baseUrl ?? import.meta.env["VITE_OPERATOR_API_BASE_URL"] ?? ""} diagnosticConfig={diagnosticConfig(search ?? window.location.search)} tenantId={configuredTenantId} />
  } catch (error) {
    if (error instanceof DiagnosticConfigurationError) return <main className="api-status"><p className="eyebrow">Heartweb Admin Operator</p><h1>Operator-Konfiguration ungueltig</h1><p>{error.message}</p></main>
    throw error
  }
}
