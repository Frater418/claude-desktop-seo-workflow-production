import { useId, useState } from "react"
import type { OperatorWorkspaceData } from "./useOperatorWorkspace"

type ContextPanelProps = { readonly data: OperatorWorkspaceData }

export function ContextPanel({ data }: ContextPanelProps): JSX.Element {
  const [isExpanded, setIsExpanded] = useState(true)
  const contentId = useId()
  const gateFindings = data.current.gate?.findings ?? []
  const dependencies = [...new Set([data.current.step?.blocker ?? "", ...data.tasks.map((task) => task.dependency)].filter((dependency) => dependency !== ""))]
  const revisions = [...data.artifacts].sort((left, right) => right.revision - left.revision)
  const artifact = data.current.artifact
  const gate = data.current.gate
  const context = data.current.context

  return <aside aria-labelledby="context-panel-title" className="evidence-panel">
    <div className="context-panel-heading">
      <div><p className="eyebrow">Arbeitskontext</p><h2 id="context-panel-title">Kontext und Nachweise</h2></div>
      <button aria-controls={contentId} aria-expanded={isExpanded} onClick={() => setIsExpanded((expanded) => !expanded)} type="button">{isExpanded ? "Kontext einklappen" : "Kontext ausklappen"}</button>
    </div>
    {isExpanded ? <div className="context-panel-content" id={contentId}>
      <section aria-labelledby="evidence-title" className="context-group"><h3 id="evidence-title">Nachweise</h3>{context === null ? <p>Aktueller Kontext nicht verfuegbar.</p> : <><p>{context.title}</p><p>{context.finding}</p></>}{gate === null ? <p>Aktueller Pruefbericht nicht verfuegbar.</p> : <p>Maschinenpruefung liegt vor.</p>}</section>
      <section aria-labelledby="findings-title" className="context-group"><h3 id="findings-title">Feststellungen</h3>{gateFindings.length === 0 ? <p>Keine Feststellungen.</p> : <ul>{gateFindings.map((finding) => <li key={finding}>{finding}</li>)}</ul>}</section>
      <section aria-labelledby="dependencies-title" className="context-group"><h3 id="dependencies-title">Abhaengigkeiten</h3>{dependencies.length === 0 ? <p>Keine Abhaengigkeiten.</p> : <ul>{dependencies.map((dependency) => <li key={dependency}>Abhaengigkeit: {dependency}</li>)}</ul>}</section>
      <section aria-labelledby="lineage-title" className="context-group"><h3 id="lineage-title">Revisionsverlauf</h3>{revisions.length === 0 ? <p>Keine Artefaktrevision vorhanden.</p> : <ol>{revisions.map((revision) => <li key={revision.artifact_id}>Artefaktrevision {revision.revision}</li>)}</ol>}</section>
      <details><summary>Technische Details</summary><dl className="technical-facts"><div><dt>Projekt-ID</dt><dd>{data.projectId}</dd></div><div><dt>Lauf-ID</dt><dd>{data.currentRun.run_id}</dd></div><div><dt>Schritt-ID</dt><dd>{data.currentRun.step_id}</dd></div>{artifact === null ? null : <><div><dt>Artefakt-ID</dt><dd>{artifact.artifact_id}</dd></div><div><dt>Inhaltshash</dt><dd>{artifact.content_sha256}</dd></div></>}{gate === null ? null : <><div><dt>Gate-ID</dt><dd>{gate.qualityGateId}</dd></div><div><dt>Gate-Lauf-ID</dt><dd>{gate.qualityGateRunId}</dd></div></>}</dl></details>
    </div> : null}
  </aside>
}
