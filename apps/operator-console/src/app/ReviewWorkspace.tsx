import { useState } from "react"
import type { ActionIntent, ActionPayload, ArtifactRecord } from "../generated/api-types"
import type { OperatorApiClient } from "../api/client"
import type { GateRead } from "../api/readModels"
import type { OperatorWorkspaceData } from "./useOperatorWorkspace"
import { useAdminAction } from "./useAdminAction"

type ReviewAction = Extract<ActionIntent["action"], "approve" | "reject" | "request-revision" | "request-input" | "escalate" | "request-waiver">
type ReviewFields = { readonly reason: string; readonly instructions: string; readonly affectedSections: string; readonly immutableConstraints: string; readonly options: string; readonly impacts: string }
type ReviewActionConfig = { readonly label: string; readonly confirmation: string; readonly preview: string }
type ReviewWorkspaceProps = { readonly api: OperatorApiClient; readonly data: OperatorWorkspaceData; readonly onReadback: () => Promise<void> }

const emptyFields: ReviewFields = { reason: "", instructions: "", affectedSections: "", immutableConstraints: "", options: "", impacts: "" }
const actionConfig: Readonly<Record<ReviewAction, ReviewActionConfig>> = {
  approve: { label: "Freigabe", confirmation: "Freigabe bestaetigen", preview: "Freigabe vorbereiten" },
  reject: { label: "Ablehnung", confirmation: "Ablehnung bestaetigen", preview: "Vorschau fuer Ablehnung erstellen" },
  "request-revision": { label: "Revision", confirmation: "Revision anfordern bestaetigen", preview: "Vorschau fuer Revision erstellen" },
  "request-input": { label: "Eingabe", confirmation: "Eingabe anfordern bestaetigen", preview: "Vorschau fuer Eingabe erstellen" },
  escalate: { label: "Eskalation", confirmation: "Eskalation bestaetigen", preview: "Vorschau fuer Eskalation erstellen" },
  "request-waiver": { label: "Ausnahme", confirmation: "Ausnahmeanfrage bestaetigen", preview: "Vorschau fuer Ausnahme erstellen" },
}

function lines(value: string): readonly string[] {
  return value.split("\n").map((entry) => entry.trim()).filter((entry) => entry !== "")
}

function payload(action: ReviewAction, fields: ReviewFields): ActionPayload | undefined {
  switch (action) {
    case "approve": return undefined
    case "reject":
    case "request-revision": return { reason: fields.reason, instructions: fields.instructions, affected_sections: lines(fields.affectedSections), immutable_constraints: lines(fields.immutableConstraints) }
    case "request-input": return { reason: fields.reason, instructions: fields.instructions }
    case "escalate": return { reason: fields.reason, options: lines(fields.options), impacts: lines(fields.impacts) }
    case "request-waiver": return { reason: fields.reason, instructions: fields.instructions }
  }
}

function fieldsComplete(action: ReviewAction, fields: ReviewFields): boolean {
  switch (action) {
    case "approve": return true
    case "reject":
    case "request-revision": return fields.reason !== "" && fields.instructions !== "" && lines(fields.affectedSections).length > 0 && lines(fields.immutableConstraints).length > 0
    case "request-input":
    case "request-waiver": return fields.reason !== "" && fields.instructions !== ""
    case "escalate": return fields.reason !== "" && lines(fields.options).length >= 2 && lines(fields.impacts).length > 0
  }
}

function canonicalArtifact(data: OperatorWorkspaceData): ArtifactRecord | undefined {
  return [...data.artifacts].filter((artifact) => artifact.tenant_id === data.currentRun.tenant_id && artifact.project_id === data.currentRun.project_id && artifact.run_id === data.currentRun.run_id && artifact.step_id === data.currentRun.step_id).sort((left, right) => right.revision - left.revision || right.artifact_id.localeCompare(left.artifact_id)).at(0)
}

