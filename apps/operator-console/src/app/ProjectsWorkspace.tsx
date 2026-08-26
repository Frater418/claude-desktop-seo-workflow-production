import { useEffect, useRef, useState } from "react"
import type { OperatorApiClient, ProjectDeletionPreview } from "../api/client"
import type { CurrentRun, ProjectSummary } from "../api/readModels"
import { completedProgress, workflowStepTitle } from "./workflowPresentation"

type ProjectsWorkspaceProps = {
  readonly api: OperatorApiClient
  readonly projects: readonly ProjectSummary[]
  readonly selectedProjectId: string | null
  readonly openProject: (projectId: string) => Promise<CurrentRun>
  readonly onCreate: () => void
  readonly onProjectDeleted: (projectId: string) => Promise<void>
}

export function ProjectsWorkspace({ api, projects, selectedProjectId, openProject, onCreate, onProjectDeleted }: ProjectsWorkspaceProps): JSX.Element {
  const [deleteTarget, setDeleteTarget] = useState<ProjectSummary | null>(null)
  const [preview, setPreview] = useState<ProjectDeletionPreview | null>(null)
  const [confirmation, setConfirmation] = useState("")
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const requestRef = useRef<AbortController | null>(null)

  useEffect(() => () => requestRef.current?.abort(), [])

  const closeDialog = (): void => {
    if (deleting) return
    requestRef.current?.abort()
    requestRef.current = null
    setDeleteTarget(null)
    setPreview(null)
    setConfirmation("")
    setError(null)
    setLoadingPreview(false)
  }

  const openDeleteDialog = async (project: ProjectSummary): Promise<void> => {
    requestRef.current?.abort()
    const controller = new AbortController()
    requestRef.current = controller
    setDeleteTarget(project)
    setPreview(null)
    setConfirmation("")
    setError(null)
    setLoadingPreview(true)
    try {
      const deletionPreview = await api.previewProjectDeletion(project.projectId, controller.signal)
      if (requestRef.current === controller) setPreview(deletionPreview)
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") return
      if (requestRef.current === controller) setError(caught instanceof Error ? caught.message : "Die Löschvorschau konnte nicht geladen werden.")
    } finally {
      if (requestRef.current === controller) setLoadingPreview(false)
    }
  }

  const confirmDeletion = async (): Promise<void> => {
    if (deleteTarget === null || preview === null || !preview.allowed || confirmation !== "LOESCHEN") return
    requestRef.current?.abort()
    const controller = new AbortController()
    requestRef.current = controller
    setDeleting(true)
    setError(null)
    try {
      const result = await api.confirmProjectDeletion(
        deleteTarget.projectId,
        {
          preview_hash: preview.preview_hash,
          idempotency_key: `idem-project-delete-${preview.preview_hash.slice(0, 24)}`,
          confirmed: true,
          confirmation_text: "LOESCHEN",
        },
        controller.signal,
      )
      if (!result.deleted || result.project_id !== deleteTarget.projectId) throw new Error("Die Löschbestätigung stimmt nicht mit dem ausgewählten Projekt überein.")
      await onProjectDeleted(deleteTarget.projectId)
      if (requestRef.current === controller) {
        setDeleteTarget(null)
        setPreview(null)
        setConfirmation("")
      }
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") return
      if (requestRef.current === controller) setError(caught instanceof Error ? caught.message : "Das Projekt konnte nicht sicher gelöscht werden.")
    } finally {
      if (requestRef.current === controller) setDeleting(false)
    }
  }

  return <section aria-labelledby="projects-workspace-title" className="work-panel projects-workspace">
    <div className="work-heading project-overview-heading">
      <div>
        <p className="eyebrow">Start</p>
        <h2 id="projects-workspace-title">Projektübersicht</h2>
        <p>{projects.length} {projects.length === 1 ? "Kundenprojekt" : "Kundenprojekte"} im lokalen Heartweb-Arbeitsbereich.</p>
      </div>
      <button className="button-primary" type="button" onClick={onCreate}>Neues Projekt anlegen</button>
    </div>
    <ul aria-label="Kanonische Projekte" className="projects-grid">
      {projects.map((project) => <li className="project-overview-card" key={project.projectId}>
        <button aria-current={selectedProjectId === project.projectId ? "true" : undefined} aria-label={`${project.name} öffnen`} className="project-choice" onClick={() => { void openProject(project.projectId) }} type="button">
          <span className="project-choice-heading"><strong>{project.name}</strong><span>{project.customer}</span></span>
          <span className="project-choice-facts">
            <span><span>Aktueller Produktionsschritt</span><strong>{workflowStepTitle(project.currentStep)}</strong></span>
            <span><span>Fortschritt</span><strong>{completedProgress(project.progress)}</strong></span>
            <span><span>Offene Blocker</span><strong>{project.blockerCount === 0 ? "Keine" : project.blockerCount}</strong></span>
            <span><span>Nächste Aktion</span><strong>{project.nextAction}</strong></span>
          </span>
          <span className="project-choice-action">Projekt öffnen</span>
        </button>
        <button aria-label={`${project.name} löschen`} className="project-delete-button" onClick={() => { void openDeleteDialog(project) }} type="button">Projekt löschen</button>
      </li>)}
    </ul>
    {deleteTarget !== null ? <div className="project-delete-backdrop">
      <section aria-labelledby="project-delete-title" aria-modal="true" className="project-delete-dialog" role="dialog">
        <div>
          <p className="eyebrow">Destruktive Aktion</p>
          <h2 id="project-delete-title">Projekt löschen</h2>
          <p><strong>{deleteTarget.name}</strong> und alle zugehörigen Runs, Artefakte, Freigaben und Exporte werden dauerhaft entfernt.</p>
        </div>
        {loadingPreview ? <p role="status">Löschumfang wird geprüft...</p> : null}
        {preview !== null ? <>
          <dl className="project-delete-impact">
            <div><dt>Dateien</dt><dd>{preview.file_count}</dd></div>
            <div><dt>Datenmenge</dt><dd>{formatBytes(preview.total_bytes)}</dd></div>
            <div><dt>Runs</dt><dd>{preview.run_count}</dd></div>
            <div><dt>Artefakte</dt><dd>{preview.artifact_count}</dd></div>
            <div><dt>Releases</dt><dd>{preview.release_count}</dd></div>
          </dl>
          <p className="project-delete-summary">{preview.file_count} Dateien mit insgesamt {formatBytes(preview.total_bytes)} werden gelöscht.</p>
          {preview.blockers.length > 0 ? <div className="action-blocker" role="alert">
            <strong>Löschung blockiert</strong>
            {preview.blockers.map((blocker) => <div key={blocker.code}><p>{blocker.message}</p><p>{blocker.remediation}</p></div>)}
          </div> : null}
          <label className="project-delete-confirmation">
            <span>Zur Bestätigung <code>LOESCHEN</code> eingeben</span>
            <input autoComplete="off" disabled={deleting} onChange={(event) => setConfirmation(event.target.value)} spellCheck={false} value={confirmation} />
          </label>
        </> : null}
        {error !== null ? <p className="project-delete-error" role="alert">{error}</p> : null}
        <div className="project-delete-actions">
          <button className="button-secondary" disabled={deleting} onClick={closeDialog} type="button">Abbrechen</button>
          <button className="button-danger" disabled={deleting || preview === null || !preview.allowed || confirmation !== "LOESCHEN"} onClick={() => { void confirmDeletion() }} type="button">
            {deleting ? "Projekt wird gelöscht..." : "Projekt endgültig löschen"}
          </button>
        </div>
      </section>
    </div> : null}
  </section>
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${new Intl.NumberFormat("de-DE", { maximumFractionDigits: 1 }).format(bytes / 1024)} KB`
  return `${new Intl.NumberFormat("de-DE", { maximumFractionDigits: 1 }).format(bytes / (1024 * 1024))} MB`
}
