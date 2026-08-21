import type { CurrentRun, ProjectSummary } from "../api/readModels"

type ProjectsWorkspaceProps = {
  readonly projects: readonly ProjectSummary[]
  readonly selectedProjectId: string
  readonly selectProject: (projectId: string) => Promise<CurrentRun>
}

export function ProjectsWorkspace({ projects, selectedProjectId, selectProject }: ProjectsWorkspaceProps): JSX.Element {
  return <section aria-labelledby="projects-workspace-title" className="work-panel projects-workspace">
    <div className="work-heading">
      <div>
        <p className="eyebrow">Projekte</p>
        <h2 id="projects-workspace-title">Projekt waehlen</h2>
      </div>
      <p>Alle Werte stammen aus der kanonischen Projektliste.</p>
    </div>
    <ul aria-label="Kanonische Projekte" className="projects-grid">
      {projects.map((project) => <li key={project.projectId}>
        <button aria-current={selectedProjectId === project.projectId ? "true" : undefined} aria-label={`${project.name} waehlen`} className="project-choice" onClick={() => { void selectProject(project.projectId) }} type="button">
          <span className="project-choice-heading"><strong>{project.name}</strong><span>{project.customer}</span></span>
          <span className="project-choice-facts">
            <span><span>Aktiver Schritt</span><strong>{project.currentStep}</strong></span>
            <span><span>Fortschritt</span><strong>{project.progress}</strong></span>
            <span><span>Blocker</span><strong>{project.blockerCount}</strong></span>
            <span><span>Verantwortung</span><strong>{project.owner}</strong></span>
            <span><span>Naechste Aktion</span><strong>{project.nextAction}</strong></span>
          </span>
        </button>
      </li>)}
    </ul>
  </section>
}
