import { useState } from "react"
import type { OperatorApiClient } from "../api/client"
import type { CurrentRun } from "../api/readModels"
import type { OperatorWorkspaceData } from "./useOperatorWorkspace"
import { ArtifactWorkspace } from "./ArtifactWorkspace"
import { ContextPanel } from "./ContextPanel"
import { IntakeWorkspace } from "./IntakeWorkspace"
import { ProjectsWorkspace } from "./ProjectsWorkspace"
import { ReviewWorkspace } from "./ReviewWorkspace"
import { TaskWorkspace } from "./TaskWorkspace"
import { WorkflowWorkspace } from "./WorkflowWorkspace"

const destinations = ["Projekte", "Workflow", "Aufgaben", "Artefakte", "Pruefungen und Freigaben", "Uebergabe und Export"] as const
type Destination = (typeof destinations)[number]

type OperatorShellProps = { readonly api: OperatorApiClient; readonly data: OperatorWorkspaceData; readonly onRefresh: () => Promise<void>; readonly onIntakeAccepted: (projectId: string) => Promise<CurrentRun>; readonly projects: readonly OperatorWorkspaceData["project"][]; readonly selectedProjectId: string; readonly selectProject: (projectId: string) => Promise<CurrentRun> }

export function OperatorShell({ api, data, onRefresh, onIntakeAccepted, projects, selectedProjectId, selectProject }: OperatorShellProps): JSX.Element {
  const [destination, setDestination] = useState<Destination>("Projekte")
  const [intakeOpen, setIntakeOpen] = useState(false)
  let mainContent: JSX.Element
  if (intakeOpen) mainContent = <IntakeWorkspace api={api} onAccepted={onIntakeAccepted} />
  else {
    switch (destination) {
      case "Projekte":
        mainContent = <ProjectsWorkspace projects={projects} selectedProjectId={selectedProjectId} selectProject={selectProject} />
        break
      case "Workflow":
        mainContent = <WorkflowWorkspace data={data} />
        break
      case "Aufgaben":
        mainContent = <TaskWorkspace data={data} />
        break
      case "Artefakte":
        mainContent = <ArtifactWorkspace api={api} data={data} />
        break
      case "Pruefungen und Freigaben":
        mainContent = <ReviewWorkspace api={api} data={data} onReadback={onRefresh} />
        break
      case "Uebergabe und Export":
        mainContent = <section className="work-panel delivery-contract-gate"><p className="eyebrow">Vertragssperre</p><h2>Uebergabe und Export</h2><p>Sprint 5E Liefervertraege sind noch nicht installiert.</p><p>Vorschau, Export, Download, Ordner und Notion-Aenderungen bleiben bis zu den freigegebenen Liefervertraegen gesperrt.</p></section>
        break
      default: {
        const unreachableDestination: never = destination
        mainContent = unreachableDestination
      }
    }
  }
  return <main className="operator-shell"><a className="skip-link" href="#arbeitsbereich">Zum Arbeitsbereich</a><aside className="side-navigation"><p className="brand-label">Heartweb Admin Operator</p><nav aria-label="Hauptnavigation">{destinations.map((entry) => <a key={entry} href={`#${entry}`} aria-current={destination === entry ? "page" : undefined} onClick={(event) => { event.preventDefault(); setIntakeOpen(false); setDestination(entry) }}>{entry}</a>)}</nav></aside><section className="shell-main"><header className="project-header"><div><p className="eyebrow">Aktives Projekt</p><h1>{data.project.name}</h1><p>{data.project.customer}</p></div><dl className="project-status"><div><dt>Aktiver Schritt</dt><dd>{data.project.currentStep}</dd></div><div><dt>Fortschritt</dt><dd>{data.project.progress}</dd></div><div><dt>Blocker</dt><dd>{data.project.blockerCount}</dd></div><div><dt>Verantwortung</dt><dd>{data.project.owner}</dd></div><div><dt>Naechste Aktion</dt><dd>{data.project.nextAction}</dd></div></dl><button type="button" onClick={() => setIntakeOpen(true)}>Projekt anlegen</button></header><div className="workspace-frame"><section className="workspace-main" id="arbeitsbereich">{mainContent}</section><ContextPanel data={data} /></div></section></main>
}
