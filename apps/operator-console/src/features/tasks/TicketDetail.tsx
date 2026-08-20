import type { DemoTask } from "../../dev/neutralDemo"

type TicketDetailProps = {
  readonly task: DemoTask
}

export function TicketDetail({ task }: TicketDetailProps): JSX.Element {
  return (
    <section aria-labelledby="ticket-detail-title" className="workspace-panel ticket-detail">
      <div className="detail-heading">
        <div>
          <p className="eyebrow">Selected ticket</p>
          <h2 id="ticket-detail-title">{task.title}</h2>
        </div>
        <p className="status-badge">{task.status}</p>
      </div>
      <dl className="ticket-context">
        <div><dt>Selected context</dt><dd>{task.sourceStep}</dd></div>
        <div><dt>Owner role</dt><dd>{task.ownerRole}</dd></div>
        <div><dt>Assignee</dt><dd>{task.assignee}</dd></div>
        <div><dt>Due date</dt><dd>{task.dueDate}</dd></div>
      </dl>
      <section className="ticket-route"><h3>Error and route class</h3><p>{task.routeClass}</p></section>
      <div className="ticket-detail-grid">
        <section><h3>Evidence and findings</h3><ul>{task.evidence.map((finding) => <li key={finding}>{finding}</li>)}</ul></section>
        <section><h3>Remediation checklist</h3><ul className="checklist">{task.remediationChecklist.map((item) => <li key={item}>{item}</li>)}</ul></section>
      </div>
      <section className="ticket-resolution"><h3>Expected resolution</h3><p>{task.expectedResolution}</p></section>
      <section className="ticket-escalation"><h3>Escalation path</h3><p>{task.escalationPath}</p></section>
      <section className="ticket-sources"><h3>Source links</h3><ul>{task.sourceLinks.map((source) => <li key={source.href}><a href={source.href}>{source.label}</a></li>)}</ul></section>
      <details>
        <summary>Technical details</summary>
        <dl className="technical-details">
          <div><dt>Task ID</dt><dd>{task.technical.taskId}</dd></div>
          <div><dt>Correlation ID</dt><dd>{task.technical.correlationId}</dd></div>
          <div><dt>Raw route</dt><dd>{task.technical.rawRoute}</dd></div>
        </dl>
      </details>
    </section>
  )
}
