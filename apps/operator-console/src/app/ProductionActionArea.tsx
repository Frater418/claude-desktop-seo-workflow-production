import { useState } from "react"
import type { OperatorApiClient, ProductionIntent } from "../api/client"
import { useProductionRun, type ProductionRunState } from "./useProductionRun"

type ProductionProgressKind = Extract<ProductionRunState["kind"], "previewing" | "confirming" | "running" | "deciding" | "retrying" | "rerunning" | "reloading">

const progressCopy: Record<ProductionProgressKind, { readonly activeStage: number; readonly kicker: string; readonly title: string; readonly description: string }> = {
  previewing: { activeStage: 0, kicker: "Sichere Vorbereitung", title: "Produktionsvoraussetzungen werden geprüft", description: "Heartweb bindet den aktuellen Projektstand, die gültigen Eingaben und alle Sperren." },
  confirming: { activeStage: 1, kicker: "Echtlauf startet", title: "Der spezialisierte Hermes-Agent wird gestartet", description: "Die bestätigte Ausführung wird an genau diesen Step, Run und Context gebunden." },
  running: { activeStage: 1, kicker: "Agentische Verarbeitung", title: "Hermes erstellt das Produktionsergebnis", description: "Heartweb prüft den kanonischen Status automatisch. Dieser Vorgang kann einige Minuten dauern." },
  deciding: { activeStage: 1, kicker: "Freigabe wird gebunden", title: "Die Toolentscheidung wird sicher übernommen", description: "Nur die bestätigte Anfrage wird an denselben Hermes-Run zurückgegeben." },
  retrying: { activeStage: 1, kicker: "Technische Wiederaufnahme", title: "Der unveränderte Lauf wird erneut ausgeführt", description: "Context Package, Identitäten und fachlicher Auftrag bleiben unverändert gebunden." },
  rerunning: { activeStage: 1, kicker: "Neue fachliche Revision", title: "Hermes verarbeitet deine Korrekturanweisung", description: "Der neue Kandidat bleibt mit Findings, Grenzen und Vorgängerrevision nachvollziehbar verbunden." },
  reloading: { activeStage: 2, kicker: "Abschlussprüfung", title: "Ergebnis wird validiert und gespeichert", description: "Heartweb prüft Verträge, Evidence und Revision, bevor etwas kanonisch übernommen wird." },
}

const productionStages = [
  { title: "Auftrag gebunden", description: "Projektstand und Freigabe" },
  { title: "Hermes verarbeitet", description: "Spezialisierter Step-Agent" },
  { title: "Prüfen und speichern", description: "Verträge, Evidence und Revision" },
] as const

function ProductionProgress({ kind }: { readonly kind: ProductionProgressKind }): JSX.Element {
  const copy = progressCopy[kind]
  return <section className="production-progress" aria-live="polite" aria-busy="true">
    <header className="production-progress__header">
      <span className="production-progress__signal" aria-hidden="true" />
      <div>
        <p className="production-progress__kicker">{copy.kicker}</p>
        <h4>{copy.title}</h4>
        <p>{copy.description}</p>
      </div>
      <span className="production-progress__mode">Realer Produktionslauf</span>
    </header>
    <ol className="production-progress__stages" aria-label="Produktionsfortschritt">
      {productionStages.map((stage, index) => {
        const status = index < copy.activeStage ? "completed" : index === copy.activeStage ? "current" : "upcoming"
        return <li key={stage.title} data-state={status} aria-current={status === "current" ? "step" : undefined}>
          <span className="production-progress__stage-marker" aria-hidden="true">{status === "completed" ? "✓" : index + 1}</span>
          <span><strong>{stage.title}</strong><small>{stage.description}</small></span>
        </li>
      })}
    </ol>
    <p className="production-progress__note"><span aria-hidden="true" />Automatische Statusprüfung aktiv. Bitte dieses Fenster geöffnet lassen.</p>
  </section>
}

