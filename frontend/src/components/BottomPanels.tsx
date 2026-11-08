import { useEffect, useState } from 'react'
import { Activity, AlertTriangle, ArrowUpRight, CheckCircle2, Server } from 'lucide-react'
import type { AlertRecord, Asset, ObservationRecord, PageKey, SystemHealth } from '../types'
import { AlertDetailsDialog } from './AlertDetailsDialog'

export function BottomPanels({ observations, health, assets, alerts, onNavigate }: {
  observations: ObservationRecord[]
  health: SystemHealth
  assets: Asset[]
  alerts: AlertRecord[]
  onNavigate: (page: PageKey) => void
}) {
  const [showStatus, setShowStatus] = useState(false)
  const [selectedAlert, setSelectedAlert] = useState<AlertRecord | null>(null)
  const activeAlerts = alerts.filter(alert => alert.status !== 'resolved')
  const onlineCount = assets.filter(asset => asset.state === 'online').length
  const healthyCount = assets.filter(asset => asset.health === 'healthy').length

  useEffect(() => {
    if (!showStatus && !selectedAlert) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { setShowStatus(false); setSelectedAlert(null) }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [showStatus, selectedAlert])

  return (
    <>
      <section className="bottom-grid">
        <button className="panel chart-panel overview-panel-button" onClick={() => onNavigate('observations')} aria-label="Open observation activity">
          <div className="panel-heading compact"><h2>Observation Activity <span>(Current session)</span></h2><ArrowUpRight size={16} /></div>
          {observations.length === 0 ? (
            <div className="large-panel-empty"><Activity size={30} /><strong>No event activity</strong><span>New health checks and incoming events will appear here.</span></div>
          ) : (
            <div className="activity-detail-list">
              <div className="activity-summary"><strong>{observations.length}</strong><span>observations currently available · View all</span></div>
              {observations.slice(0, 3).map(observation => (
                <div className="activity-detail-row" key={observation.id}>
                  <Activity size={15} />
                  <span><strong>{observation.summary}</strong><small>{new Date(observation.timestamp).toLocaleTimeString()} · {observation.source}</small></span>
                  <b className={'severity-label ' + observation.severity}>{observation.severity}</b>
                </div>
              ))}
            </div>
          )}
        </button>

        <section className="panel alerts-panel">
          <div className="panel-heading compact"><h2>Alerts</h2><button className="panel-link-action" onClick={() => onNavigate('alerts')}>Open Alerts <ArrowUpRight size={15} /></button></div>
          {activeAlerts.length === 0 ? (
            <button className="overview-empty-action" onClick={() => onNavigate('alerts')}><CheckCircle2 size={30} /><strong>No active alerts</strong><span>Open Alerts to review resolved alerts and rule results.</span></button>
          ) : (
            <div className="overview-alert-list">
              {activeAlerts.slice(0, 3).map(alert => (
                <button className="overview-alert-row" key={alert.id} onClick={() => setSelectedAlert(alert)}>
                  <span className={'severity-mark ' + alert.severity}><AlertTriangle size={15} /></span>
                  <span className="overview-alert-copy"><strong>{alert.title}</strong><small>{alert.entity ?? 'System'} · {alert.status} · {alert.occurrence_count} occurrence{alert.occurrence_count === 1 ? '' : 's'}</small></span>
                  <ArrowUpRight size={15} />
                </button>
              ))}
              {activeAlerts.length > 3 && <button className="panel-link-action overview-more-alerts" onClick={() => onNavigate('alerts')}>View {activeAlerts.length - 3} more alerts</button>}
            </div>
          )}
        </section>

        <button className="panel status-panel overview-panel-button" onClick={() => setShowStatus(true)} aria-label="Open detailed system status">
          <div className="panel-heading compact"><h2>System Status</h2><ArrowUpRight size={16} /></div>
          <div className="status-content">
            <div className="status-list">
              <span><Server size={16} />Sentinel Core: {health.status}</span>
              <span><Activity size={16} />Event queue: {health.queueDepth}</span>
              <span><CheckCircle2 size={16} />Version: {health.version}</span>
              <span><CheckCircle2 size={16} />Uptime: {health.uptime}</span>
            </div>
            <div className={'health-ring health-' + health.status}><strong>{health.status === 'healthy' ? 'OK' : '—'}</strong><span>Core Health</span></div>
          </div>
        </button>
      </section>

      {showStatus && (
        <div className="metric-detail-backdrop" onMouseDown={event => {
          if (event.target === event.currentTarget) setShowStatus(false)
        }}>
          <section className="panel metric-detail-dialog" role="dialog" aria-modal="true" aria-labelledby="system-status-title">
            <div className="metric-detail-heading"><div><span className="eyebrow">LIVE SYSTEM DETAILS</span><h2 id="system-status-title">System Status</h2><p>Sentinel Core and monitored systems at a glance.</p></div><button className="icon-button" aria-label="Close system status" onClick={() => setShowStatus(false)}>×</button></div>
            <div className="metric-detail-content">
              <article className="metric-detail-row"><div><strong>Sentinel Core</strong><small>Version {health.version} · Uptime {health.uptime} · Queue depth {health.queueDepth}</small></div><span className={'health-chip ' + health.status}>{health.status}</span></article>
              <article className="metric-detail-row"><div><strong>Core resource use</strong><small>CPU {health.cpu}% · Memory {health.memory}%</small></div><span>{health.status}</span></article>
              <article className="metric-detail-row"><div><strong>Monitored assets</strong><small>{onlineCount} online · {assets.length - onlineCount} unreachable · {healthyCount} healthy</small></div><span>{assets.length} total</span></article>
              {assets.slice(0, 8).map(asset => (
                <article className="metric-detail-row" key={asset.id}>
                  <div><strong>{asset.display_name}</strong><small>{String(asset.metadata.monitoring_mode ?? (asset.metadata.credential_id ? 'SSH' : asset.metadata.health_note === 'Live local host check' ? 'Local' : 'TCP')).toUpperCase()} · Checked {asset.metadata.last_checked_at ? new Date(String(asset.metadata.last_checked_at)).toLocaleString() : 'not yet'}</small></div>
                  <span className={'health-chip ' + asset.health}>{asset.health}</span>
                </article>
              ))}
            </div>
            <div className="metric-detail-actions"><button className="secondary-button" onClick={() => { setShowStatus(false); onNavigate('entities') }}>View monitored systems<ArrowUpRight size={15} /></button><button className="secondary-button" onClick={() => setShowStatus(false)}>Close</button></div>
          </section>
        </div>
      )}
      {selectedAlert && <AlertDetailsDialog alert={selectedAlert} onClose={() => setSelectedAlert(null)} onOpenAlerts={() => { setSelectedAlert(null); onNavigate('alerts') }} />}
    </>
  )
}
