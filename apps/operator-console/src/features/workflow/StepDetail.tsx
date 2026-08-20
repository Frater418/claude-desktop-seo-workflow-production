import type { WorkflowStep } from "../../dev/neutralDemo"

type StepDetailProps = {
  readonly step: WorkflowStep
  readonly projectId: string
}

export function StepDetail({ step, projectId }: StepDetailProps): JSX.Element {
  return (
    <section aria-labelledby="step-detail-title" className="step-detail">
      <div className="detail-heading">
        <div>
          <p className="eyebrow">Selected step {step.id}</p>
          <h2 id="step-detail-title">{step.label}</h2>
        </div>
        <p className="status-badge" data-state={step.status}>{step.status}</p>
      </div>
      <p className="objective">{step.objective}</p>
      <p className="plain-status"><strong>Status:</strong> {step.statusSummary}</p>
      <div className="detail-grid">
        <section><h3>Inputs</h3><ul>{step.inputs.map((input) => <li key={input}>{input}</li>)}</ul></section>
        <section><h3>Tools</h3><ul>{step.tools.map((tool) => <li key={tool}>{tool}</li>)}</ul></section>
        <section><h3>Quality and human gates</h3><ul>{step.gates.map((gate) => <li key={gate}>{gate}</li>)}</ul></section>
        <section><h3>Findings</h3><ul>{step.findings.map((finding) => <li key={finding}>{finding}</li>)}</ul></section>
      </div>
      <section className="output-summary"><h3>Output summary</h3><p>{step.outputSummary}</p></section>
      <section className="context-summary"><h3>Context Package</h3><p>{step.contextSummary}</p><p><strong>Worker profile:</strong> {step.workerProfile}</p><p><strong>Prompt version:</strong> {step.promptVersion}</p><p><strong>LLM state:</strong> {step.llmState}</p></section>
      <section><h3>Operator checklist</h3><ul className="checklist">{step.checklist.map((item) => <li key={item}>{item}</li>)}</ul></section>
      <section className="action-preview"><h3>Allowed action previews</h3><p>{step.actionPreview}</p><div><button disabled type="button">Start step preview</button><button disabled type="button">Approve gate preview</button></div></section>
      <details>
        <summary>Technical details</summary>
        <dl className="technical-details">
          <div><dt>Project ID</dt><dd>{projectId}</dd></div>
          <div><dt>Step projection ID</dt><dd>{step.technicalId}</dd></div>
          <div><dt>Projection handling</dt><dd>Raw projection details remain intentionally undisplayed in this Package 1 view.</dd></div>
        </dl>
      </details>
    </section>
  )
}
