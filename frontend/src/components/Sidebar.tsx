import { Activity, Bell, Boxes, Cable, Gauge, Network, ScrollText, Settings, Mail, ShieldCheck, SlidersHorizontal, Puzzle } from 'lucide-react'
import type { PageKey, SystemHealth } from '../types'

const nav = [
  { key: 'overview', label: 'Overview', icon: Gauge },
  { key: 'observations', label: 'Observations', icon: Activity },
  { key: 'graph', label: 'Graph', icon: Network },
  { key: 'entities', label: 'Entities', icon: Boxes },
  { key: 'connectors', label: 'Connectors', icon: Cable },
  { key: 'rules', label: 'Rules', icon: SlidersHorizontal },
  { key: 'alerts', label: 'Alerts', icon: Bell },
  { key: 'notifications', label: 'Notifications', icon: Mail },
  { key: 'reports', label: 'Reports', icon: ScrollText },
  { key: 'plugins', label: 'Plugins', icon: Puzzle },
  { key: 'settings', label: 'Settings', icon: Settings },
] as const

export function Sidebar({ page, onNavigate, health, alertCount }: {
  page: PageKey
  onNavigate: (page: PageKey) => void
  health: SystemHealth
  alertCount: number
}) {
  return <aside className="sidebar">
    <div className="brand"><div className="brand-mark"><ShieldCheck size={28}/></div><div><strong>SENTINEL</strong><span>Observe. Understand. Protect.</span></div></div>
    <nav className="nav">{nav.map(({key,label,icon:Icon})=><button onClick={()=>onNavigate(key)} className={'nav-item ' + (page===key?'active':'')} key={key}><Icon size={18}/><span>{label}</span>{key==='alerts' && alertCount>0 ? <b className="nav-badge">{alertCount}</b> : null}</button>)}</nav>
    <div className="core-card"><div className="core-card-head"><span>SENTINEL CORE</span><span className={'health-chip ' + health.status}>{health.status}</span></div><div className="core-stat"><span>CPU</span><b>{health.cpu}%</b></div><div className="sparkline"><i/><i/><i/><i/><i/><i/><i/></div><div className="core-stat"><span>Memory</span><b>{health.memory}%</b></div><div className="core-stat"><span>Event Queue</span><b>{health.queueDepth}</b></div><div className="core-stat"><span>Uptime</span><b>{health.uptime}</b></div></div>
  </aside>
}
