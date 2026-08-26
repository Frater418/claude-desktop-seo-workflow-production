import { useEffect, useState } from "react"
import type { ActionIntent } from "../generated/api-types"
import type { OperatorApiClient, ProductionIntent } from "../api/client"
import { gateStatusLabel, stepStatusLabel, type RunStatus } from "../api/statusLabels"
import { AcceptedIntakePanel } from "./AcceptedIntakePanel"
import { LifecycleActionArea } from "./LifecycleActionArea"
import { ProductionActionArea } from "./ProductionActionArea"
import { ReviewWorkspace } from "./ReviewWorkspace"
import type { OperatorWorkspaceData } from "./useOperatorWorkspace"

import { workflowStep, workflowStepCode, workflowSteps, workflowStepTitle } from "./workflowPresentation"

type WorkflowWorkspaceProps = {
  readonly api?: OperatorApiClient
  readonly data: OperatorWorkspaceData
  readonly onOpenDelivery?: () => void
  readonly onOpenResults?: () => void
  readonly onReadback?: () => Promise<void>
}

function routeState(data: OperatorWorkspaceData, stepId: string): "completed" | "current" | "future" {
  if (stepId === data.currentRun.step_id) return "current"
  if (data.releases?.some((release) => release.stepId === stepId) === true) return "completed"
  const currentIndex = workflowSteps.findIndex((step) => step.id === data.currentRun.step_id)
  const stepIndex = workflowSteps.findIndex((step) => step.id === stepId)
  return stepIndex >= 0 && stepIndex < currentIndex ? "completed" : "future"
}

function routeStateLabel(state: ReturnType<typeof routeState>): string {
  switch (state) {
    case "completed": return "Freigegeben"
    case "current": return "Aktuell"
    case "future": return "Später"
  }
}

type LifecycleSpec = {
  readonly action: ActionIntent["action"]
  readonly title: string
  readonly description: string
  readonly previewLabel: string
  readonly confirmLabel: string
  readonly completedLabel: string
}

function lifecycleSpec(status: RunStatus, stepId: string, hasArtifact: boolean, hasGate: boolean): LifecycleSpec | null {
  if (status === "pending") return { action: "start", title: `${workflowStepTitle(stepId)} starten`, description: "Heartweb prüft alle kanonischen Eingaben und Sperren. Erst deine Bestätigung autorisiert die Produktion dieses Schritts.", previewLabel: "Startvoraussetzungen prüfen", confirmLabel: "Schritt verbindlich starten", completedLabel: "Der Schritt wurde gestartet." }
  if (status === "in_progress" && hasArtifact && hasGate) return { action: "submit-for-gate", title: "Ergebnis zur Prüfung einreichen", description: "Das gespeicherte Ergebnis und die Maschinenprüfung werden verbindlich an deine fachliche Freigabe übergeben.", previewLabel: "Einreichung prüfen", confirmLabel: "Zur Prüfung einreichen", completedLabel: "Das Ergebnis wurde zur Prüfung eingereicht." }
  if (status === "approved") return { action: "complete", title: "Schritt freigeben und abschließen", description: "Heartweb bindet deine Freigabe an genau diese Artefaktrevision und erstellt den unveränderlichen Release dieses Schritts.", previewLabel: "Abschluss prüfen", confirmLabel: "Schritt verbindlich abschließen", completedLabel: "Der Schritt wurde freigegeben und abgeschlossen." }
  if (status === "completed" && stepId !== "4b") return { action: "start", title: "Nächsten Produktionsschritt anlegen", description: "Heartweb leitet den erlaubten Folgeschritt aus dem kanonischen Workflow ab. Es wird kein Schritt übersprungen.", previewLabel: "Folgeschritt prüfen", confirmLabel: "Nächsten Schritt anlegen", completedLabel: "Der nächste Produktionsschritt wurde angelegt." }
  return null
}

function currentActionLabel(status: RunStatus, stepId: string, hasArtifact: boolean): string {
  if (status === "pending") return "Schritt verbindlich starten"
  if (status === "in_progress" && !hasArtifact) return "Ergebnis real produzieren"
  if (status === "in_progress") return "Ergebnis zur Prüfung einreichen"
  if (status === "awaiting_gate") return "Ergebnis prüfen und entscheiden"
  if (status === "approved") return "Schritt freigeben und abschließen"
  if (status === "completed" && stepId !== "4b") return "Nächsten Produktionsschritt anlegen"
  if (status === "completed") return "Übergabe öffnen"
  return "Blocker prüfen und beheben"
}