function matchingGate(data: OperatorWorkspaceData, artifact: ArtifactRecord | undefined): GateRead | undefined {
  if (artifact === undefined) return undefined
  return data.gates.find((gate) => gate.tenantId === data.currentRun.tenant_id && gate.projectId === data.currentRun.project_id && gate.runId === data.currentRun.run_id && gate.stepId === data.currentRun.step_id && gate.artifactId === artifact.artifact_id && gate.artifactHash === artifact.content_sha256 && gate.artifactRevision === artifact.revision)
}

function ReviewFieldsForm({ action, fields, setFields, disabled }: { readonly action: ReviewAction; readonly fields: ReviewFields; readonly setFields: (fields: ReviewFields) => void; readonly disabled: boolean }): JSX.Element | null {
  const update = (field: keyof ReviewFields, value: string): void => setFields({ ...fields, [field]: value })
  if (action === "approve") return null
  return <section className="action-consequence"><h3>{actionConfig[action].label} begruenden</h3><label>Begruendung<textarea aria-label="Begruendung" value={fields.reason} onChange={(event) => update("reason", event.currentTarget.value)} disabled={disabled} /></label>{action === "reject" || action === "request-revision" || action === "request-input" || action === "request-waiver" ? <label>{action === "request-waiver" ? "Pruefanweisung fuer Ausnahme" : "Anweisungen"}<textarea aria-label={action === "request-waiver" ? "Pruefanweisung fuer Ausnahme" : "Anweisungen"} value={fields.instructions} onChange={(event) => update("instructions", event.currentTarget.value)} disabled={disabled} /></label> : null}{action === "reject" || action === "request-revision" ? <><label>Betroffene Abschnitte<textarea aria-label="Betroffene Abschnitte" value={fields.affectedSections} onChange={(event) => update("affectedSections", event.currentTarget.value)} disabled={disabled} /></label><label>Unveraenderliche Vorgaben<textarea aria-label="Unveraenderliche Vorgaben" value={fields.immutableConstraints} onChange={(event) => update("immutableConstraints", event.currentTarget.value)} disabled={disabled} /></label></> : null}{action === "escalate" ? <><label>Mindestens zwei Optionen<textarea aria-label="Mindestens zwei Optionen" value={fields.options} onChange={(event) => update("options", event.currentTarget.value)} disabled={disabled} /></label><label>Auswirkungen<textarea aria-label="Auswirkungen" value={fields.impacts} onChange={(event) => update("impacts", event.currentTarget.value)} disabled={disabled} /></label></> : null}</section>
}

