import type { BaselineComparisonRow } from "../../dev/neutralDemo"

type BaselineComparisonProps = {
  readonly rows: readonly BaselineComparisonRow[]
}

export function BaselineComparison({ rows }: BaselineComparisonProps): JSX.Element {
  return (
    <section aria-labelledby="baseline-comparison-title" className="workspace-panel baseline-comparison">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Operating capability</p>
          <h2 id="baseline-comparison-title">Baseline Comparison</h2>
        </div>
        <p className="secondary-id">Capability comparison only</p>
      </div>
      <p className="comparison-caveat">Capability comparison only. This is not measured performance or production readiness.</p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th scope="col">Capability</th><th scope="col">Original manual and chat-based risk</th><th scope="col">Current Core-backed contract</th></tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.capability}>
                <th scope="row">{row.capability}</th>
                <td>{row.manualBaseline}</td>
                <td>{row.currentContract}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
