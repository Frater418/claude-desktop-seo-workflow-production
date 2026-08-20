import type { WorkflowStep } from "../../dev/neutralDemo"

type WorkflowTimelineProps = {
  readonly steps: readonly WorkflowStep[]
  readonly sideflow: WorkflowStep
  readonly selectedStepId: string
  readonly onSelect: (stepId: string) => void
}

function StepButton({ step, selectedStepId, onSelect }: Pick<WorkflowTimelineProps, "selectedStepId" | "onSelect"> & { readonly step: WorkflowStep }): JSX.Element {
  return (
    <li>
      <button
        aria-label={`Step ${step.id}: ${step.label}`}
        aria-pressed={selectedStepId === step.id}
        className="timeline-step"
        data-state={step.status}
        onClick={() => onSelect(step.id)}
        type="button"
      >
        <span className="step-number">{step.id}</span>
        <span>{step.label}</span>
        <span className="state-label">{step.status}</span>
      </button>
    </li>
  )
}

export function WorkflowTimeline({ steps, sideflow, selectedStepId, onSelect }: WorkflowTimelineProps): JSX.Element {
  return (
    <section aria-labelledby="workflow-title" className="workflow-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Workflow control</p>
          <h2 id="workflow-title">Route and gate position</h2>
        </div>
        <p className="state-key">Released | Awaiting gate | Blocked | Locked | Not due</p>
      </div>
      <ol aria-label="Initial workflow route" className="timeline-route">
        <li className="sr-only">0 1 1b 1c 2 3 4a 4b</li>
        {steps.map((step) => <StepButton key={step.id} onSelect={onSelect} selectedStepId={selectedStepId} step={step} />)}
      </ol>
      <aside aria-label="Post-publication sideflow" className="sideflow">
        <p className="eyebrow">Post-publication sideflow</p>
        <ol>
          <StepButton onSelect={onSelect} selectedStepId={selectedStepId} step={sideflow} />
        </ol>
      </aside>
    </section>
  )
}
