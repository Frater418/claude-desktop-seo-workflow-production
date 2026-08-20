import type { NeutralDemoProject } from "../../dev/neutralDemo"

type ProjectDashboardProps = {
  readonly project: NeutralDemoProject
}

export function ProjectDashboard({ project }: ProjectDashboardProps): JSX.Element {
  return (
    <section aria-labelledby="project-dashboard-title" className="dashboard">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Project dashboard</p>
          <h2 id="project-dashboard-title">Operational status</h2>
        </div>
        <p className="next-action"><strong>Next permitted action:</strong> {project.nextAction}</p>
      </div>
      <dl className="metrics-grid">
        <div><dt>Current step</dt><dd>{project.currentStep}</dd></div>
        <div><dt>Progress</dt><dd>{project.progress}</dd></div>
        <div><dt>Open blockers</dt><dd>{project.blockerCount}</dd></div>
        <div><dt>Open tasks</dt><dd>{project.taskCount}</dd></div>
        <div><dt>Review requests</dt><dd>{project.reviewCount}</dd></div>
        <div><dt>Current artifacts</dt><dd>{project.artifactCount}</dd></div>
        <div><dt>Owner</dt><dd>{project.owner}</dd></div>
        <div><dt>Target date</dt><dd>{project.targetDate}</dd></div>
      </dl>
    </section>
  )
}
