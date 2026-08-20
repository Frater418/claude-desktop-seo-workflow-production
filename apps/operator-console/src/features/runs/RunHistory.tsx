type DemoRun = {
  readonly id: string
  readonly result: string
  readonly provider: string
  readonly model: string
  readonly promptVersion: string
  readonly workerProfile: string
  readonly toolPolicy: string
  readonly tokenUse: string
  readonly output: string
  readonly cacheState: string
}

const demoRuns: readonly DemoRun[] = [
  {
    id: "run-neutral-architecture-r2",
    result: "released",
    provider: "provider-local-simulated",
    model: "model-planning-simulated-v2",
    promptVersion: "1b-site-architecture 2.0.0",
    workerProfile: "worker-profile-information-architecture 2.0.0",
    toolPolicy: "tool-policy-architecture-safe 1.0.0",
    tokenUse: "8,420 input / 1,304 output",
    output: "Approved architecture package, revision 2",
    cacheState: "available cache hint",
  },
  {
    id: "run-neutral-navigation-r3",
    result: "rejected",
    provider: "provider-local-simulated",
    model: "model-planning-simulated-v2",
    promptVersion: "1b-site-architecture 2.0.0",
    workerProfile: "worker-profile-information-architecture 2.0.0",
    toolPolicy: "tool-policy-architecture-safe 1.0.0",
    tokenUse: "8,792 input / 1,118 output",
    output: "Navigation resolution package, revision 3",
    cacheState: "expired cache hint",
  },
  {
    id: "run-neutral-navigation-r4",
    result: "pending recovery",
    provider: "provider-local-simulated",
    model: "model-planning-simulated-v2",
    promptVersion: "1b-site-architecture 2.0.0",
    workerProfile: "worker-profile-information-architecture 2.0.0",
    toolPolicy: "tool-policy-architecture-safe 1.0.0",
    tokenUse: "Not dispatched",
    output: "Expected navigation resolution package, revision 4",
    cacheState: "lost handle: recover fresh",
  },
]

export function RunHistory(): JSX.Element {
  return (
    <section aria-labelledby="run-history-title" className="workspace-panel run-history">
      <div className="section-heading">
        <div><p className="eyebrow">Run history</p><h2 id="run-history-title">One logical project session</h2></div>
        <p className="secondary-id">local_core authority</p>
      </div>
      <p className="plain-status">Logical session <strong>logical-session-northwind-0001</strong> is the source of truth. Technical sessions are replaceable cache, not source of truth.</p>
      <div className="run-list">
        {demoRuns.map((run) => (
          <article className="run-card" key={run.id}>
            <div className="run-heading"><h3>{run.id}</h3><p className="status-badge">{run.result}</p></div>
            <dl className="run-facts">
              <div><dt>Provider</dt><dd>{run.provider}</dd></div>
              <div><dt>Model</dt><dd>{run.model}</dd></div>
              <div><dt>Prompt version</dt><dd>{run.promptVersion}</dd></div>
              <div><dt>Worker profile</dt><dd>{run.workerProfile}</dd></div>
              <div><dt>Tool policy</dt><dd>{run.toolPolicy}</dd></div>
              <div><dt>Token use</dt><dd>{run.tokenUse}</dd></div>
              <div><dt>Output artifact / revision</dt><dd>{run.output}</dd></div>
              <div><dt>Technical-session cache</dt><dd>{run.cacheState}</dd></div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  )
}
