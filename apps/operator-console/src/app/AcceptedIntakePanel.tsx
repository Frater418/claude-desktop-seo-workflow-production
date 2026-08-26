import { useState } from "react"
import type { OperatorApiClient, PlanningCapacityPreview } from "../api/client"
import type { AcceptedIntakeRead } from "../api/readModels"

function record(value: unknown): Readonly<Record<string, unknown>> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Readonly<Record<string, unknown>> : null
}

function text(value: unknown): string | null {
  return typeof value === "string" && value !== "" ? value : null
}

function strings(value: unknown): readonly string[] {
  return Array.isArray(value) && value.every((entry) => typeof entry === "string") ? value : []
}

function acceptedDate(value: string): string {
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? value : new Intl.DateTimeFormat("de-DE", { dateStyle: "medium", timeStyle: "short" }).format(parsed)
}

interface DeploymentFact {
  readonly id: string
  readonly market: string
  readonly locale: string
  readonly language: string
  readonly regions: readonly string[]
  readonly providerTarget: string | null
  readonly providerLocationCode: number | null
  readonly verified: boolean
}

interface CapacityFact {
  readonly min: number
  readonly max: number
  readonly source: string
}

function intakeFacts(intake: AcceptedIntakeRead): { readonly businessGoal: string | null; readonly capacity: CapacityFact | null; readonly deployments: readonly DeploymentFact[]; readonly domain: string | null; readonly regions: readonly string[]; readonly services: readonly string[]; readonly source: string | null } {
  const project = intake.projectV2
  const entity = record(project["entity_domain_gbp"])
  const domains = Array.isArray(entity?.["domains"]) ? entity["domains"] : []
  const primaryDomain = domains.map(record).find((entry) => entry?.["role"] === "primary") ?? domains.map(record).find((entry) => entry !== null) ?? null
  const deployments = Array.isArray(project["market_deployments"]) ? project["market_deployments"] : []
  const deploymentRecords = deployments.map(record).filter((entry): entry is Readonly<Record<string, unknown>> => entry !== null)
  const primaryDeployment = deploymentRecords.find((entry) => entry["deployment_role"] === "primary") ?? deploymentRecords[0] ?? null
  const sourceManifest = record(project["source_legacy_manifest"])
  const capacity = record(project["planning_capacity"])
  const minimum = capacity?.["min"]
  const maximum = capacity?.["max"]
  return {
    businessGoal: text(project["business_goal"]),
    capacity: typeof minimum === "number" && typeof maximum === "number" ? { min: minimum, max: maximum, source: text(capacity?.["source"]) ?? "bestätigt" } : null,
    deployments: deploymentRecords.map((deployment) => {
      const verification = record(deployment["provider_location_verification"])
      const locationCode = verification?.["provider_location_code"]
      return {
        id: text(deployment["deployment_id"]) ?? "Unbekanntes Deployment",
        market: text(deployment["country_code"]) ?? "Unbekannter Markt",
        locale: text(deployment["locale"]) ?? "Unbekannte Locale",
        language: text(deployment["language"]) ?? "Unbekannte Sprache",
        regions: strings(deployment["target_regions"]),
        providerTarget: text(verification?.["location_name"]),
        providerLocationCode: typeof locationCode === "number" ? locationCode : null,
        verified: verification?.["status"] === "verified",
      }
    }),
    domain: text(primaryDomain?.["host"]),
    regions: strings(primaryDeployment?.["target_regions"]),
    services: strings(project["core_services"]),
    source: text(sourceManifest?.["source"]),
  }
}

function CapacityEditor({ api, projectId, reload }: { readonly api: OperatorApiClient; readonly projectId: string; readonly reload: () => Promise<void> }): JSX.Element {
  const [minimum, setMinimum] = useState("")
  const [maximum, setMaximum] = useState("")
  const [preview, setPreview] = useState<PlanningCapacityPreview | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const minimumValue = Number(minimum)
  const maximumValue = Number(maximum)
  const rangeValid = minimum.trim() !== "" && maximum.trim() !== "" && Number.isFinite(minimumValue) && Number.isFinite(maximumValue) && minimumValue >= 0 && maximumValue >= minimumValue && maximumValue <= 168

  async function previewCapacity(): Promise<void> {
    if (!rangeValid) return
    setBusy(true)
    setError(null)
    try {
      setPreview(await api.previewPlanningCapacity(projectId, { min_hours_per_week: minimumValue, max_hours_per_week: maximumValue }, new AbortController().signal))
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Die Kapazitätsvorschau ist fehlgeschlagen.")
    } finally {
      setBusy(false)
    }
  }

  async function confirmCapacity(): Promise<void> {
    if (preview === null) return
    setBusy(true)
    setError(null)
    try {
      await api.confirmPlanningCapacity(projectId, { preview_hash: preview.preview_hash, idempotency_key: `idem-capacity-${preview.preview_hash.slice(0, 24)}`, confirmed: true }, new AbortController().signal)
      await reload()
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Die Kapazitätsbestätigung ist fehlgeschlagen.")
    } finally {
      setBusy(false)
    }
  }

  return <section className="intake-missing" aria-labelledby="planning-capacity-title">
    <h4 id="planning-capacity-title">Wochenkapazität fehlt</h4>
    <p>Step 0 bleibt blockiert, bis du einen verbindlichen Stundenwert oder Bereich bestätigst. Heartweb setzt keinen Default.</p>
    <div className="intake-supplement">
      <label>Minimum Stunden pro Woche<input aria-label="Minimum Stunden pro Woche" min="0" max="168" step="0.5" type="number" value={minimum} onChange={(event) => { setMinimum(event.currentTarget.value); setPreview(null) }} /></label>
      <label>Maximum Stunden pro Woche<input aria-label="Maximum Stunden pro Woche" min="0" max="168" step="0.5" type="number" value={maximum} onChange={(event) => { setMaximum(event.currentTarget.value); setPreview(null) }} /></label>
      {preview === null ? <button className="button-primary" type="button" disabled={!rangeValid || busy} onClick={() => void previewCapacity()}>{busy ? "Vorschau wird erstellt..." : "Kapazität prüfen"}</button> : <>
        <p><strong>Zu bestätigen:</strong> {preview.capacity.min === preview.capacity.max ? `${preview.capacity.min} Stunden pro Woche` : `${preview.capacity.min} bis ${preview.capacity.max} Stunden pro Woche`}</p>
        <button className="button-primary" type="button" disabled={busy} onClick={() => void confirmCapacity()}>{busy ? "Wird gespeichert..." : "Kapazität verbindlich bestätigen"}</button>
      </>}
      {error === null ? null : <p role="alert" className="action-blocker">{error}</p>}
    </div>
  </section>
}

