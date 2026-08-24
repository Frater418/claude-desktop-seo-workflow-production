import type { ChangeEvent } from "react"
import { RouteActionFooter } from "../../app/RouteActionFooter"
import { DeliveryPreview } from "./DeliveryPreview"
import { ExportHistory } from "./ExportHistory"
import type { DeliveryCenterClient, DeliveryDownloadState, DeliveryFormField, DeliveryLoadState, DeliveryRoleOption } from "./useDeliveryCenter"
import { useDeliveryCenter } from "./useDeliveryCenter"
import type { DeliveryPreviewRead } from "../../api/deliveryReadModels"
import type { DeliveryImplementationTask } from "../../generated/api-types"

type DeliveryCenterProps = { readonly api: DeliveryCenterClient; readonly tenantId: string; readonly projectId: string }

function selectedPolicyText(scope: string, preview: DeliveryLoadState<DeliveryPreviewRead> | null): string {
  switch (scope) {
    case "checkpoint":
    case "final": {
      if (preview === null) return "Vorschau nicht verfuegbar."
      switch (preview.kind) {
        case "loading": return "Vorschau wird geladen."
        case "error": return "Vorschau nicht verfuegbar."
        case "ready": return preview.data.policyEligible ? "Zulaessig" : "Nicht zulaessig"
      }
    }
    default: return "Exportumfang waehlen."
  }
}

function createNotice(state: ReturnType<typeof useDeliveryCenter>["createState"]): JSX.Element | null {
  switch (state.kind) {
    case "idle": return null
    case "building": return <p aria-live="polite">Exportauftrag wird vorbereitet.</p>
    case "submitting": return <p aria-live="polite">Export wird erstellt.</p>
    case "readback": return <p aria-live="polite">Kanonischer Exportdatensatz wird gelesen.</p>
    case "ready": return <p className="success-note" aria-live="polite">{state.message}</p>
    case "error": return <section className="action-blocker" aria-live="polite"><h3>Export fehlgeschlagen</h3><p>{state.message}</p></section>
  }
}

function downloadNotice(state: DeliveryDownloadState): JSX.Element | null {
  switch (state.kind) {
    case "idle": return null
    case "downloading": return <p aria-live="polite">Gesamtes ZIP wird heruntergeladen.</p>
    case "ready": return <p className="success-note" aria-live="polite">{state.filename} wurde heruntergeladen.</p>
    case "error": return <section className="action-blocker" aria-live="polite"><h3>ZIP-Download fehlgeschlagen</h3><p>{state.message}</p></section>
  }
}

function assignmentText(sourceAssignee: string, notionUserId: string | null | undefined): string {
  if (sourceAssignee === "") return "Nicht zugewiesen"
  if (notionUserId === null || notionUserId === undefined) return "Notion-Zuordnung offen"
  return `${sourceAssignee} ist Notion zugeordnet.`
}

function roleLabel(role: DeliveryImplementationTask["role"]): string {
  switch (role) {
    case "copywriter": return "Copywriter"
    case "developer": return "Developer"
    case "project_management": return "Projektmanagement"
    case "reviewer": return "Pruefung"
  }
}