function ProductionDetails({ state }: { readonly state: ProductionRunState }): JSX.Element | null {
  switch (state.kind) {
    case "idle": return null
    case "previewing": return <ProductionProgress kind={state.kind} />
    case "blocked": return <section className="action-blocker" aria-live="polite"><h3>Produktion ist blockiert</h3>{state.preview.blockers.map((blocker) => <div key={blocker.code}><p><strong>{blocker.message}</strong></p><p>{blocker.remediation}</p></div>)}</section>
    case "awaiting-confirmation": {
      const summary = state.preview.consequence["summary"]
      const costNotice = state.preview.consequence["cost_notice"]
      return <section className="action-consequence" aria-live="polite"><h3>Produktionsvorschau</h3><p>{typeof summary === "string" ? summary : "Der Produktionslauf ist vorbereitet."}</p>{typeof costNotice === "string" ? <p><strong>{costNotice}</strong></p> : null}</section>
    }
    case "confirming": return <ProductionProgress kind={state.kind} />
    case "running": return <ProductionProgress kind={state.kind} />
    case "awaiting-tool-decision": return <section className="action-consequence" aria-live="polite">
      <h3>Exakte Toolfreigabe erforderlich</h3>
      <p><strong>Operation:</strong> {state.interaction.operation_id}</p>
      <p><strong>Freigabeumfang:</strong> {state.interaction.confirmation_scope}</p>
      <p><strong>Kostenmodus:</strong> {state.interaction.cost_mode}</p>
      <p><strong>Kostenbindung:</strong> {typeof state.interaction.maximum_cost_usd === "number" ? `${state.interaction.maximum_cost_usd.toFixed(2)} USD` : ["unknown_blocked", "provider_credits_unreported"].includes(state.interaction.cost_mode) ? "AgentSEO-Credits; der Provider meldet keinen Einzelverbrauch" : "Keine Providerkosten"}</p>
      <details><summary>Exakte Parameter und Requesthash</summary><pre>{JSON.stringify(state.interaction.request, null, 2)}</pre><p><code>{state.interaction.request_sha256}</code></p></details>
    </section>
    case "deciding": return <ProductionProgress kind={state.kind} />
    case "retrying": return <ProductionProgress kind={state.kind} />
    case "rerunning": return <ProductionProgress kind={state.kind} />
    case "reloading": return <ProductionProgress kind={state.kind} />
    case "completed": return <p className="success-note">{state.replay ? "Der vorhandene Produktionsstand wurde geladen." : "Das Produktionsergebnis wurde validiert und gespeichert."}</p>
    case "denied": return <section className="action-blocker" aria-live="polite"><h3>Toolausführung abgelehnt</h3><p>Der Hermes-Run wurde beendet. Es wurde kein Toolergebnis als Produktionsergebnis übernommen.</p></section>
    case "failed": return <section className="action-blocker" aria-live="polite"><h3>Produktion fehlgeschlagen</h3><p>{state.message}</p></section>
  }
}

type ProductionActionAreaProps = {
  readonly api: OperatorApiClient
  readonly intent: ProductionIntent
  readonly resultName: string
  readonly reload: () => Promise<void>
}

