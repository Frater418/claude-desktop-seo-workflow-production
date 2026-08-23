import { useLayoutEffect, useMemo, useRef, useState } from "react"
import { createDiagnosticOperatorApiClient } from "../api/diagnosticOperatorApi"
import type { OperatorApiClient } from "../api/client"
import type { CurrentRun } from "../api/readModels"
import type { OperatorWorkspaceData } from "./useOperatorWorkspace"
import { ArtifactWorkspace } from "./ArtifactWorkspace"
import { ContextPanel } from "./ContextPanel"
import { DiagnosticTraceStatus, useDiagnosticTrace } from "./DiagnosticTraceProvider"
import { DeliveryCenter } from "../features/delivery/DeliveryCenter"
import { IntakeWorkspace } from "./IntakeWorkspace"
import { ProjectsWorkspace } from "./ProjectsWorkspace"
import { ReviewWorkspace } from "./ReviewWorkspace"
import { RouteActionFooterProvider, RouteActionFooterSlot } from "./RouteActionFooter"
import { TaskWorkspace } from "./TaskWorkspace"
import { WorkflowWorkspace } from "./WorkflowWorkspace"

const destinations = ["Projekte", "Workflow", "Aufgaben", "Artefakte", "Pruefungen und Freigaben", "Uebergabe und Export"] as const
type Destination = (typeof destinations)[number]

type OperatorShellProps = { readonly api: OperatorApiClient; readonly data: OperatorWorkspaceData; readonly onRefresh: () => Promise<void>; readonly onIntakeAccepted: (projectId: string) => Promise<CurrentRun>; readonly projects: readonly OperatorWorkspaceData["project"][]; readonly selectedProjectId: string; readonly selectProject: (projectId: string) => Promise<CurrentRun> }

export function OperatorShell({ api, data, onRefresh, onIntakeAccepted, projects, selectedProjectId, selectProject }: OperatorShellProps): JSX.Element {
  const [destination, setDestination] = useState<Destination>("Projekte")
  const [intakeOpen, setIntakeOpen] = useState(false)
  const diagnosticTrace = useDiagnosticTrace()
  const diagnosticApi = useMemo(() => createDiagnosticOperatorApiClient({ api, reporter: { record: diagnosticTrace.record }, tenantId: data.currentRun.tenant_id }), [api, data.currentRun.tenant_id, diagnosticTrace.record])
  const diagnosticData = useMemo(() => ({ ...data, actionClient: diagnosticApi }), [data, diagnosticApi])
  const workspaceFrameRef = useRef<HTMLDivElement>(null)
  const resetWorkspaceScroll = (): void => {
    if (workspaceFrameRef.current !== null) workspaceFrameRef.current.scrollTop = 0
  }
  useLayoutEffect(() => {
    resetWorkspaceScroll()
    const frame = requestAnimationFrame(resetWorkspaceScroll)
    return () => cancelAnimationFrame(frame)
  }, [destination, intakeOpen, selectedProjectId])
  let mainContent: JSX.Element
  if (intakeOpen) mainContent = <IntakeWorkspace api={diagnosticApi} onAccepted={onIntakeAccepted} />
  else {
    switch (destination) {
      case "Projekte":
        mainContent = <ProjectsWorkspace projects={projects} selectedProjectId={selectedProjectId} selectProject={(projectId) => { resetWorkspaceScroll(); return selectProject(projectId) }} />
        break
      case "Workflow":
        mainContent = <WorkflowWorkspace data={diagnosticData} />
        break
      case "Aufgaben":
        mainContent = <TaskWorkspace data={diagnosticData} />
        break
      case "Artefakte":
        mainContent = <ArtifactWorkspace api={diagnosticApi} data={diagnosticData} />
        break
      case "Pruefungen und Freigaben":
        mainContent = <ReviewWorkspace api={diagnosticApi} data={diagnosticData} onReadback={onRefresh} />
        break
      case "Uebergabe und Export":
        mainContent = <DeliveryCenter api={diagnosticApi} tenantId={data.currentRun.tenant_id} projectId={data.projectId} />
        break
      default: {
        const unreachableDestination: never = destination
        mainContent = unreachableDestination
      }
    }
  }
  return <main className="operator-shell"><a className="skip-link" href="#arbeitsbereich">Zum Arbeitsbereich</a><aside className="side-navigation"><p className="brand-label">Heartweb Admin Operator</p><nav aria-label="Hauptnavigation">{destinations.map((entry) => <a key={entry} href={`#${entry}`} aria-current={destination === entry ? "page" : undefined} onClick={(event) => { event.preventDefault(); resetWorkspaceScroll(); setIntakeOpen(false); setDestination(entry) }}>{entry}</a>)}</nav></aside><RouteActionFooterProvider><section className="shell-main"><header className="project-header"><div><p className="eyebrow">Aktives Projekt</p><h1>{data.project.name}</h1><p>{data.project.customer}</p></div><dl className="project-status"><div><dt>Aktiver Schritt</dt><dd>{data.project.currentStep}</dd></div><div><dt>Fortschritt</dt><dd>{data.project.progress}</dd></div><div><dt>Blocker</dt><dd>{data.project.blockerCount}</dd></div><div><dt>Verantwortung</dt><dd>{data.project.owner}</dd></div><div><dt>Naechste Aktion</dt><dd>{data.project.nextAction}</dd></div></dl><div className="project-actions"><DiagnosticTraceStatus /><button type="button" onClick={() => { resetWorkspaceScroll(); setIntakeOpen(true) }}>Projekt anlegen</button></div></header><div className="workspace-frame" ref={workspaceFrameRef}><section className="workspace-main" id="arbeitsbereich">{mainContent}</section><ContextPanel data={diagnosticData} /></div><RouteActionFooterSlot /></section></RouteActionFooterProvider></main>
}
