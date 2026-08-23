import { RouteActionFooter } from "./RouteActionFooter"
import type { AdminActionState } from "./useAdminAction"

type PersistentActionAreaProps = { readonly state: AdminActionState; readonly onPreview: () => void; readonly onConfirm: () => void }

export function WorkflowActionDetails({ state }: { readonly state: AdminActionState }): JSX.Element | null {
  switch (state.kind) {
    case "idle": return state.notice === undefined ? null : <p className="action-blocker">{state.notice}</p>
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

export function PersistentActionArea({ state, onPreview, onConfirm }: PersistentActionAreaProps): JSX.Element {
  let action: JSX.Element
  switch (state.kind) {
    case "idle": action = <button type="button" onClick={onPreview}>Naechsten Schritt vorbereiten</button>; break
    case "blocked":
    case "failed": action = <button type="button" onClick={onPreview}>Vorschau erneut erstellen</button>; break
    case "awaiting-confirmation": action = <button type="button" onClick={onConfirm}>Start verbindlich bestaetigen</button>; break
    case "previewing": action = <span>Vorschau laeuft.</span>; break
    case "confirming": action = <span>Bestaetigung laeuft.</span>; break
    case "reloading": action = <span>Kanonischer Readback laeuft.</span>; break
    case "completed": action = <span>Readback abgeschlossen.</span>; break
  }
  return <><WorkflowActionDetails state={state} /><RouteActionFooter><section aria-labelledby="workflow-action-title" className="persistent-actions"><div><p className="eyebrow">Verbindliche Aktion</p><h3 id="workflow-action-title">Naechsten Schritt starten</h3></div>{action}</section></RouteActionFooter></>
}
