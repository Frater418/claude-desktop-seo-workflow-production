import { RouteActionFooter } from "./RouteActionFooter"
import { Step4ArtifactPayloadFields } from "./Step4ArtifactPayloadFields"
import { releasedArtifactRemediation, useArtifactRevision } from "./useArtifactRevision"
import type { ArtifactRevisionApi, ArtifactRevisionData } from "./useArtifactRevision"

export function ArtifactWorkspace({ api, data, onOpenWorkflow = () => undefined }: { readonly api: ArtifactRevisionApi; readonly data: ArtifactRevisionData; readonly onOpenWorkflow?: () => void }): JSX.Element {
  const artifact = data.current.artifact
  const revision = useArtifactRevision({ api, data })
  if (artifact === null) return <section className="empty-workspace" aria-labelledby="empty-results-title"><p className="eyebrow">Projektergebnisse</p><h2 id="empty-results-title">Noch kein Produktionsergebnis vorhanden</h2><p>Das erste Ergebnis entsteht, sobald du den aktuellen Produktionsschritt startest. Bis dahin gibt es hier keine Datei, Revision oder Prüfung zu bearbeiten.</p><button className="button-primary" type="button" onClick={onOpenWorkflow}>Zum aktuellen Projektschritt</button></section>
  const comparedRevisionIsDistinct = revision.parentArtifact !== null && revision.comparisonArtifact !== null && revision.parentArtifact.artifact_id !== revision.comparisonArtifact.artifact_id

  return <section className="artifact-layout">
    <section className="work-panel">
      <p className="eyebrow">Projektergebnisse</p>
      <h2>Ergebnis lesen und als neue Revision bearbeiten</h2>
      <label>Ausgangsrevision<select aria-label="Ausgangsrevision" value={revision.parentArtifact?.artifact_id ?? ""} onChange={(event) => revision.setParentArtifactId(event.currentTarget.value)} disabled={revision.isSaving || revision.isReadbackPending || revision.isContentLoading}><option value="">Revision waehlen</option>{revision.revisions.map((entry) => <option key={entry.artifact_id} value={entry.artifact_id}>Revision {entry.revision}</option>)}</select></label>
      <button type="button" className="artifact-row" onClick={() => void revision.loadContent()} disabled={!revision.canLoadContent}>{revision.parentArtifact?.storage_key ?? artifact.storage_key}, Revision {revision.parentArtifact?.revision ?? artifact.revision}</button>
      <label>Ergebnisinhalt bearbeiten<textarea aria-label="Ergebnisinhalt bearbeiten" value={revision.content} onChange={(event) => revision.setContent(event.currentTarget.value)} disabled={revision.isEditingLocked} /></label>
      {revision.isStep4 ? <Step4ArtifactPayloadFields disabled={revision.isEditingLocked} supportingDocument={revision.supportingDocument} bundle={revision.bundle} gateContext={revision.gateContext} setSupportingDocument={revision.setSupportingDocument} setBundle={revision.setBundle} setGateContext={revision.setGateContext} /> : null}
      <label>Neue Revision<select aria-label="Neue Revision" value={revision.comparisonArtifact?.artifact_id ?? ""} onChange={(event) => revision.setNewArtifactId(event.currentTarget.value)} disabled={revision.isSaving || revision.isReadbackPending || revision.isContentLoading}><option value="">Revision waehlen</option>{revision.revisions.map((entry) => <option key={entry.artifact_id} value={entry.artifact_id}>Revision {entry.revision}</option>)}</select></label>
      {revision.isReleased ? <p className="action-blocker">{releasedArtifactRemediation}</p> : null}
      {revision.isReadbackPending ? <p aria-live="polite">Kanonische Revisionsliste wird geladen.</p> : null}
      {revision.error === null ? null : <p role="alert" className="action-blocker">{revision.error}</p>}
      {revision.newArtifact === null ? null : <p className="success-note">Revision {revision.newArtifact.revision} wurde unveraenderlich gespeichert.</p>}
      {revision.diff === "" ? null : <pre>{revision.diff}</pre>}
      {revision.validation === "" ? null : <p className="success-note">{revision.validation}</p>}
    </section>
    <aside className="evidence-inline"><h3>Revisionslinie</h3><p>Neue Inhalte erhalten eine eigene unveraenderliche Revision.</p></aside>
    <RouteActionFooter><section aria-label="Ergebnisaktionen" className="persistent-actions"><div><p className="eyebrow">Ergebnisrevision</p><h3>Änderung unveränderlich speichern</h3></div><div className="action-row"><button type="button" onClick={() => void revision.save()} disabled={!revision.canSave}>Als neue Revision speichern</button><button type="button" onClick={() => void revision.compare()} disabled={!comparedRevisionIsDistinct || revision.isSaving || revision.isReadbackPending || revision.isContentLoading}>Revisionen vergleichen</button>{revision.isStep4 ? <button type="button" onClick={() => void revision.validate()} disabled={revision.newArtifact === null || revision.isSaving || revision.isReadbackPending || revision.isContentLoading}>Schritt 4 Preflight ausführen</button> : null}</div></section></RouteActionFooter>
  </section>
}
