import { useMemo } from "react"
import { createOperatorApiClient } from "./api/client"
import { OperatorShell } from "./app/OperatorShell"
import { useOperatorWorkspace } from "./app/useOperatorWorkspace"

type AppProps = { readonly baseUrl?: string; readonly search?: string; readonly tenantId?: string }
type ConfiguredAppProps = { readonly baseUrl: string; readonly tenantId: string }

function ConfiguredApp({ baseUrl, tenantId }: ConfiguredAppProps): JSX.Element {
  const api = useMemo(() => createOperatorApiClient({ baseUrl, tenantId }), [baseUrl, tenantId])
  const workspace = useOperatorWorkspace(api)
  const state = workspace.state
  if (state.kind === "loading") return <main className="api-status"><p className="eyebrow">Heartweb Admin Operator</p><h1>Lokale Arbeitsdaten werden geladen</h1><p>Projekt, Workflow, Aufgaben und Nachweise werden aus der lokalen Operator-API gelesen.</p></main>
  if (state.kind === "empty") return <main className="api-status"><p className="eyebrow">Heartweb Admin Operator</p><h1>Kein lokales Projekt vorhanden</h1><p>Ein Projekt kann nach dem Verbindungscheck aus einem Markdown-Briefing angelegt werden.</p></main>
  if (state.kind === "error") return <main className="api-status"><p className="eyebrow">Heartweb Admin Operator</p><h1>Lokale Operator-API nicht verfuegbar</h1><p>{state.message}</p><p>Es werden keine Demo-Daten angezeigt.</p></main>
  return <OperatorShell api={api} data={state.data} onRefresh={workspace.reload} onIntakeAccepted={workspace.selectProject} projects={workspace.projects} selectedProjectId={workspace.selectedProjectId ?? state.data.projectId} selectProject={workspace.selectProject} />
}

export function App({ baseUrl, tenantId }: AppProps): JSX.Element {
  const configuredTenantId = tenantId ?? import.meta.env["VITE_OPERATOR_TENANT_ID"]
  if (configuredTenantId === undefined || configuredTenantId === "") return <main className="api-status"><p className="eyebrow">Heartweb Admin Operator</p><h1>Operator-Konfiguration unvollstaendig</h1><p>VITE_OPERATOR_TENANT_ID muss gesetzt sein, bevor die lokale Operator-API gelesen wird.</p></main>
  return <ConfiguredApp baseUrl={baseUrl ?? import.meta.env["VITE_OPERATOR_API_BASE_URL"] ?? ""} tenantId={configuredTenantId} />
}
