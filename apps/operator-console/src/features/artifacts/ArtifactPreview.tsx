export type DemoArtifact = {
  readonly id: string
  readonly label: string
  readonly type: string
  readonly status: string
  readonly revision: number
  readonly parentRevision: number
  readonly producer: string
  readonly outputSummary: string
  readonly evidenceCount: number
  readonly locationLabel: string
  readonly locationTarget: string
  readonly hash: string
  readonly storageId: string
  readonly diff: {
    readonly added: string
    readonly changed: string
    readonly removed: string
    readonly unchanged: string
    readonly operatorImpact: string
  }
}

export const defaultDemoArtifact: DemoArtifact = {
    id: "architecture-release-r2",
    label: "Approved architecture package",
    type: "Information architecture",
    status: "released",
    revision: 2,
    parentRevision: 1,
    producer: "Information architecture worker",
    outputSummary: "Released sitemap, URL schema, and internal-link tree for Northwind Facilities rollout.",
    evidenceCount: 14,
    locationLabel: "Notion simulated: Northwind / Architecture / revision 2",
    locationTarget: "#northwind-architecture-revision-2",
    hash: "d2b5f70880aa6428bcd7e492487274aed69152aa33a0415dd230e8c46ba12f90",
    storageId: "artifact-store-neutral-architecture-r2",
    diff: {
      added: "Service-area grouping and required route ownership notes.",
      changed: "Primary navigation labels now use the approved theme vocabulary.",
      removed: "The ambiguous legacy top-level grouping.",
      unchanged: "Validated topic coverage and approved URL constraints.",
      operatorImpact: "Released revision 2 is the immutable predecessor for downstream work.",
    },
}

export const demoArtifacts: readonly DemoArtifact[] = [
  defaultDemoArtifact,
  {
    id: "navigation-resolution-r3",
    label: "Navigation resolution package",
    type: "Revision candidate",
    status: "rejected",
    revision: 3,
    parentRevision: 2,
    producer: "Information architecture worker",
    outputSummary: "Candidate navigation labels and route ownership changes awaiting a fresh revision run.",
    evidenceCount: 5,
    locationLabel: "Local workspace: architecture review / revision 3",
    locationTarget: "#northwind-architecture-revision-3",
    hash: "a7cbe64019f5c66d975cb5d8d8c71fd49bc0207c2fe4d28d69eb1cc1936e2f40",
    storageId: "artifact-store-neutral-navigation-r3",
    diff: {
      added: "Accessibility route notes for the proposed navigation wording.",
      changed: "Primary navigation labels resolve the duplicate route conflict differently.",
      removed: "The duplicate primary route label from the candidate menu.",
      unchanged: "Validated topic coverage, URL constraints, and released predecessor evidence.",
      operatorImpact: "Rejected candidate retained for review. A revision run creates a new artifact identity, not an overwrite.",
    },
  },
]

type ArtifactPreviewProps = {
  readonly selectedArtifact: DemoArtifact
  readonly onSelectArtifact: (artifactId: string) => void
}

export function ArtifactPreview({ selectedArtifact, onSelectArtifact }: ArtifactPreviewProps): JSX.Element {
  return (
    <section aria-labelledby="artifact-preview-title" className="workspace-panel artifact-preview">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Artifact preview</p>
          <h2 id="artifact-preview-title">Current artifact</h2>
        </div>
        <p className="status-badge" data-state={selectedArtifact.status}>{selectedArtifact.status}</p>
      </div>
      <div className="artifact-selector" aria-label="Artifacts">
        {demoArtifacts.map((artifact) => (
          <button
            aria-pressed={artifact.id === selectedArtifact.id}
            aria-label={`Artifact: ${artifact.label}, revision ${artifact.revision}`}
            className="artifact-option"
            key={artifact.id}
            onClick={() => onSelectArtifact(artifact.id)}
            type="button"
          >
            <span>{artifact.label}</span>
            <span>revision {artifact.revision}</span>
          </button>
        ))}
      </div>
      <dl className="artifact-facts">
        <div><dt>Type</dt><dd>{selectedArtifact.type}</dd></div>
        <div><dt>Revision</dt><dd>{selectedArtifact.revision}</dd></div>
        <div><dt>Parent revision</dt><dd>{selectedArtifact.parentRevision}</dd></div>
        <div><dt>Producer</dt><dd>{selectedArtifact.producer}</dd></div>
        <div><dt>Evidence</dt><dd>{selectedArtifact.evidenceCount} verified references</dd></div>
      </dl>
      <section className="artifact-output"><h3>Output summary</h3><p>{selectedArtifact.outputSummary}</p></section>
      <p className="artifact-location"><strong>Location:</strong> <a href={selectedArtifact.locationTarget}>{selectedArtifact.locationLabel}</a></p>
      <details>
        <summary>Technical details</summary>
        <dl className="technical-details">
          <div><dt>Artifact hash</dt><dd>{selectedArtifact.hash}</dd></div>
          <div><dt>Storage ID</dt><dd>{selectedArtifact.storageId}</dd></div>
        </dl>
      </details>
    </section>
  )
}
