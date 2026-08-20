import type { DemoTask, DemoTaskId } from "../../dev/neutralDemo"

type TaskQueueProps = {
  readonly tasks: readonly DemoTask[]
  readonly selectedTaskId: DemoTaskId
  readonly onSelectTask: (taskId: DemoTaskId) => void
}

export function TaskQueue({ tasks, selectedTaskId, onSelectTask }: TaskQueueProps): JSX.Element {
  return (
    <section aria-labelledby="task-queue-title" className="workspace-panel task-queue">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Operations queue</p>
          <h2 id="task-queue-title">Task Queue</h2>
        </div>
        <p className="secondary-id">Select a task to inspect its required route.</p>
      </div>
      <div aria-label="Task queue" className="task-list">
        {tasks.map((task) => {
          const selected = task.id === selectedTaskId

          return (
            <article className="task-card" data-selected={selected} key={task.id}>
              <button
                aria-label={`Task: ${task.title}`}
                aria-pressed={selected}
                className="task-select"
                onClick={() => onSelectTask(task.id)}
                type="button"
              >
                <span>{task.title}</span>
                <span className="task-state">{task.status}</span>
              </button>
              <dl className="task-facts">
                <div><dt>Type</dt><dd>{task.type}</dd></div>
                <div><dt>Severity</dt><dd>{task.severity}</dd></div>
                <div><dt>Status</dt><dd>{task.status}</dd></div>
                <div><dt>Owner role</dt><dd>{task.ownerRole}</dd></div>
                <div><dt>Assignee</dt><dd>{task.assignee}</dd></div>
                <div><dt>Due date</dt><dd>{task.dueDate}</dd></div>
                <div><dt>Source step</dt><dd>{task.sourceStep}</dd></div>
                <div><dt>Next action</dt><dd>{task.nextAction}</dd></div>
                <div className="task-dependency"><dt>Dependency</dt><dd>{task.dependency}</dd></div>
              </dl>
            </article>
          )
        })}
      </div>
    </section>
  )
}
