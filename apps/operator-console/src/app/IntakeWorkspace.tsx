import { useEffect, useRef, useState } from "react"
import type { OperatorApiClient } from "../api/client"
import type { CurrentRun, IntakePreviewRead } from "../api/readModels"

type IntakeWorkspaceProps = {
  readonly api: Pick<OperatorApiClient, "previewMarkdownIntake" | "acceptMarkdownIntake">
  readonly onAccepted: (projectId: string) => Promise<CurrentRun>
  readonly onCancel?: () => void
}

type Notice = { readonly kind: "error" | "success" | "pending"; readonly message: string }
type JsonRecord = Readonly<Record<string, unknown>>

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Die Projektaufnahme konnte nicht verarbeitet werden."
}

function value(entry: string | null): string {
  return entry ?? "Nicht angegeben"
}

function isRecord(entry: unknown): entry is JsonRecord {
  return typeof entry === "object" && entry !== null && !Array.isArray(entry)
}

function recordAt(entry: JsonRecord | null, key: string): JsonRecord | null {
  const nested = entry?.[key]
  return isRecord(nested) ? nested : null
}

function stringAt(entry: JsonRecord | null, key: string): string {
  const nested = entry?.[key]
  return typeof nested === "string" && nested !== "" ? nested : "Nicht angegeben"
}

function stringListAt(entry: JsonRecord | null, key: string): readonly string[] {
  const nested = entry?.[key]
  return Array.isArray(nested) && nested.every((item) => typeof item === "string") ? nested : []
}

function workstreamList(entry: JsonRecord | null): readonly string[] {
  const workstreams = entry?.["workstreams"]
  if (!Array.isArray(workstreams)) return []
  return workstreams.flatMap((item) => isRecord(item) && typeof item["type"] === "string" ? [item["type"]] : [])
}

function joined(values: readonly string[]): string {
  return values.length === 0 ? "Nicht angegeben" : values.join(", ")
}

function DraftDialog({ projectDocument, projectName, onClose }: { readonly projectDocument: JsonRecord; readonly projectName: string; readonly onClose: () => void }): JSX.Element {
  const closeButton = useRef<HTMLButtonElement>(null)
  const customer = recordAt(projectDocument, "customer")
  const conversion = recordAt(projectDocument, "conversion_model")

  useEffect(() => {
    closeButton.current?.focus()
    const closeOnEscape = (event: KeyboardEvent): void => {
      if (event.key === "Escape") onClose()
    }
    document.body.classList.add("intake-dialog-open")
    window.addEventListener("keydown", closeOnEscape)
    return () => {
      document.body.classList.remove("intake-dialog-open")
      window.removeEventListener("keydown", closeOnEscape)
    }
  }, [onClose])

  return <div className="intake-dialog-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
    <section className="intake-dialog" role="dialog" aria-modal="true" aria-labelledby="project-v2-dialog-title">
      <header className="intake-dialog-header">
        <div>
          <p className="eyebrow">Noch nicht gespeichert</p>
          <h3 id="project-v2-dialog-title">Project V2 prüfen</h3>
          <p>Dies ist der vollständige Entwurf für {projectName}. Erst die Projektannahme schreibt ihn in den Kundenordner.</p>
        </div>
        <button ref={closeButton} className="button-secondary" type="button" onClick={onClose}>Schließen</button>
      </header>
      <div className="intake-dialog-content">
        <section className="intake-draft-summary" aria-labelledby="intake-summary-title">
          <h4 id="intake-summary-title">Fachliche Zusammenfassung</h4>
          <dl className="facts">
            <div><dt>Kunde</dt><dd>{stringAt(customer, "name")}</dd></div>
            <div><dt>Geschäftsziel</dt><dd>{stringAt(projectDocument, "business_goal")}</dd></div>
            <div><dt>Primäre Conversion</dt><dd>{stringAt(conversion, "primary")}</dd></div>
            <div><dt>Workstreams</dt><dd>{joined(workstreamList(projectDocument))}</dd></div>
            <div><dt>Zielgruppen</dt><dd>{joined(stringListAt(projectDocument, "target_audiences"))}</dd></div>
            <div><dt>Kernleistungen</dt><dd>{joined(stringListAt(projectDocument, "core_services"))}</dd></div>
          </dl>
        </section>
        <section className="intake-json-preview" aria-labelledby="intake-json-title">
          <div className="intake-json-heading">
            <div>
              <h4 id="intake-json-title">Vollständiges Project V2</h4>
              <p>Genau dieser Inhalt wird bei der Annahme als <code>v2/operator/project-v2.json</code> gespeichert.</p>
            </div>
          </div>
          <pre>{JSON.stringify(projectDocument, null, 2)}</pre>
        </section>
      </div>
    </section>
  </div>
}

