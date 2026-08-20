import type { WorkflowStep } from "../../dev/neutralDemo"

type WorkflowMatrixProps = {
  readonly steps: readonly WorkflowStep[]
  readonly sideflow: WorkflowStep
}

function WorkflowMatrixRow({ step }: { readonly step: WorkflowStep }): JSX.Element {
  return (
    <tr>
      <th scope="row"><span className="matrix-step-id">{step.id}</span>{step.label}</th>
      <td>{step.objective}</td>
      <td>{step.inputs.join(", ")}</td>
      <td>{step.outputSummary}</td>
      <td>{step.machineGate}</td>
      <td>{step.humanGate}</td>
      <td><strong>{step.status}</strong><br />{step.statusSummary}</td>
      <td>{step.actionPreview}</td>
    </tr>
  )
}

function MatrixTable({ ariaLabel, steps }: { readonly ariaLabel: string; readonly steps: readonly WorkflowStep[] }): JSX.Element {
  return (
    <div className="table-wrap">
      <table aria-label={ariaLabel}>
        <thead>
          <tr>
            <th scope="col">Step</th>
            <th scope="col">Goal</th>
            <th scope="col">Canonical input</th>
            <th scope="col">Output</th>
            <th scope="col">Machine gate</th>
            <th scope="col">Human gate</th>
            <th scope="col">Current status</th>
            <th scope="col">Next action</th>
          </tr>
        </thead>
        <tbody>{steps.map((step) => <WorkflowMatrixRow key={step.id} step={step} />)}</tbody>
      </table>
    </div>
  )
}

export function WorkflowMatrix({ steps, sideflow }: WorkflowMatrixProps): JSX.Element {
  return (
    <section aria-labelledby="workflow-matrix-title" className="workspace-panel workflow-matrix">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Workflow presentation</p>
          <h2 id="workflow-matrix-title">Workflow Matrix</h2>
        </div>
        <p className="secondary-id">Initial route and post-publication sideflow are distinct.</p>
      </div>
      <ol aria-label="Initial workflow matrix route" className="matrix-route">
        <li className="sr-only">0 1 1b 1c 2 3 4a 4b</li>
        {steps.map((step) => <li key={step.id}>{step.id}</li>)}
      </ol>
      <MatrixTable ariaLabel="Initial workflow matrix" steps={steps} />
      <aside aria-label="Workflow matrix sideflow" className="matrix-sideflow">
        <p className="eyebrow">Post-publication sideflow</p>
        <p>{sideflow.id}</p>
        <MatrixTable ariaLabel="Post-publication workflow matrix" steps={[sideflow]} />
      </aside>
    </section>
  )
}
