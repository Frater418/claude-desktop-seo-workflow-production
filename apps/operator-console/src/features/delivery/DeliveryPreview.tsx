import type { DeliveryDeliverableId, DeliveryReleaseStatus, DeliveryRole } from "../../api/deliveryReadModels"
import type { DeliveryLoadState } from "./useDeliveryCenter"
import type { DeliveryPreviewRead } from "../../api/deliveryReadModels"

type DeliveryPreviewProps = { readonly heading: string; readonly state: DeliveryLoadState<DeliveryPreviewRead> }

function deliverableLabel(value: DeliveryDeliverableId): string {
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

function roleLabel(value: DeliveryRole): string {
  switch (value) {
    case "copywriter": return "Copywriter"
    case "developer": return "Developer"
    case "project_management": return "Projektmanagement"
    case "reviewer": return "Pruefung"
  }
}

function releaseLabel(value: DeliveryReleaseStatus): string {
  switch (value) {
    case "released": return "Freigegeben"
    case "draft": return "Entwurf"
  }
}

export function DeliveryPreview({ heading, state }: DeliveryPreviewProps): JSX.Element {
  switch (state.kind) {
    case "loading":
      return <section className="work-panel delivery-preview"><h3>{heading}</h3><p aria-live="polite">Vorschau wird geladen.</p></section>
    case "error":
      return <section className="work-panel delivery-preview"><h3>{heading}</h3><section className="action-blocker" aria-live="polite"><h4>Vorschau nicht verfuegbar</h4><p>{state.message}</p></section></section>
    case "ready": {
      const preview = state.data
      return <section className="work-panel delivery-preview"><h3>{heading}</h3><dl className="facts"><div><dt>Richtlinienstatus</dt><dd>{preview.policyEligible ? "Export zulaessig" : "Export nicht zulaessig"}</dd></div><div><dt>Fehlende Pflichtausgaben</dt><dd>{preview.missingDeliverableIds.length}</dd></div></dl><section className="gate-report"><h4>Enthaltene Lieferobjekte</h4>{preview.selectedDeliverables.length === 0 ? <p>Keine Lieferobjekte vorhanden.</p> : <ul>{preview.selectedDeliverables.map((item) => <li key={item.artifactId}><strong>{deliverableLabel(item.deliverableId)}</strong>: <span>{releaseLabel(item.releaseStatus)}</span>, Rolle {roleLabel(item.role)}{item.outputPath === null ? ". Ausgabepfad nicht verfuegbar." : `. Ausgabepfad: ${item.outputPath}`}</li>)}</ul>}</section><section className="gate-report"><h4>Fehlende Pflichtausgaben</h4>{preview.missingDeliverableIds.length === 0 ? <p>Keine Pflichtausgaben fehlen.</p> : <ul>{preview.missingDeliverableIds.map((item) => <li key={item}>{deliverableLabel(item)}</li>)}</ul>}</section>{preview.errors.length === 0 ? null : <section className="action-blocker"><h4>Richtlinienfehler</h4>{preview.errors.map((error) => <p key={error.code}>{error.message}</p>)}</section>}</section>
    }
  }
}
