import { useEffect, useState } from 'react'
import { Check, ChevronLeft, ChevronRight, CircleCheck, RotateCcw, Search } from 'lucide-react'
import type { AlertRecord } from '../types'
import type { SentinelSettings } from '../config'
import { getAlerts } from '../api/client'
import { AlertDetailsDialog } from './AlertDetailsDialog'

const PAGE_SIZE = 50

export function AlertsPage({ alerts, settings, onStatus }: { alerts: AlertRecord[]; settings: SentinelSettings; onStatus: (alert: AlertRecord, status: AlertRecord['status']) => Promise<void> }) {
  const [filter, setFilter] = useState('active')
  const [severity, setSeverity] = useState('all')
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(0)
  const [rows, setRows] = useState<AlertRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedAlert, setSelectedAlert] = useState<AlertRecord | null>(null)

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(async () => {
      setLoading(true)
      try {
        const result = await getAlerts(settings, {
          limit: PAGE_SIZE, offset: page * PAGE_SIZE,
          status: filter, severity: severity === 'all' ? undefined : severity,
          search: query.trim() || undefined,
        })
        if (active) { setRows(result); setError('') }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Could not load alerts')
      } finally {
        if (active) setLoading(false)
      }
    }, query ? 250 : 0)
    return () => { active = false; window.clearTimeout(timer) }
  }, [settings, page, filter, severity, query, alerts])

  const changeFilter = (status: string, level: string, search: string) => {
    setPage(0); setFilter(status); setSeverity(level); setQuery(search)
  }

  return <section className="functional-page">
    <div className="page-title"><div><span>Rule results</span><h1>Alerts</h1><p>Review and resolve issues matched by your rules.</p></div></div>
    <div className="panel alert-toolbar">
      <div className="search-box"><Search size={16}/><input value={query} onChange={event=>changeFilter(filter,severity,event.target.value)} placeholder="Search alerts, systems, rules..."/></div>
      <label className="inline-filter"><span>Status</span><select value={filter} onChange={event=>changeFilter(event.target.value,severity,query)}><option value="active">Active</option><option value="open">Open</option><option value="acknowledged">Acknowledged</option><option value="resolved">Resolved</option><option value="all">All</option></select></label>
      <label className="inline-filter"><span>Severity</span><select value={severity} onChange={event=>changeFilter(filter,event.target.value,query)}><option value="all">All</option><option value="critical">Critical</option><option value="error">Error</option><option value="warning">Warning</option><option value="info">Info</option></select></label>
      <span>{rows.length ? (page * PAGE_SIZE + 1) + '–' + (page * PAGE_SIZE + rows.length) : '0'} loaded</span>
    </div>
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="alert-list">{loading ? <div className="panel large-panel-empty"><strong>Loading alerts…</strong></div> : rows.length ? rows.map(alert=><article className="panel alert-card" key={alert.id}>
      <span className={'severity-mark ' + alert.severity}/><div className="alert-copy"><div className="alert-title-row"><button className="alert-detail-trigger" onClick={() => setSelectedAlert(alert)}>{alert.title}</button><span className={'alert-status ' + alert.status}>{alert.status}</span></div><p>{alert.summary}</p><small>{alert.entity ?? 'System'} · {alert.occurrence_count} occurrence{alert.occurrence_count===1?'':'s'} · First seen {new Date(alert.triggered_at).toLocaleString()} · Last seen {new Date(alert.last_seen_at).toLocaleString()} · Rule {alert.rule_id ?? 'removed'} · Observation {alert.source_observation_id}</small></div>
      <div className="alert-actions">{alert.status==='open' && <button className="secondary-button" onClick={()=>void onStatus(alert,'acknowledged')}><Check size={15}/>Acknowledge</button>}{alert.status!=='resolved' ? <button className="primary-button" onClick={()=>void onStatus(alert,'resolved')}><CircleCheck size={15}/>Resolve</button> : <button className="secondary-button" onClick={()=>void onStatus(alert,'open')}><RotateCcw size={15}/>Reopen</button>}</div>
    </article>) : <div className="panel large-panel-empty"><strong>No {filter==='active'?'active ':''}alerts match</strong><span>When an observation matches an enabled rule, Sentinel will open an alert here.</span></div>}</div>
    <div className="page-controls"><button className="secondary-button" disabled={page===0 || loading} onClick={()=>setPage(value=>Math.max(0,value-1))}><ChevronLeft size={15}/>Previous</button><span>Page {page+1}</span><button className="secondary-button" disabled={rows.length<PAGE_SIZE || loading} onClick={()=>setPage(value=>value+1)}>Next<ChevronRight size={15}/></button></div>
    {selectedAlert && <AlertDetailsDialog alert={selectedAlert} onClose={() => setSelectedAlert(null)} onOpenAlerts={() => setSelectedAlert(null)} openAlertsLabel="Back to Alerts" />}
  </section>
}
