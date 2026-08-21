import { useState } from "react"
import type { OperatorApiClient } from "../api/client"
import type { CurrentRun, IntakePreviewRead } from "../api/readModels"

type IntakeWorkspaceProps = { readonly api: Pick<OperatorApiClient, "previewMarkdownIntake" | "acceptMarkdownIntake">; readonly onAccepted: (projectId: string) => Promise<CurrentRun> }
type Notice = { readonly kind: "error" | "success" | "pending"; readonly message: string }

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Die Intake-Annahme konnte nicht verarbeitet werden."
}

function value(value: string | null): string {
  return value ?? "Nicht angegeben"
}

export function IntakeWorkspace({ api, onAccepted }: IntakeWorkspaceProps): JSX.Element {
  const [markdown, setMarkdown] = useState("")
  const [preview, setPreview] = useState<IntakePreviewRead | null>(null)
  const [notice, setNotice] = useState<Notice | null>(null)
  const [isPreviewing, setIsPreviewing] = useState(false)
  const [isAccepting, setIsAccepting] = useState(false)
  const [previewFresh, setPreviewFresh] = useState(false)
  const setSource = (source: string): void => {
    setMarkdown(source)
    if (preview !== null) {
      setPreviewFresh(false)
      setNotice({ kind: "error", message: "Markdown wurde geaendert. Vorschau erneut erstellen." })
    } else setNotice(null)
  }
  const previewIntake = async (): Promise<void> => {
    setIsPreviewing(true)
    setNotice(null)
    try {
      setPreview(await api.previewMarkdownIntake({ markdown }, new AbortController().signal))
      setPreviewFresh(true)
    } catch (error) {
      setPreview(null)
      setPreviewFresh(false)
      setNotice({ kind: "error", message: errorMessage(error) })
    } finally {
      setIsPreviewing(false)
    }
  }
  const accept = async (): Promise<void> => {
    if (preview === null || !preview.eligible || !previewFresh) return
    setIsAccepting(true)
    setPreviewFresh(false)
    setNotice({ kind: "pending", message: "Kanonischer Stand wird geladen." })
    try {
      const accepted = await api.acceptMarkdownIntake({ confirmed: true, markdown, preview_hash: preview.previewHash, source_sha256: preview.sourceHash, reviewed: preview.reviewed }, new AbortController().signal)
      const currentRun = await onAccepted(accepted.projectId)
      setNotice(currentRun.step_id === "0" ? { kind: "success", message: "Schritt 0 bereit" } : { kind: "error", message: "Der kanonische Projektlauf ist nicht in Schritt 0." })
    } catch (error) {
      setNotice({ kind: "error", message: errorMessage(error) })
    } finally {
      setIsAccepting(false)
    }
  }
  return <section className="work-panel intake-workspace"><h2>Projekt anlegen</h2><label>Markdown-Briefing<textarea aria-label="Markdown-Briefing" value={markdown} onChange={(event) => setSource(event.currentTarget.value)} /></label><label>Markdown-Datei<input aria-label="Markdown-Datei" type="file" accept=".md,text/markdown" onChange={(event) => { const file = event.currentTarget.files?.[0]; if (file !== undefined && typeof file.text === "function") void file.text().then(setSource) }} /></label><button type="button" onClick={() => void previewIntake()} disabled={markdown === "" || isPreviewing || isAccepting}>Vorschau erstellen</button>{preview !== null ? <section className="reviewed-intake" aria-labelledby="intake-preview-title"><h3 id="intake-preview-title">Vorschau der Projektaufnahme</h3><dl className="facts"><div><dt>Titel</dt><dd>{value(preview.title)}</dd></div><div><dt>Projektname</dt><dd>{value(preview.projectName)}</dd></div><div><dt>Project V2</dt><dd>{preview.projectV2Present ? "Project V2 vorhanden" : "Project V2 nicht vorhanden"}</dd></div><div><dt>Pruefung</dt><dd>{preview.eligible ? "Annahme moeglich" : "Annahme nicht moeglich"}</dd></div></dl><details><summary>Technische Zuordnung</summary><dl><div><dt>Mandanten-ID</dt><dd>{value(preview.tenantId)}</dd></div><div><dt>Projekt-ID</dt><dd>{value(preview.projectId)}</dd></div></dl></details><input aria-label="Projektname pruefen" value={value(preview.projectName)} readOnly /><h4>Fehlende Angaben</h4>{preview.missingFields.length === 0 ? <p>Keine fehlenden Angaben.</p> : <ul>{preview.missingFields.map((field) => <li key={field}>{field}</li>)}</ul>}<button type="button" onClick={() => void accept()} disabled={!preview.eligible || !previewFresh || isAccepting}>Intake verbindlich annehmen</button></section> : null}{notice !== null ? <p className={notice.kind === "success" ? "success-note" : "action-blocker"} aria-live="polite">{notice.message}</p> : null}</section>
}
