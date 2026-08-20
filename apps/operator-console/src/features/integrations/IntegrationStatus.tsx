import type { DemoIntegration } from "../../dev/neutralDemo"

type IntegrationStatusProps = {
  readonly integrations: readonly DemoIntegration[]
}

export function IntegrationStatus({ integrations }: IntegrationStatusProps): JSX.Element {
  return (
    <section aria-labelledby="integration-status-title" className="workspace-panel integration-status" role="region">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Non-authoritative delivery view</p>
          <h2 id="integration-status-title">Integration status</h2>
        </div>
        <p className="secondary-id">Transition Service remains the authority.</p>
      </div>
      <div className="table-wrap">
        <table>
          <caption>Simulated integration state</caption>
          <thead>
            <tr>
              <th scope="col">Integration</th>
              <th scope="col">Latest source event and revision</th>
              <th scope="col">Delivery</th>
              <th scope="col">Replay</th>
              <th scope="col">Conflict</th>
              <th scope="col">Retry</th>
              <th scope="col">DLQ</th>
              <th scope="col">Wait and resume</th>
              <th scope="col">Next operator action</th>
            </tr>
          </thead>
          <tbody>
            {integrations.map((integration) => (
              <tr key={integration.label}>
                <th scope="row">{integration.label}</th>
                <td>{integration.latestSource}</td>
                <td>{integration.delivery}</td>
                <td>{integration.replay}</td>
                <td>{integration.conflict}</td>
                <td>{integration.retry}</td>
                <td>{integration.deadLetterQueue}</td>
                <td>{integration.waitResume}</td>
                <td>{integration.nextAction}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <details>
        <summary>Technical details</summary>
        <dl className="technical-details integration-technical-details">
          {integrations.map((integration) => (
            <div key={integration.label}>
              <dt>{integration.label}</dt>
              <dd>Event: {integration.technical.rawEvent}<br />Route: {integration.technical.rawRoute}<br />Delivery reference: {integration.technical.deliveryReference}</dd>
            </div>
          ))}
        </dl>
      </details>
    </section>
  )
}
