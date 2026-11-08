import { useEffect, useState } from 'react'
import { motion } from 'motion/react'
import {
  Activity,
  ArrowUpRight,
  Boxes,
  Radio,
  ShieldAlert,
  X,
  type LucideIcon,
} from 'lucide-react'
import type { AlertRecord, Asset, Connector, ObservationRecord, PageKey } from '../types'

interface MetricCardData {
  label: 'Connectors' | 'Entities' | 'Observations' | 'Alerts'
  value: number
  detail: string
  tone: 'blue' | 'green' | 'amber' | 'red'
  icon: LucideIcon
}

export function MetricCards({
  connectorCount, assetCount, observationCount, alertCount,
  assets, connectors, observations, alerts, onNavigate,
}: {
  connectorCount: number
  assetCount: number
  observationCount: number
  alertCount: number
  assets: Asset[]
  connectors: Connector[]
  observations: ObservationRecord[]
  alerts: AlertRecord[]
  onNavigate: (page: PageKey) => void
}) {
  const [selected, setSelected] = useState<MetricCardData['label'] | null>(null)
  const metrics: MetricCardData[] = [
    { label: 'Connectors', value: connectorCount, detail: connectorCount === 0 ? 'None configured' : 'Configured', tone: 'amber', icon: Radio },
    { label: 'Entities', value: assetCount, detail: assetCount === 0 ? 'None discovered' : 'Discovered assets', tone: 'blue', icon: Boxes },
    { label: 'Observations', value: observationCount, detail: observationCount === 0 ? 'No events recorded' : 'Recorded events', tone: 'blue', icon: Activity },
    { label: 'Alerts', value: alertCount, detail: alertCount === 0 ? 'No active alerts' : 'Needs attention', tone: alertCount === 0 ? 'green' : 'red', icon: ShieldAlert },
  ]

  useEffect(() => {
    if (!selected) return
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === 'Escape') setSelected(null) }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [selected])

  const selectedMetric = metrics.find(metric => metric.label === selected)
  const destination: Record<MetricCardData['label'], { page: PageKey; label: string }> = {
    Connectors: { page: 'entities', label: 'Open Entities' },
    Entities: { page: 'entities', label: 'View all entities' },
    Observations: { page: 'observations', label: 'View observations' },
    Alerts: { page: 'alerts', label: 'View alerts' },
  }
  const activeAlerts = alerts.filter(alert => alert.status !== 'resolved')
  const severityCounts = activeAlerts.reduce<Record<string, number>>((counts, alert) => {
    counts[alert.severity] = (counts[alert.severity] ?? 0) + 1
    return counts
  }, {})

  return (
    <>
      <section className="metric-grid" aria-label="Overview information">
        {metrics.map(({ label, value, detail, tone, icon: Icon }, index) => (
          <motion.button
            type="button"
            className={'panel metric-card tone-' + tone}
            key={label}
            aria-label={'Open ' + label + ' details'}
            aria-haspopup="dialog"
            onClick={() => setSelected(label)}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.06 }}
          >
            <div><span className="eyebrow">{label}</span><strong>{value}</strong><small>{detail}</small></div>
            <div className="metric-visual"><Icon size={32} /><ArrowUpRight size={16} /></div>
          </motion.button>
        ))}
      </section>

      {selectedMetric && (
        <div className="metric-detail-backdrop" onMouseDown={event => {
          if (event.target === event.currentTarget) setSelected(null)
        }}>
          <section className="panel metric-detail-dialog" role="dialog" aria-modal="true" aria-labelledby="metric-detail-title">
            <div className="metric-detail-heading">
              <div><span className="eyebrow">OVERVIEW DETAILS</span><h2 id="metric-detail-title">{selectedMetric.label}</h2><p>{selectedMetric.value} {selectedMetric.label.toLowerCase()} · {selectedMetric.detail}</p></div>
              <button className="icon-button" aria-label="Close details" onClick={() => setSelected(null)}><X size={18} /></button>
            </div>
            <div className="metric-detail-content">
              {selectedMetric.label === 'Connectors' && (
                connectors.length ? connectors.map(connector => (
                  <article className="metric-detail-row" key={connector.name}>
                    <div><strong>{connector.name}</strong><small>{connector.rate} · Last seen {connector.lastSeen}</small></div>
                    <span className={'health-chip ' + connector.status}>{connector.status}</span>
                  </article>
                )) : <div className="metric-detail-empty"><strong>No connector registry entries yet</strong><p>System connections can be added from Entities. Sentinel currently supports SSH metrics, HTTP/HTTPS checks, and ping reachability.</p></div>
              )}
              {selectedMetric.label === 'Entities' && (
                assets.length ? assets.slice(0, 8).map(asset => {
                  const connection = String(asset.metadata.monitoring_mode ?? (asset.metadata.credential_id ? 'SSH' : asset.metadata.health_note === 'Live local host check' ? 'Local' : 'TCP'))
                  const metricParts = [
                    asset.metadata.cpu_percent == null ? null : 'CPU ' + asset.metadata.cpu_percent + '%',
                    asset.metadata.memory_used_percent == null ? null : 'Memory ' + asset.metadata.memory_used_percent + '%',
                    asset.metadata.response_time_ms == null ? null : 'Response ' + asset.metadata.response_time_ms + ' ms',
                  ].filter(Boolean).join(' · ')
                  return (
                    <article className="metric-detail-row" key={asset.id}>
                      <div><strong>{asset.display_name}</strong><small>{connection.toUpperCase()} · {asset.state}{metricParts ? ' · ' + metricParts : ''}</small></div>
                      <span className={'health-chip ' + asset.health}>{asset.health}</span>
                    </article>
                  )
                }) : <div className="metric-detail-empty"><strong>No entities registered</strong><p>Add a monitored system to start seeing its health here.</p></div>
              )}
              {selectedMetric.label === 'Observations' && (
                observations.length ? observations.slice(0, 8).map(observation => (
                  <article className="metric-detail-row observation-detail-row" key={observation.id}>
                    <div><strong>{observation.summary}</strong><small>{new Date(observation.timestamp).toLocaleString()} · {observation.source}{observation.entity ? ' · ' + observation.entity : ''}</small></div>
                    <span className={'severity-label ' + observation.severity}>{observation.severity}</span>
                  </article>
                )) : <div className="metric-detail-empty"><strong>No observations recorded</strong><p>New health checks and incoming events will appear here.</p></div>
              )}
              {selectedMetric.label === 'Alerts' && (
                activeAlerts.length ? <>
                  <div className="metric-alert-summary">{Object.entries(severityCounts).map(([severity, count]) => <span key={severity}>{severity}: <strong>{count}</strong></span>)}</div>
                  {activeAlerts.slice(0, 8).map(alert => (
                    <article className="metric-detail-row observation-detail-row" key={alert.id}>
                      <div><strong>{alert.title}</strong><small>{alert.entity ?? 'System'} · {alert.status} · Last seen {new Date(alert.last_seen_at).toLocaleString()}</small></div>
                      <span className={'severity-label ' + alert.severity}>{alert.severity}</span>
                    </article>
                  ))}
                </> : <div className="metric-detail-empty"><strong>No active alerts</strong><p>When a rule detects an issue, the alert and its severity will appear here.</p></div>
              )}
            </div>
            <div className="metric-detail-actions">
              <button className="secondary-button" onClick={() => { setSelected(null); onNavigate(destination[selectedMetric.label].page) }}>{destination[selectedMetric.label].label}<ArrowUpRight size={15} /></button>
              <button className="secondary-button" onClick={() => setSelected(null)}>Close</button>
            </div>
          </section>
        </div>
      )}
    </>
  )
}
