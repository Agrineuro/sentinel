import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, Search } from 'lucide-react'
import type { ObservationRecord } from '../types'
import type { SentinelSettings } from '../config'
import { getObservations } from '../api/client'

const PAGE_SIZE = 50

export function ObservationsPage({ observations, settings }: { observations: ObservationRecord[]; settings: SentinelSettings }) {
  const [query, setQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [severityFilter, setSeverityFilter] = useState('all')
  const [page, setPage] = useState(0)
  const [rows, setRows] = useState<ObservationRecord[]>([])
  const [selected, setSelected] = useState<ObservationRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(async () => {
      setLoading(true)
      try {
        const result = await getObservations(settings, {
          limit: PAGE_SIZE, offset: page * PAGE_SIZE,
          type: typeFilter === 'all' ? undefined : typeFilter,
          severity: severityFilter === 'all' ? undefined : severityFilter,
          search: query.trim() || undefined,
        })
        if (active) { setRows(result); setError('') }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Could not load observations')
      } finally {
        if (active) setLoading(false)
      }
    }, query ? 250 : 0)
    return () => { active = false; window.clearTimeout(timer) }
  }, [settings, page, typeFilter, severityFilter, query, observations[0]?.id])

  useEffect(() => {
    setSelected(current => rows.find(row => row.id === current?.id) ?? rows[0] ?? null)
  }, [rows])

  const changeFilter = (type: string, severity: string, search: string) => {
    setPage(0)
    setTypeFilter(type)
    setSeverityFilter(severity)
    setQuery(search)
  }

  return <section className="observations-page">
    <div className="page-title"><div><span>Event intelligence</span><h1>Observations</h1><p>Browse saved events by source, type, system, or severity.</p></div></div>
    <div className="observation-toolbar panel">
      <div className="search-box observation-search"><Search size={16}/><input value={query} onChange={event=>changeFilter(typeFilter,severityFilter,event.target.value)} placeholder="Search observations..."/></div>
      <label className="inline-filter"><span>Type</span><select value={typeFilter} onChange={event=>changeFilter(event.target.value,severityFilter,query)}><option value="all">All</option>{Array.from(new Set(observations.map(row=>row.type))).sort().map(type=><option key={type} value={type}>{type}</option>)}</select></label>
      <label className="inline-filter"><span>Severity</span><select value={severityFilter} onChange={event=>changeFilter(typeFilter,event.target.value,query)}><option value="all">All</option>{Array.from(new Set(observations.map(row=>row.severity))).sort().map(severity=><option key={severity} value={severity}>{severity}</option>)}</select></label>
      <span>{rows.length ? (page * PAGE_SIZE + 1) + '–' + (page * PAGE_SIZE + rows.length) : '0'} loaded</span>
    </div>
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="observation-workspace">
      <section className="panel observation-table">
        {loading ? <p className="muted-copy">Loading observations…</p> : rows.length ? rows.map(row => <button className={'observation-table-row ' + (selected?.id===row.id?'selected':'')} key={row.id} onClick={()=>setSelected(row)}><time>{new Date(row.timestamp).toLocaleTimeString()}</time><div><strong>{row.summary}</strong><span>{row.source}{row.entity ? ' · ' + row.entity : ''}</span></div><b>{row.type}</b></button>) : <p className="muted-copy">No observations match these filters.</p>}
        <div className="page-controls"><button className="secondary-button" disabled={page===0 || loading} onClick={()=>setPage(value=>Math.max(0,value-1))}><ChevronLeft size={15}/>Previous</button><span>Page {page+1}</span><button className="secondary-button" disabled={rows.length<PAGE_SIZE || loading} onClick={()=>setPage(value=>value+1)}>Next<ChevronRight size={15}/></button></div>
      </section>
      <aside className="panel observation-detail">{selected ? <><span className="detail-kicker">Selected observation</span><h2>{selected.summary}</h2><dl><dt>Timestamp</dt><dd>{new Date(selected.timestamp).toLocaleString()}</dd><dt>Source</dt><dd>{selected.source}</dd><dt>Type</dt><dd>{selected.type}</dd><dt>Severity</dt><dd>{selected.severity}</dd><dt>Entity</dt><dd>{selected.entity ?? 'None'}</dd></dl>{selected.value !== undefined && <><h3>Observed value</h3><pre>{JSON.stringify(selected.value, null, 2)}</pre></>}<h3>Raw event</h3><pre>{JSON.stringify(selected.raw ?? selected, null, 2)}</pre></> : <p>No observation selected.</p>}</aside>
    </div>
  </section>
}