function readinessLabel(status: RunStatus, hasArtifact: boolean, fallback: string | undefined): string {
  if (fallback !== undefined && fallback !== "Keine offenen Blocker") return fallback
  if (status === "pending") return "Startbereit"
  if (status === "in_progress" && !hasArtifact) return "Produktion ausstehend"
  if (status === "in_progress") return "Maschinenprüfung abgeschlossen"
  if (status === "awaiting_gate") return "Deine Prüfung erforderlich"
  if (status === "approved") return "Freigegeben, Abschluss ausstehend"
  if (status === "completed") return "Abgeschlossen"
  return stepStatusLabel(status)
}

export function WorkflowWorkspace({ api, data, onOpenDelivery = () => undefined, onOpenResults = () => undefined, onReadback }: WorkflowWorkspaceProps): JSX.Element {
  const [reviewOpen, setReviewOpen] = useState(false)
  const step = data.current.step
  const gate = data.current.gate
  const artifact = data.current.artifact
  const definition = workflowStep(data.currentRun.step_id)
  const status = stepStatusLabel(data.run.status)
  const currentTasks = data.tasks.filter((task) => task.runId === data.currentRun.run_id && task.stepId === data.currentRun.step_id)
  const lifecycle = lifecycleSpec(data.run.status, data.currentRun.step_id, artifact !== null, gate !== null)
  const intent: ActionIntent | null = lifecycle === null ? null : { action: lifecycle.action, tenant_id: data.currentRun.tenant_id, project_id: data.projectId, run_id: data.currentRun.run_id, step_id: data.currentRun.step_id, expected_revision: data.currentRun.expected_revision }
  const productionIntent: ProductionIntent = { tenant_id: data.currentRun.tenant_id, project_id: data.projectId, run_id: data.currentRun.run_id, step_id: data.currentRun.step_id, expected_revision: data.currentRun.expected_revision }
  const finalDeliveryReady = data.releases?.some((release) => release.stepId === "4b") === true
  const canReview = api !== undefined && data.run.status === "awaiting_gate" && artifact !== null && gate !== null
  const reviewReadback = onReadback ?? data.reload

  useEffect(() => setReviewOpen(false), [data.currentRun.run_id])

  return <section className="workflow-page">
    <section aria-labelledby="workflow-overview-title" className="workflow-overview">
      <header className="section-heading">
        <div>
          <p className="eyebrow">Produktionsablauf</p>
          <h2 id="workflow-overview-title">8 verbindliche Schritte bis zur Übergabe</h2>
          <p>Jeder Schritt erzeugt ein Ergebnis, wird maschinell geprüft und anschließend hier freigegeben.</p>
        </div>
      </header>
      <ol aria-label="Produktionsschritte" className="workflow-route">
        {workflowSteps.map((routeStep) => {
          const state = routeState(data, routeStep.id)
          return <li data-state={state} key={routeStep.id}>
            <span>{workflowStepCode(routeStep.id)}</span>
            <strong>{routeStep.label}</strong>
            <small>{routeStateLabel(state)}</small>
          </li>
        })}
      </ol>
    </section>

    <section aria-labelledby="current-step-title" className="current-step-panel">
      <header className="current-step-heading">
        <div>
          <p className="eyebrow">Jetzt bearbeiten</p>
          <h2 id="current-step-title">{workflowStepTitle(definition.id)}</h2>
          <p>{definition.description}</p>
        </div>
        <span className="status-badge">{status}</span>
      </header>

      <div className="step-readiness">
        <div><span>Status</span><strong>{readinessLabel(data.run.status, artifact !== null, step?.blocker)}</strong></div>
        <div><span>Nächste Aktion</span><strong>{currentActionLabel(data.run.status, data.currentRun.step_id, artifact !== null)}</strong></div>
        <div><span>Erwartetes Ergebnis</span><strong>{definition.result}</strong></div>
      </div>

      {definition.id === "0" && data.intake !== undefined ? <AcceptedIntakePanel api={api} intake={data.intake} reload={data.reload} /> : null}

      {artifact === null ? <section className="step-process" aria-labelledby="step-process-title">
        <h3 id="step-process-title">Was nach dem Start geschieht</h3>
        <ol>
          <li><strong>Produktion:</strong> Heartweb erstellt {definition.result} aus den freigegebenen Eingaben.</li>
          <li><strong>Maschinenprüfung:</strong> Struktur, Verträge und erforderliche Nachweise werden geprüft.</li>
          <li><strong>Deine Prüfung:</strong> Das konkrete Ergebnis und der Prüfbericht erscheinen in diesem Schritt.</li>
          <li><strong>Freigabe:</strong> Erst deine bestätigte Entscheidung öffnet den nächsten Schritt.</li>
        </ol>
      </section> : <section className="step-result-summary" aria-labelledby="step-result-title">
        <div>
          <p className="eyebrow">Aktuelles Ergebnis</p>
          <h3 id="step-result-title">{definition.result}, Revision {artifact.revision}</h3>
          <p>Das Ergebnis ist unveränderlich gespeichert. Bearbeitungen erzeugen immer eine neue Revision.</p>
        </div>
        <button className="button-secondary" type="button" onClick={onOpenResults}>Ergebnis öffnen</button>
      </section>}

      {gate === null ? null : <section className="machine-review" aria-labelledby="machine-review-title">
        <div>
          <p className="eyebrow">Maschinenprüfung</p>
          <h3 id="machine-review-title">{gateStatusLabel(gate.result)}</h3>
          <p>{gate.summary}</p>
        </div>
        {gate.findings.length === 0 ? <p className="machine-review-finding">Keine maschinellen Feststellungen.</p> : <ul>{gate.findings.map((finding) => <li key={finding}>{finding}</li>)}</ul>}
        {canReview ? <button className="button-primary" type="button" aria-expanded={reviewOpen} onClick={() => setReviewOpen((open) => !open)}>{reviewOpen ? "Prüfung schließen" : "Ergebnis prüfen und entscheiden"}</button> : null}
      </section>}

      {currentTasks.length === 0 ? null : <section className="step-task-summary"><h3>Offene Aufgaben in diesem Schritt</h3><ul>{currentTasks.map((task) => <li key={task.taskId}>{task.title}: {task.resolution}</li>)}</ul></section>}

      {data.run.status === "in_progress" && artifact === null && api !== undefined ? <ProductionActionArea key={`${data.currentRun.run_id}:production`} api={api} intent={productionIntent} resultName={definition.result} reload={data.reload} /> : null}

      {lifecycle !== null && intent !== null ? <LifecycleActionArea key={`${data.currentRun.run_id}:${data.run.status}:${lifecycle.action}`} client={data.actionClient} intent={intent} title={lifecycle.title} description={lifecycle.description} previewLabel={lifecycle.previewLabel} confirmLabel={lifecycle.confirmLabel} completedLabel={lifecycle.completedLabel} reload={data.reload} /> : null}

      {finalDeliveryReady ? <section className="delivery-ready-summary"><div><p className="eyebrow">Übergabe freigegeben</p><h3>Das finale Übergabepaket ist verfügbar</h3></div><button className="button-primary" type="button" onClick={onOpenDelivery}>Übergabe öffnen</button></section> : null}

      {reviewOpen && canReview && api !== undefined ? <section className="embedded-review" aria-label="Prüfung und Freigabe im aktuellen Schritt"><ReviewWorkspace api={api} data={data} onReadback={reviewReadback} /></section> : null}

      {data.current.context === null && data.integrations.length === 0 ? null : <details className="step-supporting-details">
        <summary>Nachweise und technische Ausführung</summary>
        {data.current.context === null ? null : <section><h3>{data.current.context.title}</h3><p>{data.current.context.finding}</p></section>}
        {data.integrations.length === 0 ? null : <dl className="technical-facts">{data.integrations.map((integration) => <div key={integration.name}><dt>{integration.name}</dt><dd>{integration.mode === "live" ? "Live" : "Simulation"}</dd></div>)}</dl>}
      </details>}
    </section>
  </section>
}
