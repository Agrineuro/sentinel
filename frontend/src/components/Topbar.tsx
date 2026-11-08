import { useMemo, useState } from 'react'
import {
  Activity,
  Bell,
  Server,
  Moon,
  Search,
  Settings,
  Sun,
  LogOut,
} from 'lucide-react'

import type { SentinelSettings } from '../config'
import type { SentinelUser } from '../api/auth'
import type { Asset, ObservationRecord, PageKey, SystemHealth } from '../types'

interface TopbarProps {
  health: SystemHealth
  assetCount: number
  alertCount: number
  settings: SentinelSettings
  user: SentinelUser
  onLogout: () => void
  assets: Asset[]
  observations: ObservationRecord[]
  onNavigate: (page: PageKey) => void
  onToggleTheme: () => void
}

function getInitials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean)

  if (parts.length === 0) return 'US'

  return parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

export function Topbar({
  health,
  assetCount,
  alertCount,
  settings,
  user,
  onLogout,
  assets,
  observations,
  onNavigate,
  onToggleTheme,
}: TopbarProps) {
  const healthy = health.status === 'healthy'
  const [query, setQuery] = useState('')
  const matches = useMemo(() => {
    const term = query.trim().toLowerCase()
    if (!term) return []
    const entityMatches = assets
      .filter(asset => (asset.display_name + ' ' + asset.asset_type + ' ' + String(asset.metadata.ip ?? '')).toLowerCase().includes(term))
      .slice(0, 5)
      .map(asset => ({ id: asset.id, title: asset.display_name, detail: asset.asset_type + ' · ' + String(asset.metadata.ip ?? ''), page: 'entities' as PageKey, icon: Server }))
    const observationMatches = observations
      .filter(row => (row.summary + ' ' + row.source + ' ' + row.type + ' ' + (row.entity ?? '')).toLowerCase().includes(term))
      .slice(0, 5)
      .map(row => ({ id: row.id, title: row.summary, detail: row.source + ' · ' + row.type, page: 'observations' as PageKey, icon: Activity }))
    return [...entityMatches, ...observationMatches].slice(0, 8)
  }, [query, assets, observations])

  return (
    <header className="topbar">
      <div className="global-search">
        <div className="search-box">
          <Search size={17} />
          <input
            value={query}
            onChange={event => setQuery(event.target.value)}
            onKeyDown={event => {
              if (event.key === 'Escape') setQuery('')
              if (event.key === 'Enter' && matches[0]) {
                onNavigate(matches[0].page)
                setQuery('')
              }
            }}
            placeholder="Search entities and observations..."
            aria-label="Search Sentinel"
            aria-expanded={Boolean(query.trim())}
          />
        </div>
        {query.trim() && <div className="global-search-results">
          {matches.length ? matches.map(({id,title,detail,page,icon:Icon})=><button key={id} onClick={()=>{onNavigate(page);setQuery('')}}><Icon size={15}/><span><strong>{title}</strong><small>{detail}</small></span></button>) : <div className="global-search-empty">No matching systems or observations</div>}
        </div>}
      </div>

      <div className="topbar-actions">
        <span className={`system-health ${health.status}`}>
          <i />
          {healthy ? 'System Healthy' : `System ${health.status}`}
        </span>

        <span className="systems-count">
          {assetCount} {assetCount === 1 ? 'asset' : 'assets'}
        </span>

        <button
          className="icon-button"
          onClick={() => onNavigate('alerts')}
          title="Open alerts"
          aria-label="Open alerts"
        >
          <Bell size={18} />

          {alertCount > 0 && <b>{alertCount}</b>}
        </button>

        <button
          className="icon-button"
          onClick={onToggleTheme}
          title={`Switch to ${
            settings.theme === 'dark' ? 'light' : 'dark'
          } mode`}
          aria-label="Toggle theme"
        >
          {settings.theme === 'dark' ? (
            <Sun size={18} />
          ) : (
            <Moon size={18} />
          )}
        </button>

        <button
          className="icon-button"
          onClick={() => onNavigate('settings')}
          title="Open settings"
          aria-label="Open settings"
        >
          <Settings size={18} />
        </button>

        <div
          className="profile-button"
          title="Current user"
        >
          <span className="avatar">
            {getInitials(user.display_name)}
          </span>

          <span className="profile-copy">
            <strong>{user.display_name}</strong>
            <small>{user.role}</small>
          </span>

        </div>

        <button className="icon-button" onClick={onLogout} title="Sign out" aria-label="Sign out"><LogOut size={17} /></button>
      </div>
    </header>
  )
}
