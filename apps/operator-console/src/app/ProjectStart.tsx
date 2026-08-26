import { useState } from "react"
import type { OperatorApiClient } from "../api/client"
import type { CurrentRun, ProjectSummary } from "../api/readModels"
import { IntakeWorkspace } from "./IntakeWorkspace"
import { ProjectsWorkspace } from "./ProjectsWorkspace"

type ProjectStartProps = {
  readonly api: OperatorApiClient
  readonly onAccepted: (projectId: string) => Promise<CurrentRun>
  readonly onProjectDeleted: (projectId: string) => Promise<void>
  readonly onOpenProject?: (projectId: string) => Promise<CurrentRun>
  readonly projects?: readonly ProjectSummary[]
}

export function ProjectStart({ api, onAccepted, onProjectDeleted, onOpenProject, projects = [] }: ProjectStartProps): JSX.Element {
  const [intakeOpen, setIntakeOpen] = useState(false)

  if (intakeOpen) {
    return <main className="project-start-page project-start-intake">
      <IntakeWorkspace api={api} onAccepted={onAccepted} onCancel={() => setIntakeOpen(false)} />
    </main>
  }

  if (projects.length > 0 && onOpenProject !== undefined) {
    return <main className="project-start-page"><ProjectsWorkspace api={api} projects={projects} selectedProjectId={null} openProject={onOpenProject} onCreate={() => setIntakeOpen(true)} onProjectDeleted={onProjectDeleted} /></main>
  }

  return <main className="project-start-page">
    <header className="project-start-header">
      <div>
        <p className="eyebrow">Heartweb Admin Operator</p>
        <h1>Projektübersicht</h1>
        <p>Hier verwaltest du bestehende Kundenprojekte und legst neue Projekte aus einem geprüften Briefing an.</p>
      </div>
      <button className="button-primary" type="button" onClick={() => setIntakeOpen(true)}>Erstes Projekt anlegen</button>
    </header>

    <section className="project-start-summary" aria-label="Projektbestand">
      <div><span>Projekte</span><strong>0</strong></div>
      <div><span>Aktive Workflows</span><strong>0</strong></div>
      <div><span>Offene Blocker</span><strong>0</strong></div>
    </section>

    <section className="project-start-empty" aria-labelledby="project-start-empty-title">
      <p className="eyebrow">Noch kein Kundenprojekt</p>
      <h2 id="project-start-empty-title">Das erste Projekt wartet auf sein Briefing</h2>
      <p>Nach der Anlage erscheint das Projekt hier mit Kunde, aktuellem Schritt, Fortschritt, Blockern und nächster Aktion.</p>
      <button className="button-secondary" type="button" onClick={() => setIntakeOpen(true)}>Neues Projekt anlegen</button>
    </section>
  </main>
}