export function ReviewWorkspace({ api, data, onReadback }: ReviewWorkspaceProps): JSX.Element {
  const [selectedAction, setSelectedAction] = useState<ReviewAction>("approve")
  const [fields, setFields] = useState<ReviewFields>(emptyFields)
  const action = useAdminAction({ client: api, reload: onReadback })
  const artifact = canonicalArtifact(data)
  const gate = matchingGate(data, artifact)
  const exactEvidence = artifact !== undefined && gate !== undefined
  const locked = action.state.kind === "awaiting-confirmation" || action.state.kind === "confirming" || action.state.kind === "reloading"
  const prepare = (reviewAction: ReviewAction): void => {
    setSelectedAction(reviewAction)
    const currentPayload = payload(reviewAction, fields)
    const baseIntent = { action: reviewAction, tenant_id: data.currentRun.tenant_id, project_id: data.currentRun.project_id, run_id: data.currentRun.run_id, step_id: data.currentRun.step_id, expected_revision: data.currentRun.expected_revision }
    const intent: ActionIntent = currentPayload === undefined ? baseIntent : { ...baseIntent, payload: currentPayload }
    void action.preview(intent)
  }
  const selectAction = (reviewAction: ReviewAction): void => {
    setSelectedAction(reviewAction)
    setFields(emptyFields)
  }
  const result = action.state.kind === "awaiting-confirmation" ? action.state.preview.consequence["result"] : ""
  return <section className="review-layout"><section className="work-panel"><p className="eyebrow">Pruefungen und Freigaben</p><h2>Entscheidung vorbereiten</h2>{artifact === undefined || gate === undefined ? <section className="action-blocker"><h3>Keine exakt gebundene Pruefung</h3><p>Eine Freigabe setzt ein kanonisches Artefakt und einen dazu passenden Pruefnachweis voraus.</p><p>Aktuelles Artefakt und Pruefnachweis erneut laden oder die Pruefung fuer diese Revision abschliessen.</p></section> : <section className="gate-report"><h3>{artifact.storage_key.split("/").at(-1) ?? artifact.storage_key}, Revision {artifact.revision}</h3><dl className="facts"><div><dt>Gate-Ergebnis</dt><dd>{gate.result}</dd></div><div><dt>Nachweis</dt><dd>{Object.entries(gate.evidence).map(([name, value]) => <span key={name}>{name}: {String(value)} </span>)}</dd></div><div><dt>Feststellungen</dt><dd>{gate.findings.length === 0 ? "Keine Feststellungen" : gate.findings.join("; ")}</dd></div><div><dt>Pruefer</dt><dd>{gate.checkerVersion}</dd></div><div><dt>Geprueft am</dt><dd>{gate.checkedAt}</dd></div></dl><details><summary>Technische Details</summary><dl><div><dt>Artefakt-ID</dt><dd>{artifact.artifact_id}</dd></div><div><dt>Inhaltshash</dt><dd>{artifact.content_sha256}</dd></div><div><dt>Gate-Lauf-ID</dt><dd>{gate.qualityGateRunId}</dd></div><div><dt>Gate-ID</dt><dd>{gate.qualityGateId}</dd></div></dl></details></section>}<div className="action-row"><button type="button" onClick={() => prepare("approve")} disabled={!exactEvidence || locked}>Freigabe vorbereiten</button><button type="button" onClick={() => selectAction("request-revision")} disabled={locked}>Revision anfordern</button><button type="button" onClick={() => selectAction("request-input")} disabled={locked}>Eingabe anfordern</button><button type="button" onClick={() => selectAction("reject")} disabled={locked}>Ablehnung vorbereiten</button><button type="button" onClick={() => selectAction("escalate")} disabled={locked}>Eskalation vorbereiten</button><button type="button" onClick={() => selectAction("request-waiver")} disabled={locked}>Ausnahme anfragen</button></div><ReviewFieldsForm action={selectedAction} fields={fields} setFields={setFields} disabled={locked} />{selectedAction !== "approve" ? <button type="button" onClick={() => prepare(selectedAction)} disabled={!fieldsComplete(selectedAction, fields) || locked}>{actionConfig[selectedAction].preview}</button> : null}<section aria-live="polite">{action.state.kind === "idle" && action.state.notice !== undefined ? <p className="action-blocker">{action.state.notice}</p> : null}{action.state.kind === "previewing" ? <p>Vorschau wird geladen.</p> : null}{action.state.kind === "blocked" ? <div className="action-blocker"><h3>Aktion nicht erlaubt</h3>{action.state.preview.blockers.map((blocker) => <div key={blocker.code}><p>{blocker.message}</p><p>{blocker.remediation}</p></div>)}</div> : null}{action.state.kind === "awaiting-confirmation" ? <div className="action-consequence"><h3>Konkrete Folge</h3><p>{typeof result === "string" ? result : "Die Serverfolge wurde vorbereitet."}</p><button type="button" onClick={() => { void action.confirm() }}>{actionConfig[selectedAction].confirmation}</button></div> : null}{action.state.kind === "confirming" ? <p>Aktion wird verbindlich bestaetigt.</p> : null}{action.state.kind === "reloading" ? <p>Kanonischer Stand wird geladen.</p> : null}{action.state.kind === "completed" ? <p className="success-note">{action.state.replay ? "Kanonische Wiederholung bestaetigt." : "Kanonischer Stand aktualisiert"}</p> : null}{action.state.kind === "failed" ? <div className="action-blocker"><h3>Aktion fehlgeschlagen</h3><p>{action.state.message}</p></div> : null}</section></section><aside className="evidence-inline"><h3>Pruefnachweis</h3><p>Freigaben werden erst nach Vorschau, Bestaetigung und kanonischem Readback angezeigt.</p></aside></section>
}
