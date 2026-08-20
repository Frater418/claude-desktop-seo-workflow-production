export function ContextPackageSummary(): JSX.Element {
  return (
    <section aria-labelledby="context-package-title" className="workspace-panel context-package">
      <div className="section-heading">
        <div><p className="eyebrow">Context package summary</p><h2 id="context-package-title">Revision package for step 1b</h2></div>
        <p className="status-badge">valid</p>
      </div>
      <dl className="context-facts">
        <div><dt>Target</dt><dd>Step 1b, revision 4</dd></div>
        <div><dt>Trigger</dt><dd>revision</dd></div>
        <div><dt>Official prompt</dt><dd>heartweb.step.1b, 2.0.0</dd></div>
        <div><dt>Output contracts</dt><dd>Architecture package and navigation validation report</dd></div>
        <div><dt>Trusted current sources</dt><dd>Project v2 and released topic inventory</dd></div>
        <div><dt>Approved predecessors</dt><dd>Topic inventory revision 2</dd></div>
        <div><dt>Evidence and findings</dt><dd>Route conflict finding and verified navigation evidence</dd></div>
        <div><dt>Operator instruction</dt><dd>Resolve duplicate navigation labels without changing released topic coverage.</dd></div>
        <div><dt>Source count</dt><dd>8 immutable sources</dd></div>
        <div><dt>Rebuild status</dt><dd>Deterministic rebuild available from immutable package</dd></div>
      </dl>
      <section className="recovery-note"><h3>Technical-session cache</h3><p>Lost handle. Decision: <strong>recover fresh</strong>.</p><p>Immutable context package remains valid.</p></section>
      <details>
        <summary>Technical details</summary>
        <dl className="technical-details">
          <div><dt>Package ID</dt><dd>context-northwind-revision-0004</dd></div>
          <div><dt>Package hash</dt><dd>4e5b01cdf313bd9d610a97817b8520e4d3f189cb041e3c48a7bcae00f1ea3cd5</dd></div>
          <div><dt>Technical session decision</dt><dd>recover_fresh</dd></div>
        </dl>
      </details>
    </section>
  )
}
