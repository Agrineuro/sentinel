import { useCallback, useMemo, useState } from 'react'
import { BottomPanels } from './components/BottomPanels'
import { EntitiesPage } from './components/EntitiesPage'
import { ConnectorsPage } from './components/ConnectorsPage'
import { RulesPage } from './components/RulesPage'
import { AlertsPage } from './components/AlertsPage'
import { ReportsPage } from './components/ReportsPage'
import { createRelationship, deleteRelationship, createRule, updateRule, deleteRule, updateAlert } from './api/client'
import { MetricCards } from './components/MetricCards'
import { ObservationsPage } from './components/ObservationsPage'
import { RightRail } from './components/RightRail'
import { SettingsPage } from './components/SettingsPage'
import { Sidebar } from './components/Sidebar'
import { SystemGraph } from './components/SystemGraph'
import { Topbar } from './components/Topbar'
import {
  loadSettings,
  saveSettings,
  type SentinelSettings,
} from './config'
import { useObservationSocket } from './hooks/useObservationSocket'
import { useAuth } from './auth/AuthProvider'
import { useSentinelData } from './hooks/useSentinelData'
import type { ObservationRecord, PageKey } from './types'

export default function App() {
  const { user, logout } = useAuth()
  const canOperate = user.role === 'admin' || user.role === 'operator'
  const [page, setPage] = useState<PageKey>('overview')
  const [settings, setSettings] = useState<SentinelSettings>(() =>
    loadSettings(),
  )

  const data = useSentinelData(settings)

  const addObservation = useCallback(
    (row: ObservationRecord) =>
      data.setObservations((current) =>
        current.some((existing) => existing.id === row.id)
          ? current
          : [row, ...current].slice(0, 250),
      ),
    [data.setObservations],
  )

  const socket = useObservationSocket(settings, addObservation)

  const alertCount = data.alerts.filter((alert) => alert.status !== 'resolved').length

  const statusText = data.usingFallback
    ? 'Cached snapshot'
    : data.error
      ? 'Refresh warning'
      : socket.connected
        ? 'WebSocket connected'
        : 'API connected'

  const refreshData = useCallback(async () => {
    await data.refresh()
  }, [data.refresh])

  const addRelationship = useCallback(async (relationship: { source_asset_id: string; target_asset_id: string; relationship_type: string }) => {
    await createRelationship(settings, relationship)
    await data.refresh()
  }, [settings, data.refresh])

  const removeRelationship = useCallback(async (id: string) => {
    await deleteRelationship(settings, id)
    await data.refresh()
  }, [settings, data.refresh])

  const addRule = useCallback(async (rule: Parameters<typeof createRule>[1]) => {
    await createRule(settings, rule)
    await data.refresh()
  }, [settings, data.refresh])

  const toggleRule = useCallback(async (rule: (typeof data.rules)[number]) => {
    await updateRule(settings, rule.id, { enabled: !rule.enabled })
    await data.refresh()
  }, [settings, data.refresh])

  const removeRule = useCallback(async (rule: (typeof data.rules)[number]) => {
    await deleteRule(settings, rule.id)
    await data.refresh()
  }, [settings, data.refresh])

  const changeAlertStatus = useCallback(async (alert: (typeof data.alerts)[number], status: (typeof data.alerts)[number]['status']) => {
    await updateAlert(settings, alert.id, status)
    await data.refresh()
  }, [settings, data.refresh])

  const save = (next: SentinelSettings) => {
    saveSettings(next)
    setSettings(next)
  }

  const content = useMemo(() => {
    if (page === 'entities') {
      return <EntitiesPage assets={data.assets} settings={settings} onAdded={refreshData} canOperate={canOperate} />
    }

    if (page === 'connectors') {
      return <ConnectorsPage connectors={data.connectors} assets={data.assets} settings={settings} onRefresh={refreshData} onNavigate={setPage} canOperate={canOperate} />
    }

    if (page === 'settings') {
      return <SettingsPage settings={settings} onSave={save} />
    }

    if (page === 'observations') {
      return <ObservationsPage observations={data.observations} settings={settings} />
    }

    if (page === 'rules') {
      return <RulesPage rules={data.rules} settings={settings} onCreate={addRule} onToggle={toggleRule} onDelete={removeRule} canOperate={canOperate} />
    }

    if (page === 'alerts') {
      return <AlertsPage alerts={data.alerts} settings={settings} onStatus={changeAlertStatus} canOperate={canOperate} />
    }

    if (page === 'reports') {
      return <ReportsPage report={data.report} />
    }

    if (page === 'graph') {
      return (
        <section className="standalone-graph">
          <SystemGraph assets={data.assets} health={data.health} relationships={data.relationships} graphAnimation={settings.graphAnimation} onCreateRelationship={addRelationship} onDeleteRelationship={removeRelationship} canEdit={canOperate} />
        </section>
      )
    }


    return (
      <>
        <MetricCards
          connectorCount={data.connectors.length}
          assetCount={data.assets.length}
          observationCount={data.observations.length}
          alertCount={alertCount}
          assets={data.assets}
          connectors={data.connectors}
          observations={data.observations}
          alerts={data.alerts}
          onNavigate={setPage}
        />

        <div className="main-grid">
          <SystemGraph assets={data.assets} health={data.health} relationships={data.relationships} graphAnimation={settings.graphAnimation} onCreateRelationship={addRelationship} onDeleteRelationship={removeRelationship} canEdit={canOperate} />

          <RightRail
            observations={data.observations}
            connectors={data.connectors}
          />
        </div>

        <BottomPanels
          observations={data.observations}
          health={data.health}
          assets={data.assets}
          alerts={data.alerts}
          onNavigate={setPage}
        />
      </>
    )
  }, [
    page,
    settings,
    canOperate,
    data.assets,
    data.connectors,
    data.health,
    data.observations,
    data.relationships,
    refreshData,
    addRelationship,
    removeRelationship,
    addRule,
    toggleRule,
    removeRule,
    changeAlertStatus,
    alertCount,
  ])

  return (
    <div
  className={`app-shell theme-${settings.theme} ${
    settings.compactMode ? 'compact-mode' : ''
  }`}
>
      <Sidebar
        page={page}
        onNavigate={setPage}
        health={data.health}
        alertCount={alertCount}
      />

      <div className="workspace">
          <Topbar
            health={data.health}
            assetCount={data.assets.length}
            alertCount={alertCount}
            settings={settings}
            user={user}
            onLogout={() => void logout()}
            assets={data.assets}
            observations={data.observations}
            onNavigate={setPage}
            onToggleTheme={() => {
              const next = {
                ...settings,
                theme: settings.theme === 'dark' ? 'light' : 'dark',
              } as SentinelSettings

              saveSettings(next)
              setSettings(next)
            }}
          />

        <main className="dashboard">
          {data.error && (
            <div className={'connection-banner ' + (data.usingFallback ? 'warning' : 'error')} role="status" aria-live="polite">
              <div className="connection-banner-copy">
                <strong>{data.usingFallback ? 'Showing cached dashboard data' : 'Dashboard data refresh failed'}</strong>
                <span>{data.error}</span>
              </div>
              <button className="secondary-button" onClick={() => void data.refresh()}>Retry</button>
            </div>
          )}

          {content}
        </main>

        <footer className="statusbar">
          <span>
            <i className={data.error ? 'warning-dot' : ''} />
            {data.loading ? 'Refreshing' : statusText}
          </span>

          <span>
            <i className={socket.connected ? '' : 'warning-dot'} />
            {socket.connected
              ? 'Live observations connected'
              : 'WebSocket not configured'}
          </span>

          <span>Assets: {data.assets.length}</span>
          <span>API: {settings.apiBaseUrl}</span>
          <span>Version: {data.health.version}</span>
        </footer>
      </div>
    </div>
  )
}
