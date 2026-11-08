import { Activity, Cable } from 'lucide-react'
import type { Connector, ObservationRecord } from '../types'

export function RightRail({
  observations,
  connectors,
}: {
  observations: ObservationRecord[]
  connectors: Connector[]
}) {
  return (
    <aside className="right-rail">
      <section className="panel side-panel">
        <div className="panel-heading compact">
          <h2>Recent Observations</h2>
        </div>

        <div className="observation-list">
          {observations.length === 0 ? (
            <div className="panel-empty">
              <Activity size={24} />
              <strong>No observations yet</strong>
              <span>
                Events created by connectors will appear here.
              </span>
            </div>
          ) : (
            observations.slice(0, 5).map((observation) => (
              <article className="observation" key={observation.id}>
                <span className="observation-icon tone-blue">
                  <Activity size={18} />
                </span>

                <div className="observation-copy">
                  <time>
                    {new Date(observation.timestamp).toLocaleTimeString()}
                  </time>
                  <strong>{observation.summary}</strong>
                  <small>{observation.source}</small>
                </div>

                <span className="category tone-blue">
                  {observation.severity}
                </span>
              </article>
            ))
          )}
        </div>
      </section>

      <section className="panel side-panel connector-panel">
        <div className="panel-heading compact">
          <h2>Connector Health</h2>
        </div>

        <div className="connector-list">
          {connectors.length === 0 ? (
            <div className="panel-empty">
              <Cable size={24} />
              <strong>No connectors configured</strong>
              <span>
                Add your first connector to begin receiving data.
              </span>
            </div>
          ) : (
            connectors.map((connector) => (
              <div className="connector-row" key={connector.name}>
                <span className={`connector-dot ${connector.status}`} />
                <strong>{connector.name}</strong>
                <span className={`connector-state ${connector.status}`}>
                  {connector.status}
                </span>
                <small>{connector.rate}</small>
                <time>{connector.lastSeen}</time>
              </div>
            ))
          )}
        </div>
      </section>
    </aside>
  )
}
