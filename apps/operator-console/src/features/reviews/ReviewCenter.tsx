import {
  activeGateReview,
  reviewDecisionOptions,
  reviewDecisions,
  type ReviewDecisionId,
} from "../../dev/neutralDemo"

type ReviewCenterProps = {
  readonly selectedDecisionId: ReviewDecisionId
  readonly onSelectDecision: (decisionId: ReviewDecisionId) => void
}

export function ReviewCenter({ selectedDecisionId, onSelectDecision }: ReviewCenterProps): JSX.Element {
  const selectedDecision = reviewDecisions[selectedDecisionId]

  return (
    <section aria-labelledby="review-center-title" className="workspace-panel review-center">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Human gate review</p>
          <h2 id="review-center-title">Review Center</h2>
        </div>
        <p className="status-badge">{activeGateReview.status}</p>
      </div>
      <dl className="review-facts">
        <div><dt>Review</dt><dd>{activeGateReview.title}</dd></div>
        <div><dt>Artifact</dt><dd>{activeGateReview.artifactLabel}, revision {activeGateReview.artifactRevision}</dd></div>
        <div><dt>Reviewer role</dt><dd>{activeGateReview.reviewerRole}</dd></div>
        <div><dt>Deadline</dt><dd>{activeGateReview.deadline}</dd></div>
      </dl>
      <div className="review-evidence-grid">
        <section><h3>Machine-gate evidence</h3><ul>{activeGateReview.machineGateEvidence.map((item) => <li key={item}>{item}</li>)}</ul></section>
        <section><h3>Human findings</h3><ul>{activeGateReview.humanFindings.map((item) => <li key={item}>{item}</li>)}</ul></section>
      </div>
      <section className="review-escalation"><h3>Escalation path</h3><p>{activeGateReview.escalationPath}</p></section>
      <section className="review-sources"><h3>Source links</h3><ul>{activeGateReview.sourceLinks.map((source) => <li key={source.href}><a href={source.href}>{source.label}</a></li>)}</ul></section>
      <fieldset className="review-decisions">
        <legend>Local decision preview</legend>
        <div className="decision-options">
          {reviewDecisionOptions.map((decision) => (
            <label className="decision-option" key={decision.id}>
              <input checked={selectedDecisionId === decision.id} name="review-decision" onChange={() => onSelectDecision(decision.id)} type="radio" value={decision.id} />
              <span>{decision.label}</span>
            </label>
          ))}
        </div>
      </fieldset>
      <section aria-label="Decision consequence" aria-live="polite" className="decision-preview" data-decision={selectedDecision.id}>
        <h3>Structured local preview</h3>
        <dl>
          <div><dt>Selected decision</dt><dd>{selectedDecision.label}</dd></div>
          <div><dt>Expected revision</dt><dd>{selectedDecision.expectedRevision}</dd></div>
          <div><dt>Consequence</dt><dd>{selectedDecision.consequence}</dd></div>
        </dl>
      </section>
      <div className="review-submit"><p>Final decision requires Transition Service/API and is disabled in local simulation.</p><button disabled type="button">Transition Service/API required</button></div>
      <details>
        <summary>Technical details</summary>
        <dl className="technical-details">
          <div><dt>Artifact hash</dt><dd>{activeGateReview.artifactHash}</dd></div>
          <div><dt>Review ID</dt><dd>{activeGateReview.technical.reviewId}</dd></div>
          <div><dt>Raw event</dt><dd>{activeGateReview.technical.rawEvent}</dd></div>
          <div><dt>Raw route</dt><dd>{activeGateReview.technical.rawRoute}</dd></div>
        </dl>
      </details>
    </section>
  )
}
