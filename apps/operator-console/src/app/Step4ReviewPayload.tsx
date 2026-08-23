import type { GateRead } from "../api/readModels"
import type { ReviewArtifactPayloadState } from "./useReviewArtifactPayload"

type Step4ReviewPayloadProps = { readonly gate: GateRead | undefined; readonly state: ReviewArtifactPayloadState }

function hasLocalProvenance(content: string, gate: GateRead | undefined): boolean {
  const evidence = gate === undefined ? "" : Object.values(gate.evidence).join(" ")
  return /local|simulat|staging/i.test(`${content} ${evidence}`)
}

export function Step4ReviewPayload({ gate, state }: Step4ReviewPayloadProps): JSX.Element {
  if (state.kind === "loading") return <section aria-live="polite" className="gate-report"><h3>Schritt-4-Unterlagen werden geladen</h3><p>Primaerdokument und unterstuetzender Nachweis werden exakt an die aktuelle Revision gebunden geladen.</p></section>
  if (state.kind === "blocked") return <section aria-live="assertive" className="action-blocker" role="alert"><h3>Review-Unterlagen blockiert</h3><p>{state.message}</p><p>Laden Sie das exakte aktuelle Primaerartefakt, das unterstuetzende Dokument und den gebundenen Pruefnachweis erneut, bevor Sie die Freigabe vorbereiten.</p></section>
  const localProvenance = hasLocalProvenance(state.supporting.content, gate)
  return <section aria-live="polite" className="gate-report step4-review-payload"><h3>Exakte Schritt-4-Review-Unterlagen</h3><section aria-labelledby="review-primary-payload-heading" className="work-panel" role="region"><h4 id="review-primary-payload-heading">Kanonisches Primaerdokument</h4><dl className="facts"><div><dt>Revision</dt><dd>{state.primary.artifact.revision}</dd></div><div><dt>Inhaltshash</dt><dd>{state.primary.artifact.content_sha256}</dd></div></dl><pre aria-label="Kanonisches Primaerdokument">{state.primary.content}</pre></section><section aria-labelledby="review-supporting-payload-heading" className="work-panel" role="region"><h4 id="review-supporting-payload-heading">Unterstuetzendes Dokument</h4><dl className="facts"><div><dt>Revision</dt><dd>{state.supporting.artifact.revision}</dd></div><div><dt>Inhaltshash</dt><dd>{state.supporting.artifact.content_sha256}</dd></div></dl><pre aria-label="Unterstuetzendes Dokument">{state.supporting.content}</pre></section>{localProvenance ? <section className="action-blocker"><h4>Lokale oder simulierte Nachweisquelle</h4><p>Die sichtbaren Nachweise sind lokal oder simuliert bereitgestellt und kein externer Nachweis.</p></section> : null}</section>
}
