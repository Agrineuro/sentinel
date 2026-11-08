import { useCallback, useEffect, useState } from 'react'
import {
  getAssets,
  getConnectors,
  getRules,
  getAlerts,
  getReportSummary,
  getObservations,
  getRelationships,
  getSystemHealth,
  refreshSystemHealth,
} from '../api/client'
import type { SentinelSettings } from '../config'
import type {
  Asset,
  Connector,
  ObservationRecord,
  SystemHealth,
  RuleRecord,
  AlertRecord,
  ReportSummary,
} from '../types'

const emptyHealth: SystemHealth = {
  status: 'unknown',
  cpu: 0,
  memory: 0,
  queueDepth: 0,
  uptime: 'Unknown',
  version: 'development',
}

export function useSentinelData(settings: SentinelSettings) {
  const [health, setHealth] = useState<SystemHealth>(emptyHealth)
  const [assets, setAssets] = useState<Asset[]>([])
  const [observations, setObservations] = useState<ObservationRecord[]>([])
  const [connectors, setConnectors] = useState<Connector[]>([])
  const [relationships, setRelationships] = useState<import("../types").Relationship[]>([])
  const [rules, setRules] = useState<RuleRecord[]>([])
  const [alerts, setAlerts] = useState<AlertRecord[]>([])
  const [report, setReport] = useState<ReportSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [usingFallback, setUsingFallback] = useState(false)

  const refresh = useCallback(async (checkSystems = false) => {
    setLoading(true)

    try {
      if (checkSystems) await refreshSystemHealth(settings)
      const [
        nextHealth,
        nextAssets,
        nextObservations,
        nextConnectors,
        nextRelationships,
        nextRules,
        nextAlerts,
        nextReport,
      ] = await Promise.all([
        getSystemHealth(settings),
        getAssets(settings),
        getObservations(settings).catch(() => []),
        getConnectors(settings),
        getRelationships(settings),
        getRules(settings),
        getAlerts(settings),
        getReportSummary(settings),
      ])

      setHealth(nextHealth)
      setAssets(nextAssets)
      setObservations(nextObservations)
      setConnectors(nextConnectors)
      setRelationships(nextRelationships)
      setRules(nextRules)
      setAlerts(nextAlerts)
      setReport(nextReport)
      try {
        if (settings.useMockFallback) {
          localStorage.setItem('sentinel.dashboard.cache.v1', JSON.stringify({
            health: nextHealth, assets: nextAssets, observations: nextObservations,
            connectors: nextConnectors, relationships: nextRelationships,
            rules: nextRules, alerts: nextAlerts, report: nextReport,
          }))
        } else {
          localStorage.removeItem('sentinel.dashboard.cache.v1')
        }
      } catch { /* snapshot cache is optional */ }
      setError(null)
      setUsingFallback(false)
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Backend request failed'

      let restored = false
      if (settings.useMockFallback) {
        try {
          const cached = JSON.parse(localStorage.getItem('sentinel.dashboard.cache.v1') || 'null')
          if (cached?.health && Array.isArray(cached.assets)) {
            setHealth(cached.health)
            setAssets(cached.assets)
            setObservations(Array.isArray(cached.observations) ? cached.observations : [])
            setConnectors(Array.isArray(cached.connectors) ? cached.connectors : [])
            setRelationships(Array.isArray(cached.relationships) ? cached.relationships : [])
            setRules(Array.isArray(cached.rules) ? cached.rules : [])
            setAlerts(Array.isArray(cached.alerts) ? cached.alerts : [])
            setReport(cached.report ?? null)
            restored = true
          }
        } catch { /* ignore an invalid saved snapshot */ }
      }
      setError(message)
      setUsingFallback(restored)
    } finally {
      setLoading(false)
    }
  }, [settings])

  useEffect(() => {
    void refresh(true)
  }, [refresh])

  useEffect(() => {
    const timer = window.setInterval(() => {
      void refresh()
    }, 30_000)

    return () => window.clearInterval(timer)
  }, [refresh])

  return {
    health,
    assets,
    observations,
    connectors,
    relationships,
    rules,
    alerts,
    report,
    loading,
    error,
    usingFallback,
    refresh,
    setObservations,
  }
}
