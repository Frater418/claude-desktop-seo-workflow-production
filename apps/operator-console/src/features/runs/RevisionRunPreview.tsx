export function RevisionRunPreview(): JSX.Element {
  return (
    <section aria-labelledby="revision-run-title" className="workspace-panel revision-run-preview">
      <div className="section-heading">
        <div><p className="eyebrow">Revision run preview</p><h2 id="revision-run-title">Fresh revision, Review Center controlled</h2></div>
        <p className="status-badge">preview only</p>
      </div>
      <div className="preview-grid">
        <section><h3>Rejected artifact</h3><p>Navigation resolution package, revision 3. The rejected artifact remains immutable and available as comparison input.</p></section>
        <section><h3>Machine findings</h3><p>Two primary navigation labels resolve to the same route.</p></section>
        <section><h3>Human finding</h3><p>Keep the approved service-area grouping visible while resolving route ownership.</p></section>
        <section><h3>Operator instruction</h3><p>Produce a new candidate with distinct labels and preserve all approved topic coverage.</p></section>
        <section><h3>Immutable fields</h3><ul><li>Project and logical session identity</li><li>Released topic inventory revision 2</li><li>Rejected revision 3 and finding record</li></ul></section>
        <section><h3>Forbidden changes</h3><ul><li>No in-place overwrite of revision 3</li><li>No technical-session reuse for revision dispatch</li><li>No removal of approved predecessor evidence</li></ul></section>
        <section><h3>Expected new revision</h3><p>Navigation resolution package, revision 4, plus navigation validation report.</p></section>
        <section><h3>Model and tool policy</h3><p>model-planning-simulated-v2 with tool-policy-architecture-safe 1.0.0. Execution must be fresh.</p></section>
      </div>
      <section className="identity-preview"><h3>New artifact identity preview</h3><p>artifact-northwind-navigation-r4. This identity is reserved for the expected output and cannot replace the rejected artifact.</p></section>
      <div className="dispatch-preview"><p>Dispatch disabled: Review Center is required.</p><button disabled type="button">Review Center is required</button></div>
    </section>
  )
}
