import type { DeliveryExportResultRead, DeliveryPackageRecordRead } from "../../api/deliveryReadModels"
import type { DeliveryLoadState } from "./useDeliveryCenter"

type ExportHistoryProps = { readonly history: DeliveryLoadState<readonly DeliveryExportResultRead[]>; readonly record: DeliveryLoadState<DeliveryPackageRecordRead>; readonly selectedExportId: string | null; readonly onSelect: (exportId: string) => Promise<void> }

function byteCount(value: number): string {
  return `${new Intl.NumberFormat("de-DE").format(value)} Byte`
}

function scopeLabel(value: DeliveryExportResultRead["replayState"] | DeliveryPackageRecordRead["scope"]): string {
  switch (value) {
    case "checkpoint": return "Checkpoint"
    case "final": return "Finale Uebergabe"
    case "created": return "Erstellt"
    case "replayed": return "Wiederverwendet"
  }
}

function roleLabel(value: DeliveryPackageRecordRead["rolePackages"][number]["role"]): string {
  switch (value) {
    case "copywriter": return "Copywriter"
    case "developer": return "Developer"
    case "project_management": return "Projektmanagement"
    case "reviewer": return "Pruefung"
  }
}

function packageStatusLabel(value: DeliveryPackageRecordRead["derivedStatus"]): string {
  switch (value) {
    case "archived": return "Archiviert"
    case "prepared": return "Vorbereitet"
  }
}

function deliverableLabel(value: DeliveryPackageRecordRead["requiredDeliverables"][number]["deliverableId"]): string {
  switch (value) {
    case "strategy": return "Strategie"
    case "architecture": return "Seitenarchitektur"
    case "design": return "Design-System"
    case "keyword-research": return "Keyword-Recherche"
    case "roadmap": return "Roadmap"
    case "copywriter-handoff": return "Copywriter-Handoff"
    case "developer-handoff": return "Developer-Handoff"
  }
}

function releaseLabel(value: DeliveryPackageRecordRead["requiredDeliverables"][number]["releaseStatus"]): string {
  switch (value) {
    case "released": return "Freigegeben"
    case "draft": return "Entwurf"
  }
}

function recordView(state: DeliveryLoadState<DeliveryPackageRecordRead>): JSX.Element {
  switch (state.kind) {
    case "loading": return <p aria-live="polite">Exportdatensatz wird geladen.</p>
    case "error": return <section className="action-blocker" aria-live="polite"><h3>Exportdatensatz nicht verfuegbar</h3><p>{state.message}</p></section>
    case "ready": {
      const record = state.data
      return <section className="gate-report"><h3>Ausgewaehlter Export</h3><dl className="facts"><div><dt>Paketstatus</dt><dd>{packageStatusLabel(record.derivedStatus)}</dd></div><div><dt>Paketrevision</dt><dd>{record.packageRevision}</dd></div><div><dt>Quell-Snapshot-Revision</dt><dd>{record.sourceSnapshotRevision}</dd></div></dl><h4>Lieferobjekte</h4>{record.requiredDeliverables.length === 0 ? <p>Keine Lieferobjekte im Exportdatensatz.</p> : <ul>{record.requiredDeliverables.map((item) => <li key={item.deliverableId}>{deliverableLabel(item.deliverableId)}: {releaseLabel(item.releaseStatus)}, {item.packagePath}</li>)}</ul>}<h4>Fehlende Lieferobjekte</h4>{record.missingDeliverables.length === 0 ? <p>Keine fehlenden Lieferobjekte.</p> : <ul>{record.missingDeliverables.map((item) => <li key={item}>{deliverableLabel(item)}</li>)}</ul>}<h4>Paketpfade</h4><ul>{record.packagePaths.map((path) => <li key={path}>{path}</li>)}</ul><h4>Rollen- und Notion-Manifeste</h4><ul>{record.rolePackages.map((item) => <li key={item.roleHandoffManifestId}>{roleLabel(item.role)}: {item.manifestPath}<details><summary>Technische Details</summary><dl className="technical-facts"><div><dt>Manifest-ID</dt><dd>{item.roleHandoffManifestId}</dd></div><div><dt>Pruefsumme</dt><dd>{item.manifestSha256}</dd></div></dl></details></li>)}<li>Notion: {record.notionImportManifest.manifestPath}<details><summary>Technische Details</summary><dl className="technical-facts"><div><dt>Manifest-ID</dt><dd>{record.notionImportManifest.notionImportManifestId}</dd></div><div><dt>Pruefsumme</dt><dd>{record.notionImportManifest.manifestSha256}</dd></div></dl></details></li></ul><details><summary>Technische Paketdetails</summary><dl className="technical-facts"><div><dt>Paketsumme</dt><dd>{record.packageSha256}</dd></div><div><dt>ZIP-Pruefsumme</dt><dd>{record.zipSha256}</dd></div></dl></details><p>Alle Manifeste sind im gesamten ZIP enthalten.</p></section>
    }
  }
}

export function ExportHistory({ history, record, selectedExportId, onSelect }: ExportHistoryProps): JSX.Element {
  switch (history.kind) {
    case "loading": return <section className="work-panel"><h2>Exporthistorie</h2><p aria-live="polite">Exporthistorie wird geladen.</p></section>
    case "error": return <section className="work-panel"><h2>Exporthistorie</h2><section className="action-blocker" aria-live="polite"><h3>Historie nicht verfuegbar</h3><p>{history.message}</p></section>{selectedExportId === null ? null : recordView(record)}</section>
    case "ready": return <section className="work-panel"><h2>Exporthistorie</h2>{history.data.length === 0 ? <p>Keine Exporte vorhanden.</p> : <ul>{history.data.map((item) => <li key={item.exportId}><button aria-pressed={item.exportId === selectedExportId} aria-label={`Export ${item.exportId} waehlen`} onClick={() => { void onSelect(item.exportId) }} type="button"><strong>{scopeLabel(item.replayState)}</strong>: {item.createdAt}</button><dl className="facts"><div><dt>Quell-Snapshot-Revision</dt><dd>{item.sourceSnapshotRevision}</dd></div><div><dt>ZIP-Groesse</dt><dd>{byteCount(item.zipSizeBytes)}</dd></div></dl><details><summary>Technische Details</summary><dl className="technical-facts"><div><dt>ZIP-Pruefsumme</dt><dd>{item.zipSha256}</dd></div></dl></details></li>)}</ul>}{selectedExportId === null ? null : recordView(record)}</section>
  }
}
