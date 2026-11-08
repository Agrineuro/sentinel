import { Activity, Bell, Boxes, Clock3 } from 'lucide-react'
import type { ReportSummary } from '../types'

function Breakdown({ title, values }: { title: string; values: Record<string, number> }) {
  const entries = Object.entries(values).sort((a,b)=>b[1]-a[1])
  return <section className="panel report-card"><h2>{title}</h2>{entries.length ? <div className="report-breakdown">{entries.map(([key,value])=><div key={key}><span>{key}</span><strong>{value}</strong></div>)}</div> : <p className="muted-copy">No data yet.</p>}</section>
}
export function ReportsPage({ report }: { report: ReportSummary | null }) {
  if (!report) return <section className="functional-page"><div className="page-title"><div><span>Operational summary</span><h1>Reports</h1><p>Observation and system health summary.</p></div></div><div className="panel large-panel-empty"><strong>Report data is not available</strong><span>Check the Sentinel Core connection and refresh.</span></div></section>
  return <section className="functional-page">
    <div className="page-title"><div><span>Operational summary</span><h1>Reports</h1><p>Observation and system health summary · generated {new Date(report.generated_at).toLocaleString()}</p></div></div>
    <div className="report-stat-grid">
      <article className="panel report-stat"><Activity/><span>Observations, 24 hours</span><strong>{report.observations_last_24h}</strong></article>
      <article className="panel report-stat"><Clock3/><span>All saved observations</span><strong>{report.observation_total}</strong></article>
      <article className="panel report-stat"><Bell/><span>Open alerts</span><strong>{report.open_alerts}</strong></article>
      <article className="panel report-stat"><Boxes/><span>Tracked systems</span><strong>{Object.values(report.assets_by_health).reduce((sum,value)=>sum+value,0)}</strong></article>
    </div>
    <div className="report-grid"><Breakdown title="Observations by type" values={report.observations_by_type}/><Breakdown title="Observations by severity" values={report.observations_by_severity}/><Breakdown title="Systems by health" values={report.assets_by_health}/></div>
  </section>
}
