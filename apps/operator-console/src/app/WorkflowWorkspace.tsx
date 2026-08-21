import type { OperatorWorkspaceData } from "./useOperatorWorkspace"
import type { ActionIntent } from "../generated/api-types"
import { PersistentActionArea } from "./PersistentActionArea"
import { useAdminAction } from "./useAdminAction"

export function WorkflowWorkspace({ data }: { readonly data: OperatorWorkspaceData }): JSX.Element {
  const step = data.current.step
  const gate = data.current.gate
  const status = step === null ? "Aktueller Schritt nicht verfuegbar" : step.status === "in_progress" ? "In Bearbeitung" : step.status
  const action = useAdminAction({ client: data.actionClient, reload: data.reload })
  const intent: ActionIntent = { action: "start", tenant_id: data.currentRun.tenant_id, project_id: data.projectId, run_id: data.currentRun.run_id, step_id: data.currentRun.step_id, expected_revision: data.currentRun.expected_revision }
  return <section className="work-panel workflow-workspace"><div className="work-heading"><div><p className="eyebrow">Workflow</p><h2>Aktiver Arbeitsschritt</h2></div><span className="status-badge">{status}</span></div><ol aria-label="Initiale Workflow-Schritte" className="workflow-route"><li>0</li><li>1</li><li>1b</li><li>1c</li><li>2</li><li>3</li><li>4a</li><li>4b</li></ol><p className="sideflow-note">3b: noch nicht faellig</p><div className="facts"><div><span>Blocker</span><strong>{step === null ? "Aktueller Blocker nicht verfuegbar" : step.blocker}</strong></div><div><span>Naechste Aktion</span><strong>{step === null ? "Aktuelle Aktion nicht verfuegbar" : step.nextAction}</strong></div></div><section className="gate-report"><h3>Maschinenpruefung</h3><p>{gate === null ? "Aktueller Pruefbericht nicht verfuegbar" : gate.summary}</p></section><PersistentActionArea state={action.state} onPreview={() => { void action.preview(intent) }} onConfirm={() => { void action.confirm() }} /><section aria-label="Lokale Integrationen" className="integration-labels">{data.integrations.map((integration) => <p key={integration.name}>{integration.name}: {integration.mode}</p>)}</section></section>
}