export function DeliveryCenter({ api, tenantId, projectId }: DeliveryCenterProps): JSX.Element {
  const delivery = useDeliveryCenter({ api, tenantId, projectId })
  const openAssignments = delivery.assignments.unresolved + delivery.assignments.unassigned
  const downloadRunning = (() => {
    switch (delivery.downloadState.kind) {
      case "downloading": return true
      case "idle":
      case "ready":
      case "error": return false
    }
  })()
  const update = (field: DeliveryFormField) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>): void => delivery.updateField(field, event.currentTarget.value)
  const toggle = (role: DeliveryRoleOption) => (): void => delivery.toggleRole(role)
  return <section aria-labelledby="delivery-center-title"><div className="work-heading"><div><p className="eyebrow">Lokale Lieferung</p><h2 id="delivery-center-title">Uebergabe und Export</h2><p>Lieferpakete werden aus dem kanonischen Projektstand vorbereitet. Externe Systeme werden nicht beschrieben.</p></div><dl className="facts"><div><dt>Richtlinienstatus</dt><dd>{selectedPolicyText(delivery.form.scope, delivery.preview)}</dd></div><div><dt>Erstellungsdaten</dt><dd>{delivery.assessment.input === null ? "Unvollstaendig" : "Vollstaendig"}</dd></div></dl></div><section className="work-panel"><h3>Liefer-Vorschauen</h3><DeliveryPreview heading="Checkpoint-Vorschau" state={delivery.checkpoint} /><DeliveryPreview heading="Finale Uebergabe" state={delivery.final} /></section><section className="work-panel"><h3>Exportdaten</h3><p>Richtlinienstatus und Erstellungsdaten werden getrennt geprueft.</p><dl className="facts"><div><dt>Paketgroesse</dt><dd>Erst nach Erstellung verfuegbar</dd></div><div><dt>Pruefsummen</dt><dd>Erst nach Erstellung verfuegbar</dd></div><div><dt>Offene Notion-Zuordnungen</dt><dd>{openAssignments}</dd></div></dl><label>Exportumfang<select aria-label="Exportumfang" value={delivery.form.scope} onChange={update("scope")}><option value="">Bitte waehlen</option><option value="checkpoint">Checkpoint</option><option value="final">Finale Uebergabe</option></select></label><label>Exportfolge<input aria-label="Exportfolge" min="1" type="number" value={delivery.form.exportSequence} onChange={update("exportSequence")} /></label><label>Quell-Snapshot-Revision<input aria-label="Quell-Snapshot-Revision" min="1" type="number" value={delivery.form.sourceSnapshotRevision} onChange={update("sourceSnapshotRevision")} /></label><label>Paketrevision<input aria-label="Paketrevision" min="1" type="number" value={delivery.form.packageRevision} onChange={update("packageRevision")} /></label><label>Entwurfsrichtlinie<select aria-label="Entwurfsrichtlinie" value={delivery.form.draftInclusionPolicy} onChange={update("draftInclusionPolicy")}><option value="">Bitte waehlen</option><option value="exclude_drafts">Entwuerfe ausschliessen</option><option value="include_explicit_drafts">Ausdruecklich Entwuerfe einbeziehen</option></select></label><fieldset><legend>Erforderliche Rollenpakete</legend><label><input aria-label="Copywriter" checked={delivery.form.selectedRoles.includes("copywriter")} onChange={toggle("copywriter")} type="checkbox" />Copywriter</label><label><input aria-label="Developer" checked={delivery.form.selectedRoles.includes("developer")} onChange={toggle("developer")} type="checkbox" />Developer</label></fieldset><label>Externe Kundenkennung<input aria-label="Externe Kundenkennung" value={delivery.form.customerExternalId} onChange={update("customerExternalId")} /></label><label>Publikations-URLs<textarea aria-label="Publikations-URLs" value={delivery.form.publicationUrls} onChange={update("publicationUrls")} /></label><label>Notion-Implementierungsaufgaben<textarea aria-label="Notion-Implementierungsaufgaben" value={delivery.form.implementationTasksJson} onChange={update("implementationTasksJson")} /></label>{delivery.assessment.errors.length === 0 ? null : <section className="action-blocker" aria-live="polite"><h4>Erstellungsdaten vervollstaendigen</h4><ul>{delivery.assessment.errors.map((error) => <li key={error}>{error}</li>)}</ul></section>}{delivery.needsHigherSequence ? <p className="action-blocker" aria-live="polite">Die Exportdaten wurden nach einem Sendeversuch geaendert. Erhoehen Sie die Exportfolge fuer einen neuen Export.</p> : null}<section className="gate-report"><h4>Rollen- und Assignee-Zuordnung</h4>{delivery.assessment.input === null ? <p>Zuordnungen werden nach einer vollstaendigen Eingabe angezeigt.</p> : <ul>{delivery.assessment.input.implementationTasks.map((task) => <li key={task.task_id}>{roleLabel(task.role)}: {assignmentText(task.source_assignee, task.notion_user_id)}</li>)}</ul>}</section>{delivery.notionPreviewVisible ? <section className="action-consequence" aria-live="polite"><h4>Notion-Uebergabe vorbereiten</h4><p>Diese Vorschau bereitet nur das manuelle Notion-Importpaket vor. Es werden keine externen Daten geschrieben.</p></section> : null}{createNotice(delivery.createState)}{downloadNotice(delivery.downloadState)}</section><ExportHistory history={delivery.history} record={delivery.record} selectedExportId={delivery.selectedExportId} onSelect={delivery.selectExport} /><RouteActionFooter><section aria-label="Lieferaktionen" className="persistent-actions"><div><p className="eyebrow">Lieferung</p><h3>Export ausfuehren</h3></div><button disabled={!delivery.canCreate} onClick={() => { void delivery.createExport() }} type="button">Export erstellen</button>{delivery.canRetry ? <button onClick={() => { void delivery.retryExport() }} type="button">Export unveraendert wiederholen</button> : null}<button disabled={delivery.selectedExportId === null || downloadRunning} onClick={() => { void delivery.downloadExport() }} type="button">Gesamtes ZIP herunterladen</button><button disabled={delivery.assessment.input === null} onClick={delivery.prepareNotionPreview} type="button">Notion-Uebergabe vorbereiten</button></section></RouteActionFooter></section>
}
