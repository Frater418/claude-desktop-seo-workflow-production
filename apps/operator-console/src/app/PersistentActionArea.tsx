import type { AdminActionState } from "./useAdminAction"

type PersistentActionAreaProps = {
  readonly state: AdminActionState
  readonly onPreview: () => void
  readonly onConfirm: () => void
}

export function PersistentActionArea({ state, onPreview, onConfirm }: PersistentActionAreaProps): JSX.Element {
  let content: JSX.Element
  switch (state.kind) {
    case "idle":
      content = <><p>{state.notice ?? "Die naechste legale Aktion wird erst nach einer Vorschau verbindlich."}</p><button type="button" onClick={onPreview}>Naechsten Schritt vorbereiten</button></>
      break
    case "previewing":
      content = <p>Vorschau wird geladen.</p>
      break
    case "blocked":
      content = <><div className="action-blocker"><h3>Aktion nicht erlaubt</h3>{state.preview.blockers.map((blocker) => <div key={blocker.code}><p>{blocker.message}</p><p>{blocker.remediation}</p></div>)}</div><button type="button" onClick={onPreview}>Vorschau erneut erstellen</button></>
      break
    case "awaiting-confirmation": {
      const result = state.preview.consequence["result"]
      content = <><div className="action-consequence"><h3>Serverfolge</h3><p>{typeof result === "string" ? result : "Die Serverfolge wurde vorbereitet."}</p></div><button type="button" onClick={onConfirm}>Start verbindlich bestaetigen</button></>
      break
    }
    case "confirming":
      content = <p>Aktion wird verbindlich bestaetigt.</p>
      break
    case "reloading":
      content = <p>Kanonischer Stand wird geladen.</p>
      break
    case "completed":
      content = <p className="success-note">{state.replay ? "Kanonische Wiederholung bestaetigt." : "Kanonischer Stand aktualisiert."}</p>
      break
    case "failed":
      content = <><div className="action-blocker"><h3>Aktion fehlgeschlagen</h3><p>{state.message}</p></div><button type="button" onClick={onPreview}>Vorschau erneut erstellen</button></>
      break
  }
  return <section aria-labelledby="workflow-action-title" aria-live="polite" className="persistent-actions"><div><p className="eyebrow">Verbindliche Aktion</p><h3 id="workflow-action-title">Naechsten Schritt starten</h3></div>{content}</section>
}