export function IntakeWorkspace({ api, onAccepted, onCancel }: IntakeWorkspaceProps): JSX.Element {
  const [markdown, setMarkdown] = useState("")
  const [preview, setPreview] = useState<IntakePreviewRead | null>(null)
  const [notice, setNotice] = useState<Notice | null>(null)
  const [isPreviewing, setIsPreviewing] = useState(false)
  const [isAccepting, setIsAccepting] = useState(false)
  const [previewFresh, setPreviewFresh] = useState(false)
  const [draftOpen, setDraftOpen] = useState(false)
  const [draftConfirmed, setDraftConfirmed] = useState(false)
  const [supplementalInformation, setSupplementalInformation] = useState("")
  const draftButton = useRef<HTMLButtonElement>(null)
  const supplementalInput = useRef<HTMLTextAreaElement>(null)

  const projectDocument = preview !== null && isRecord(preview.reviewed.project_v2) ? preview.reviewed.project_v2 : null
  const previewState = !previewFresh ? "stale" : preview?.eligible ? "ready" : "blocked"
  const previewStateLabel = !previewFresh ? "Vorschau veraltet" : preview?.eligible ? "Entwurf vollständig" : "Angaben fehlen"

  const closeDraft = (): void => {
    setDraftOpen(false)
    requestAnimationFrame(() => draftButton.current?.focus())
  }

  const setSource = (source: string): void => {
    setMarkdown(source)
    setSupplementalInformation("")
    setDraftConfirmed(false)
    setDraftOpen(false)
    if (preview !== null) {
      setPreviewFresh(false)
      setNotice({ kind: "error", message: "Das Briefing wurde geändert. Bitte einen neuen Project-V2-Entwurf erstellen." })
    } else setNotice(null)
  }

  const previewIntake = async (source: string = markdown): Promise<void> => {
    setIsPreviewing(true)
    setDraftConfirmed(false)
    setDraftOpen(false)
    setNotice({ kind: "pending", message: "Die AI analysiert das Briefing und erstellt Project V2." })
    try {
      setPreview(await api.previewMarkdownIntake({ markdown: source }, new AbortController().signal))
      setPreviewFresh(true)
      setNotice(null)
    } catch (error) {
      setPreview(null)
      setPreviewFresh(false)
      setNotice({ kind: "error", message: errorMessage(error) })
    } finally {
      setIsPreviewing(false)
    }
  }

  const supplementAndPreview = async (): Promise<void> => {
    const supplement = supplementalInformation.trim()
    if (supplement === "") {
      setNotice({ kind: "error", message: "Bitte ergänze die angeforderten Informationen, bevor du Project V2 erneut erstellen lässt." })
      supplementalInput.current?.focus()
      return
    }
    const separator = markdown.endsWith("\n\n") ? "" : markdown.endsWith("\n") ? "\n" : "\n\n"
    const updatedMarkdown = `${markdown}${separator}## Nachgereichte Angaben zur Intake-Prüfung\n\n${supplement}\n`
    setMarkdown(updatedMarkdown)
    setSupplementalInformation("")
    await previewIntake(updatedMarkdown)
  }

  const accept = async (): Promise<void> => {
    if (preview === null || !preview.eligible || !previewFresh || !draftConfirmed) return
    setIsAccepting(true)
    setPreviewFresh(false)
    setNotice({ kind: "pending", message: "Der Kundenordner wird angelegt und Schritt 0 wird geladen." })
    let projectCreated = false
    try {
      const accepted = await api.acceptMarkdownIntake({ confirmed: true, markdown, preview_hash: preview.previewHash, source_sha256: preview.sourceHash, reviewed: preview.reviewed }, new AbortController().signal)
      projectCreated = true
      const currentRun = await onAccepted(accepted.projectId)
      setNotice(currentRun.step_id === "0" ? { kind: "success", message: "Projekt angelegt. Schritt 0 ist bereit." } : { kind: "error", message: "Das Projekt wurde angelegt, aber der kanonische Projektlauf ist nicht in Schritt 0." })
    } catch (error) {
      if (!projectCreated) setPreviewFresh(true)
      setNotice({ kind: "error", message: errorMessage(error) })
    } finally {
      setIsAccepting(false)
    }
  }

  return <section className="work-panel intake-workspace" aria-busy={isPreviewing || isAccepting}>
    {onCancel === undefined ? null : <div className="intake-navigation"><button className="button-secondary" type="button" onClick={onCancel} disabled={isPreviewing || isAccepting}>Zur Projektübersicht</button></div>}
    <header className="intake-intro">
      <p className="eyebrow">Neues Kundenprojekt</p>
      <h2>Briefing in Project V2 umwandeln</h2>
      <p>Heartweb analysiert das Briefing mit AI und erstellt einen schema-validierten Entwurf. Vor der verbindlichen Projektanlage kannst du den vollständigen Inhalt prüfen.</p>
    </header>

    <section className="intake-stage" aria-labelledby="intake-source-title">
      <div className="intake-stage-heading">
        <span className="intake-stage-number" aria-hidden="true">1</span>
        <div><h3 id="intake-source-title">Briefing bereitstellen</h3><p>Datei auswählen oder den Inhalt direkt einfügen.</p></div>
      </div>
      <label className="intake-file-field">Markdown-Datei<input aria-label="Markdown-Datei" type="file" accept=".md,text/markdown" onChange={(event) => { const file = event.currentTarget.files?.[0]; if (file !== undefined && typeof file.text === "function") void file.text().then(setSource) }} /></label>
      <label>Markdown-Briefing<textarea aria-label="Markdown-Briefing" value={markdown} onChange={(event) => setSource(event.currentTarget.value)} /></label>
      <div className="intake-source-actions">
        <button className="button-primary" type="button" onClick={() => void previewIntake()} disabled={markdown === "" || isPreviewing || isAccepting}>{isPreviewing ? "Project V2 wird erstellt..." : "Project V2 erstellen"}</button>
        <p>Dieser Schritt speichert noch kein Kundenprojekt.</p>
      </div>
    </section>

    {notice !== null ? <p className={`intake-notice intake-notice-${notice.kind}`} role={notice.kind === "error" ? "alert" : "status"}>{notice.message}</p> : null}

    {preview !== null ? <section className="reviewed-intake" aria-labelledby="intake-preview-title">
      <header className="intake-review-header">
        <div className="intake-stage-heading">
          <span className="intake-stage-number" aria-hidden="true">2</span>
          <div><h3 id="intake-preview-title">Project V2 prüfen</h3><p>Prüfe die AI-Aufbereitung, bevor du ein Projekt anlegst.</p></div>
        </div>
        <strong className="intake-status" data-state={previewState}>{previewStateLabel}</strong>
      </header>

      <dl className="facts intake-preview-facts">
        <div><dt>Briefingtitel</dt><dd>{value(preview.title)}</dd></div>
        <div><dt>Projektname</dt><dd>{value(preview.projectName)}</dd></div>
        <div><dt>Project V2</dt><dd>{preview.projectV2Present ? "Schema-validierter Entwurf vorhanden" : "Kein vollständiger Entwurf vorhanden"}</dd></div>
      </dl>

      {preview.generationSummary !== null ? <section className="intake-validation-summary" aria-labelledby="intake-validation-title">
        <div>
          <p className="eyebrow">Realer AI-Lauf</p>
          <h4 id="intake-validation-title">Provider- und Vertragsprüfung</h4>
        </div>
        <dl className="technical-facts intake-generation-facts">
          <div><dt>Provider-Run</dt><dd>{preview.generationSummary.providerRunId}</dd></div>
          <div><dt>Modell</dt><dd>{preview.generationSummary.modelId}</dd></div>
          <div><dt>Antwort</dt><dd>{preview.generationSummary.outputCharacters.toLocaleString("de-DE")} Zeichen</dd></div>
        </dl>
        <ul className="intake-validation-stages">{preview.generationSummary.validationStages.map((stage) => <li key={stage}>{stage}</li>)}</ul>
        {preview.generationSummary.normalizations.length > 0 ? <details><summary>Angewandte Normalisierung</summary><ul>{preview.generationSummary.normalizations.map((item) => <li key={item}>{item}</li>)}</ul></details> : null}
      </section> : null}

      <section className="intake-missing" aria-labelledby="intake-missing-title">
        <h4 id="intake-missing-title">Fehlende Angaben</h4>
        {preview.missingFields.length === 0 ? <p>Keine fehlenden Angaben.</p> : <>
          <ul>{preview.missingFields.map((field) => <li key={field}>{field}</li>)}</ul>
          <div className="intake-supplement">
            <div>
              <h5>Angaben direkt ergänzen</h5>
              <p id="intake-supplement-help">Beantworte die offenen Punkte hier. Heartweb hängt deine Antwort sichtbar an das geladene Briefing an und startet danach einen neuen AI-Lauf. Die ausgewählte Markdown-Datei auf der Festplatte wird nicht verändert.</p>
            </div>
            <label>Nachgereichte Informationen<textarea ref={supplementalInput} aria-describedby="intake-supplement-help" value={supplementalInformation} onChange={(event) => setSupplementalInformation(event.currentTarget.value)} placeholder="Zum Beispiel: Quelle: https://...; Rechtsraum: Luxemburg; abgerufen am: 24.08.2026" /></label>
            <button className="button-primary" type="button" onClick={() => void supplementAndPreview()} disabled={supplementalInformation.trim() === "" || isPreviewing || isAccepting}>{isPreviewing ? "Project V2 wird neu erstellt..." : "Angaben ergänzen und Project V2 neu erstellen"}</button>
          </div>
        </>}
      </section>

      {projectDocument !== null ? <div className="intake-preview-actions">
        <button ref={draftButton} className="button-secondary" type="button" onClick={() => setDraftOpen(true)}>Vollständigen Project-V2-Entwurf öffnen</button>
        <p>Die Vorschau ist noch keine Datei im Kundenordner.</p>
      </div> : <div className="intake-draft-unavailable" role="status">
        <strong>Noch kein vollständiger Project-V2-Entwurf vorhanden</strong>
        <p>Ergänze zuerst die oben angeforderten Informationen und erstelle Project V2 erneut. Danach kannst du den vollständigen Entwurf öffnen und prüfen.</p>
      </div>}

      {preview.eligible && projectDocument !== null ? <section className="intake-acceptance" aria-labelledby="intake-acceptance-title">
        <div className="intake-stage-heading">
          <span className="intake-stage-number" aria-hidden="true">3</span>
          <div>
            <h3 id="intake-acceptance-title">Projekt verbindlich anlegen</h3>
            <p>Die Annahme legt den Kundenordner dauerhaft an, speichert Project V2, das für diesen Entwurf verwendete Briefing einschließlich sichtbar nachgereichter Angaben und den AI-Laufnachweis, initialisiert den Workflow von Schritt 0 bis 4B und öffnet Schritt 0. Es wird noch kein Produktionsschritt gestartet.</p>
          </div>
        </div>
        <label className="intake-confirmation"><input type="checkbox" checked={draftConfirmed} onChange={(event) => setDraftConfirmed(event.currentTarget.checked)} disabled={!previewFresh} /><span>Ich habe den vollständigen Project-V2-Entwurf geprüft.</span></label>
        <button className="button-primary intake-accept-button" type="button" onClick={() => void accept()} disabled={!preview.eligible || !previewFresh || !draftConfirmed || isAccepting}>{isAccepting ? "Projekt wird angelegt..." : "Projekt anlegen und Schritt 0 öffnen"}</button>
      </section> : <section className="intake-acceptance intake-acceptance-blocked" aria-labelledby="intake-acceptance-title">
        <div className="intake-stage-heading">
          <span className="intake-stage-number" aria-hidden="true">3</span>
          <div><h3 id="intake-acceptance-title">Projektanlage noch gesperrt</h3><p>Ein Kundenprojekt kann erst angelegt werden, wenn alle offenen Angaben ergänzt wurden und ein vollständiger Project-V2-Entwurf zur Prüfung vorliegt.</p></div>
        </div>
      </section>}

      <details className="intake-technical-details">
        <summary>Technische Zuordnung</summary>
        <dl className="technical-facts"><div><dt>Mandanten-ID</dt><dd>{value(preview.tenantId)}</dd></div><div><dt>Projekt-ID</dt><dd>{value(preview.projectId)}</dd></div></dl>
      </details>
    </section> : null}

    {draftOpen && projectDocument !== null ? <DraftDialog projectDocument={projectDocument} projectName={value(preview?.projectName ?? null)} onClose={closeDraft} /> : null}
  </section>
}