type AcceptedIntakePanelProps = {
  readonly api?: OperatorApiClient | undefined
  readonly intake: AcceptedIntakeRead
  readonly reload?: () => Promise<void>
}

export function AcceptedIntakePanel({ api, intake, reload = async () => undefined }: AcceptedIntakePanelProps): JSX.Element {
  const facts = intakeFacts(intake)
  return <section aria-labelledby="accepted-intake-title" className="accepted-intake-panel">
    <header className="section-heading">
      <div>
        <p className="eyebrow">Eingangsgrundlage</p>
        <h3 id="accepted-intake-title">Freigegebene Daten für Schritt 0</h3>
        <p>Die Projektanlage ist abgeschlossen. Ergänzungen werden als neue Project-V2- und Logical-Session-Revision gespeichert.</p>
      </div>
      <span className="completion-badge">Angenommen am {acceptedDate(intake.acceptedAt)}</span>
    </header>

    {facts.capacity === null
      ? api === undefined
        ? <p className="action-blocker">Die Wochenkapazität fehlt. Öffne dieses Projekt in der verbundenen Operator Console, um sie zu bestätigen.</p>
        : <CapacityEditor api={api} projectId={intake.projectId} reload={reload} />
      : <dl className="intake-business-facts"><div><dt>Bestätigte Wochenkapazität</dt><dd>{facts.capacity.min === facts.capacity.max ? `${facts.capacity.min} Stunden` : `${facts.capacity.min} bis ${facts.capacity.max} Stunden`} pro Woche | {facts.capacity.source === "operator_confirmed" ? "durch Operator bestätigt" : "im Briefing bestätigt"}</dd></div></dl>}

    <details className="intake-foundation-details">
      <summary>Briefing, Project V2 und Laufnachweis anzeigen</summary>
      <ol className="completed-actions" aria-label="Abgeschlossene Projektanlage">
        <li>Briefing vollständig übernommen</li>
        <li>Project V2 aus dem Briefing erzeugt</li>
        <li>Project V2 fachlich und strukturell validiert</li>
        <li>Projekt verbindlich angenommen</li>
        <li>Projektordner und Workflow initialisiert</li>
      </ol>

      <dl className="intake-business-facts">
        {facts.businessGoal === null ? null : <div><dt>Geschäftsziel</dt><dd>{facts.businessGoal}</dd></div>}
        {facts.domain === null ? null : <div><dt>Website</dt><dd>{facts.domain}</dd></div>}
        {facts.regions.length === 0 ? null : <div><dt>Zielmarkt</dt><dd>{facts.regions.join(", ")}</dd></div>}
        <div><dt>Kernleistungen</dt><dd>{facts.services.length}</dd></div>
        <div><dt>Verwendete Quelle</dt><dd>{facts.source ?? "Angenommenes Markdown-Briefing"}</dd></div>
      </dl>

      <h4>Standort- und Marktbindungen</h4>
      <dl className="intake-business-facts" aria-label="Gebundene Markt-Deployments">
        {facts.deployments.map((deployment) => <div key={deployment.id}>
          <dt>{deployment.regions.length === 0 ? deployment.id : deployment.regions.join(", ")}</dt>
          <dd>
            {deployment.market} | {deployment.locale} | Sprache {deployment.language} | Provider-Ziel {deployment.providerTarget ?? "nicht gebunden"} | Code {deployment.providerLocationCode ?? "fehlt"} | {deployment.verified ? "verifiziert" : "nicht verifiziert"}
          </dd>
        </div>)}
      </dl>

      <details className="intake-record-details">
        <summary>Angenommenes Briefing</summary>
        <pre className="accepted-intake-markdown">{intake.markdown}</pre>
      </details>
      <details className="intake-record-details">
        <summary>Vollständiges Project V2</summary>
        <pre>{JSON.stringify(intake.projectV2, null, 2)}</pre>
      </details>
      <details className="intake-record-details technical-details">
        <summary>Technischer Laufnachweis</summary>
        <dl className="technical-facts">
          <div><dt>Briefing-Hash</dt><dd>{intake.sourceHash}</dd></div>
          <div><dt>Angenommen durch</dt><dd>{intake.acceptedBy}</dd></div>
          {intake.generation === null ? <div><dt>AI-Lauf</dt><dd>Kein AI-Laufnachweis gespeichert</dd></div> : <>
            <div><dt>Modell</dt><dd>{intake.generation.modelId}</dd></div>
            <div><dt>Prompt</dt><dd>{intake.generation.promptId}, Version {intake.generation.promptVersion}</dd></div>
            <div><dt>Provider-Run</dt><dd>{intake.generation.providerRunId}</dd></div>
          </>}
        </dl>
      </details>
    </details>
  </section>
}
