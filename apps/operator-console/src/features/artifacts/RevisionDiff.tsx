import type { DemoArtifact } from "./ArtifactPreview"

type RevisionDiffProps = {
  readonly artifact: DemoArtifact
}

export function RevisionDiff({ artifact }: RevisionDiffProps): JSX.Element {
  return (
    <section aria-labelledby="revision-diff-title" className="workspace-panel revision-diff">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Immutable comparison</p>
          <h2 id="revision-diff-title">Revision {artifact.revision} compared with revision {artifact.parentRevision}</h2>
        </div>
        <p className="secondary-id">Both revisions remain available for review</p>
      </div>
      <div className="diff-grid">
        <section><h3>Added</h3><p>{artifact.diff.added}</p></section>
        <section><h3>Changed</h3><p>{artifact.diff.changed}</p></section>
        <section><h3>Removed</h3><p>{artifact.diff.removed}</p></section>
        <section><h3>Unchanged</h3><p>{artifact.diff.unchanged}</p></section>
      </div>
      <section className="operator-impact"><h3>Operator impact</h3><p>{artifact.diff.operatorImpact}</p></section>
      <details>
        <summary>Technical details</summary>
        <dl className="technical-details">
          <div><dt>Current immutable hash</dt><dd>{artifact.hash}</dd></div>
          <div><dt>Comparison base</dt><dd>revision-{artifact.parentRevision}-immutable</dd></div>
        </dl>
      </details>
    </section>
  )
}
