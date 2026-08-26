import { useLayoutEffect, useMemo, useRef, useState } from "react"
import { createDiagnosticOperatorApiClient } from "../api/diagnosticOperatorApi"
import type { OperatorApiClient } from "../api/client"
import type { OperatorWorkspaceData } from "./useOperatorWorkspace"
import { ArtifactWorkspace } from "./ArtifactWorkspace"
import { DiagnosticTraceStatus, useDiagnosticTrace } from "./DiagnosticTraceProvider"
import { DeliveryCenter } from "../features/delivery/DeliveryCenter"

import { RouteActionFooterProvider, RouteActionFooterSlot } from "./RouteActionFooter"
import { TaskWorkspace } from "./TaskWorkspace"
import { WorkflowWorkspace } from "./WorkflowWorkspace"
import { completedProgress, workflowStepTitle } from "./workflowPresentation"

const projectDestinations = ["Projektablauf", "Aufgaben", "Ergebnisse"] as const
type Destination = (typeof projectDestinations)[number] | "Uebergabe"

type OperatorShellProps = { readonly api: OperatorApiClient; readonly data: OperatorWorkspaceData; readonly initialDestination?: Destination; readonly onDeselectProject: () => void; readonly onRefresh: () => Promise<void> }

export function OperatorShell({ api, data, initialDestination = "Projektablauf", onDeselectProject, onRefresh }: OperatorShellProps): JSX.Element {
  const [destination, setDestination] = useState<Destination>(initialDestination)
  const diagnosticTrace = useDiagnosticTrace()
  const operationNamespace = useRef(crypto.randomUUID().replaceAll("-", "").slice(0, 12)).current
  const diagnosticApi = useMemo(() => createDiagnosticOperatorApiClient({ api, operationNamespace, reporter: { record: diagnosticTrace.record }, tenantId: data.currentRun.tenant_id }), [api, data.currentRun.tenant_id, diagnosticTrace.record, operationNamespace])
  const diagnosticData = useMemo(() => ({ ...data, actionClient: diagnosticApi }), [data, diagnosticApi])
  const workspaceFrameRef = useRef<HTMLDivElement>(null)
  const resetWorkspaceScroll = (): void => {
    if (workspaceFrameRef.current !== null) workspaceFrameRef.current.scrollTop = 0
  }
  const openDestination = (nextDestination: Destination): void => {
    resetWorkspaceScroll()
    setDestination(nextDestination)
  }
  const closeProject = async (): Promise<void> => {
    resetWorkspaceScroll()
    if (diagnosticTrace.canClose) await diagnosticTrace.close().catch(() => undefined)
    onDeselectProject()
  }
  const visibleProjectDestinations: readonly Destination[] = [...projectDestinations, "Uebergabe"]
  const customerDiffers = data.project.customer.trim().toLocaleLowerCase("de") !== data.project.name.trim().toLocaleLowerCase("de")
  useLayoutEffect(() => {
    resetWorkspaceScroll()
    const frame = requestAnimationFrame(resetWorkspaceScroll)
    return () => cancelAnimationFrame(frame)
  }, [data.projectId, destination])
  let mainContent: JSX.Element
  switch (destination) {
    case "Projektablauf":
      mainContent = <WorkflowWorkspace api={diagnosticApi} data={diagnosticData} onOpenDelivery={() => openDestination("Uebergabe")} onOpenResults={() => openDestination("Ergebnisse")} onReadback={onRefresh} />
      break
    case "Aufgaben":
      mainContent = <TaskWorkspace data={diagnosticData} onOpenWorkflow={() => openDestination("Projektablauf")} />
      break
    case "Ergebnisse":
      mainContent = <ArtifactWorkspace api={diagnosticApi} data={diagnosticData} onOpenWorkflow={() => openDestination("Projektablauf")} />
      break
    case "Uebergabe":
      mainContent = <DeliveryCenter api={diagnosticApi} tenantId={data.currentRun.tenant_id} projectId={data.projectId} />
      break
    default: {
      const unreachableDestination: never = destination
      mainContent = unreachableDestination
    }
  }
  return <main className="operator-shell">
    <a className="skip-link" href="#arbeitsbereich">Zum Arbeitsbereich</a>
    <aside className="side-navigation">
      <p className="brand-label">Heartweb Admin Operator</p>
      <nav aria-label="Projektverwaltung">
        <button className="nav-item" type="button" onClick={() => { void closeProject() }}>Projektübersicht</button>
      </nav>
      <section className="project-navigation" aria-labelledby="active-project-navigation-title">
        <p className="navigation-group-label" id="active-project-navigation-title">Aktives Projekt</p>
        <strong title={data.project.name}>{data.project.name}</strong>
        <button className="project-close-button" type="button" onClick={() => { void closeProject() }}>Projekt schließen</button>
        <nav aria-label="Aktives Projekt">
          {visibleProjectDestinations.map((entry) => <button className="nav-item" key={entry} type="button" aria-current={destination === entry ? "page" : undefined} onClick={() => openDestination(entry)}>
            <span>{entry}</span>
            {entry === "Aufgaben" && data.tasks.length > 0 ? <small>{data.tasks.length}</small> : null}
            {entry === "Ergebnisse" && data.artifacts.length > 0 ? <small>{data.artifacts.length}</small> : null}
          </button>)}
        </nav>
      </section>
    </aside>
    <RouteActionFooterProvider>
      <section className="shell-main">
        <header className="project-header">
          <div className="project-identity">
            <p className="eyebrow">{workflowStepTitle(data.project.currentStep)}</p>
            <h1>{data.project.name}</h1>
            {customerDiffers ? <p>{data.project.customer}</p> : null}
          </div>
          <section className="project-priority" aria-label="Aktueller Projektstatus">
            <div className="project-next-action"><span>Nächste Aktion</span><strong>{data.project.nextAction}</strong></div>
            <dl className="project-status">
              <div><dt>Fortschritt</dt><dd>{completedProgress(data.project.progress)}</dd></div>
              <div><dt>Offene Blocker</dt><dd>{data.project.blockerCount === 0 ? "Keine" : data.project.blockerCount}</dd></div>
            </dl>
          </section>
          <details className="project-technical-details">
            <summary>Technische Details</summary>
            <dl className="technical-facts"><div><dt>Verantwortung</dt><dd>{data.project.owner}</dd></div><div><dt>Projekt-ID</dt><dd>{data.projectId}</dd></div><div><dt>Lauf-ID</dt><dd>{data.currentRun.run_id}</dd></div></dl>
            <DiagnosticTraceStatus />
          </details>
        </header>
        <div className="workspace-frame" ref={workspaceFrameRef}><section className="workspace-main" id="arbeitsbereich">{mainContent}</section></div>
        <RouteActionFooterSlot />
      </section>
    </RouteActionFooterProvider>
  </main>
}