export function ProductionActionArea({ api, intent, resultName, reload }: ProductionActionAreaProps): JSX.Element {
  const production = useProductionRun({ client: api, reload, intent })
  const [decisionReason, setDecisionReason] = useState("")
  const [findings, setFindings] = useState("")
  const [affectedSections, setAffectedSections] = useState("")
  const [immutableConstraints, setImmutableConstraints] = useState("")
  const [rerunInstruction, setRerunInstruction] = useState("")
  const lineItems = (value: string): string[] => value.split("\n").map((item) => item.trim()).filter((item) => item !== "")
  const rerunReady = lineItems(findings).length > 0 && lineItems(affectedSections).length > 0 && lineItems(immutableConstraints).length > 0 && rerunInstruction.trim() !== ""
  let action: JSX.Element | null
  switch (production.state.kind) {
    case "idle": action = <button className="button-primary" type="button" onClick={() => { void production.preview(intent) }}>Produktion prüfen</button>; break
    case "blocked": action = <button type="button" onClick={() => { void production.preview(intent) }}>Erneut prüfen</button>; break
    case "failed": action = production.state.technicalRetry === undefined
      ? <button type="button" onClick={() => { void production.preview(intent) }}>Erneut prüfen</button>
      : <div className="action-controls"><label>Begründung für technischen Retry<input value={decisionReason} onChange={(event) => setDecisionReason(event.target.value)} placeholder="Warum soll derselbe unveränderte Lauf technisch wiederholt werden?" /></label><button className="button-primary" type="button" disabled={decisionReason.trim() === ""} onClick={() => { void production.retryTechnical(decisionReason.trim()) }}>Technischen Retry starten</button></div>; break
    case "awaiting-confirmation": action = <button className="button-primary" type="button" onClick={() => { void production.confirm() }}>Produktion jetzt ausführen</button>; break
    case "previewing": action = null; break
    case "confirming": action = null; break
    case "running": action = null; break
    case "awaiting-tool-decision": action = <div className="action-controls"><label>Begründung<input value={decisionReason} onChange={(event) => setDecisionReason(event.target.value)} placeholder="Warum wird diese exakte Toolanfrage genehmigt oder abgelehnt?" /></label><div><button className="button-primary" type="button" disabled={decisionReason.trim() === ""} onClick={() => { void production.decideTool(true, decisionReason.trim()) }}>Exakt diese Anfrage genehmigen</button><button type="button" disabled={decisionReason.trim() === ""} onClick={() => { void production.decideTool(false, decisionReason.trim()) }}>Anfrage ablehnen</button></div></div>; break
    case "deciding": action = null; break
    case "retrying": action = null; break
    case "rerunning": action = null; break
    case "reloading": action = null; break
    case "completed": action = <details className="action-controls"><summary>Fachliche Revision anfordern</summary><label>Findings, je Zeile<textarea value={findings} onChange={(event) => setFindings(event.target.value)} placeholder="Was ist am aktuellen Ergebnis fachlich falsch oder unvollständig?" /></label><label>Betroffene Bereiche, je Zeile<textarea value={affectedSections} onChange={(event) => setAffectedSections(event.target.value)} placeholder="Welche Abschnitte oder Artefaktteile müssen geändert werden?" /></label><label>Unveränderliche Grenzen, je Zeile<textarea value={immutableConstraints} onChange={(event) => setImmutableConstraints(event.target.value)} placeholder="Welche freigegebenen Fakten und Grenzen dürfen nicht verändert werden?" /></label><label>Konkrete neue Anweisung<textarea value={rerunInstruction} onChange={(event) => setRerunInstruction(event.target.value)} placeholder="Welches Ergebnis soll die neue Revision liefern?" /></label><button className="button-primary" type="button" disabled={!rerunReady} onClick={() => { void production.rerunWithSteering({ findings: lineItems(findings), affectedSections: lineItems(affectedSections), immutableConstraints: lineItems(immutableConstraints), instruction: rerunInstruction.trim() }) }}>Neue fachliche Revision starten</button></details>; break
    case "denied": action = <button type="button" onClick={() => { void production.preview(intent) }}>Neue Produktionsvorschau</button>; break
  }
  return <section aria-labelledby="production-action-title" className="step-action-area">
    <div>
      <p className="eyebrow">Nächste verbindliche Aktion</p>
      <h3 id="production-action-title">{resultName} produzieren</h3>
      <p>Heartweb prüft zuerst Runtime, Eingaben und Sperren. Erst deine Bestätigung startet den realen Modell- oder Providerlauf.</p>
    </div>
    <ProductionDetails state={production.state} />
    {action}
  </section>
}
