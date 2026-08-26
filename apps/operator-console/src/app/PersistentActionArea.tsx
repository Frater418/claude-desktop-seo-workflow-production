import type { AdminActionState } from "./useAdminAction"

type PersistentActionAreaProps = {
  readonly title: string
  readonly description: string
  readonly previewLabel: string
  readonly confirmLabel: string
  readonly completedLabel: string
  readonly state: AdminActionState
  readonly onPreview: () => void
  readonly onConfirm: () => void
}

export function WorkflowActionDetails({ state }: { readonly state: AdminActionState }): JSX.Element | null {
  switch (state.kind) {
    case "idle": return state.notice === undefined || state.notice.trim() === "" ? null : <p className="action-blocker">{state.notice}</p>
    case "previewing": return <p aria-live="polite">Vorschau wird geladen.</p>
    case "blocked": return <section className="action-blocker" aria-live="polite"><h3>Aktion nicht erlaubt</h3>{state.preview.blockers.map((blocker) => <div key={blocker.code}><p>{blocker.message}</p><p>{blocker.remediation}</p></div>)}</section>
    case "awaiting-confirmation": {
      const result = state.preview.consequence["result"]
      return <section className="action-consequence" aria-live="polite"><h3>Folge der Aktion</h3><p>{typeof result === "string" ? result : "Die Aktion wurde vorbereitet."}</p></section>
    }
    case "confirming": return <p aria-live="polite">Aktion wird verbindlich bestaetigt.</p>
    case "reloading": return <p aria-live="polite">Kanonischer Stand wird geladen.</p>
    case "completed": return <p className="success-note">{state.replay ? "Kanonische Wiederholung bestaetigt." : "Kanonischer Stand aktualisiert."}</p>
    case "failed": return <section className="action-blocker" aria-live="polite"><h3>Aktion fehlgeschlagen</h3><p>{state.message}</p></section>
  }
}

export function PersistentActionArea({ title, description, previewLabel, confirmLabel, completedLabel, state, onPreview, onConfirm }: PersistentActionAreaProps): JSX.Element {
  let action: JSX.Element
  switch (state.kind) {
    case "idle": action = <button className="button-primary" type="button" onClick={onPreview}>{previewLabel}</button>; break
    case "blocked":
    case "failed": action = <button type="button" onClick={onPreview}>Erneut prüfen</button>; break
    case "awaiting-confirmation": action = <button className="button-primary" type="button" onClick={onConfirm}>{confirmLabel}</button>; break
    case "previewing": action = <span>Voraussetzungen werden geprüft.</span>; break
    case "confirming": action = <span>Aktion wird verbindlich ausgeführt.</span>; break
    case "reloading": action = <span>Aktueller Projektstand wird geladen.</span>; break
    case "completed": action = <span>{completedLabel}</span>; break
  }
  return <section aria-labelledby="workflow-action-title" className="step-action-area"><div><p className="eyebrow">Nächste verbindliche Aktion</p><h3 id="workflow-action-title">{title}</h3><p>{description}</p></div><WorkflowActionDetails state={state} />{action}</section>
}
