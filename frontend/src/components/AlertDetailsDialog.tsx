import { ArrowLeft, ExternalLink } from 'lucide-react'
import type { AlertRecord } from '../types'

export function AlertDetailsDialog({ alert, onClose, onOpenAlerts, openAlertsLabel = 'Open Alerts page' }: {
  alert: AlertRecord
  onClose: () => void
  onOpenAlerts: () => void
  openAlertsLabel?: string
}) {
  return (
    <div className="metric-detail-backdrop" onMouseDown={event => {
      if (event.target === event.currentTarget) onClose()
    }}>
      <section className="panel metric-detail-dialog alert-detail-dialog" role="dialog" aria-modal="true" aria-labelledby="alert-detail-title">
        <div className="metric-detail-heading">
          <div>
            <span className={'severity-label ' + alert.severity}>{alert.severity} alert</span>
            <h2 id="alert-detail-title">{alert.title}</h2>
            <p>{alert.summary}</p>
          </div>
          <button className="icon-button" aria-label="Close alert details" onClick={onClose}>×</button>
        </div>
        <div className="metric-detail-content">
          <dl className="alert-detail-fields">
            <div><dt>Status</dt><dd><span className={'alert-status ' + alert.status}>{alert.status}</span></dd></div>
            <div><dt>Severity</dt><dd className={'severity-label ' + alert.severity}>{alert.severity}</dd></div>
            <div><dt>System</dt><dd>{alert.entity ?? alert.entity_id ?? 'Unassigned'}</dd></div>
            <div><dt>Occurrences</dt><dd>{alert.occurrence_count}</dd></div>
            <div><dt>First seen</dt><dd>{new Date(alert.triggered_at).toLocaleString()}</dd></div>
            <div><dt>Last seen</dt><dd>{new Date(alert.last_seen_at).toLocaleString()}</dd></div>
            <div><dt>Rule</dt><dd>{alert.rule_id ?? 'Rule removed'}</dd></div>
            <div><dt>Source observation</dt><dd>{alert.source_observation_id}</dd></div>
            {alert.acknowledged_at && <div><dt>Acknowledged</dt><dd>{new Date(alert.acknowledged_at).toLocaleString()}</dd></div>}
            {alert.resolved_at && <div><dt>Resolved</dt><dd>{new Date(alert.resolved_at).toLocaleString()}</dd></div>}
            <div><dt>Alert ID</dt><dd>{alert.id}</dd></div>
          </dl>
        </div>
        <div className="metric-detail-actions">
          <button className="secondary-button" onClick={onClose}><ArrowLeft size={15} />Back</button>
          <button className="primary-button" onClick={onOpenAlerts}>{openAlertsLabel}<ExternalLink size={14} /></button>
        </div>
      </section>
    </div>
  )
}
