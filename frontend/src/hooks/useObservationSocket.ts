import { useEffect, useRef, useState } from 'react'
import type { SentinelSettings } from '../config'
import type { ObservationRecord } from '../types'

export function useObservationSocket(settings: SentinelSettings, onObservation: (observation: ObservationRecord) => void) {
  const [connected, setConnected] = useState(false)
  const [lastEventAt, setLastEventAt] = useState<string | null>(null)
  const callbackRef = useRef(onObservation)
  callbackRef.current = onObservation

  useEffect(() => {
    let socket: WebSocket | null = null
    let reconnectTimer: number | null = null
    let stopped = false

    const connect = () => {
      if (stopped || !settings.websocketUrl) return
      socket = new WebSocket(settings.websocketUrl, ['sentinel'])
      socket.onopen = () => setConnected(true)
      socket.onclose = () => {
        setConnected(false)
        if (!stopped) reconnectTimer = window.setTimeout(connect, settings.reconnectSeconds * 1000)
      }
      socket.onerror = () => socket?.close()
      socket.onmessage = (event) => {
        try {
          const row = JSON.parse(event.data) as Record<string, unknown>
          const observation: ObservationRecord = {
            id: String(row.id ?? row.observation_id ?? crypto.randomUUID()),
            timestamp: String(row.timestamp ?? row.created_at ?? new Date().toISOString()),
            type: String(row.type ?? row.observation_type ?? 'system.event'),
            severity: String(row.severity ?? 'info'),
            summary: String(row.summary ?? row.message ?? 'Observation received'),
            source: String(row.source ?? row.connector ?? 'Sentinel'),
            entity: row.entity ? String(row.entity) : undefined,
            raw: row,
          }
          callbackRef.current(observation)
          setLastEventAt(observation.timestamp)
        } catch { /* ignore malformed events */ }
      }
    }

    connect()
    return () => {
      stopped = true
      if (reconnectTimer) window.clearTimeout(reconnectTimer)
      socket?.close()
    }
  }, [settings.websocketUrl, settings.reconnectSeconds])

  return { connected, lastEventAt }
}
