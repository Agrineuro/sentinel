import type {
  Asset,
  Connector,
  HealthState,
  ObservationRecord,
  Relationship,
  SystemHealth,
  RuleRecord,
  AlertRecord,
  ReportSummary,
} from '../types'
import type { SentinelSettings } from '../config'

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message)
  }
}

async function request<T>(
  settings: SentinelSettings,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const base = settings.apiBaseUrl.replace(/\/$/, '')

  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(settings.apiKey ? { 'X-Sentinel-Token': settings.apiKey } : {}),
      ...(init?.headers ?? {}),
    },
  })

  if (!response.ok) {
    let message = response.status + ' ' + response.statusText
    try {
      const body = await response.json() as { detail?: unknown }
      if (typeof body.detail === 'string') message = body.detail
      else if (body.detail !== undefined) message = JSON.stringify(body.detail)
    } catch { /* keep the HTTP status when the response has no JSON body */ }
    throw new ApiError(message, response.status)
  }

  return response.json() as Promise<T>
}

function formatUptime(seconds: unknown): string {
  const value = Number(seconds)
  if (!Number.isFinite(value) || value < 0) return 'Unknown'
  const days = Math.floor(value / 86400)
  const hours = Math.floor((value % 86400) / 3600)
  const minutes = Math.floor((value % 3600) / 60)
  return days ? days + 'd ' + hours + 'h' : hours ? hours + 'h ' + minutes + 'm' : minutes + 'm'
}

function normalizeHealth(value: unknown): HealthState {
  const text = String(value ?? '').toLowerCase()

  if (['ok', 'online', 'up', 'healthy', 'connected'].includes(text)) {
    return 'healthy'
  }

  if (['warning', 'degraded', 'reconnecting'].includes(text)) {
    return 'degraded'
  }

  if (['error', 'down', 'offline', 'failed'].includes(text)) {
    return 'offline'
  }

  return 'unknown'
}

export async function getSystemHealth(
  settings: SentinelSettings,
): Promise<SystemHealth> {
  const raw = await request<Record<string, unknown>>(settings, '/health')

  return {
    authenticationRequired: Boolean(raw.authentication_required),
    status: normalizeHealth(raw.status ?? raw.health),
    cpu: Number(raw.cpu_percent ?? raw.cpu ?? 0),
    memory: Number(raw.memory_percent ?? raw.memory ?? 0),
    queueDepth: Number(raw.queue_depth ?? raw.event_queue ?? 0),
    uptime: String(raw.uptime ?? formatUptime(raw.uptime_seconds)),
    version: String(raw.version ?? '0.1.0'),
  }
}

export async function getAssets(
  settings: SentinelSettings,
): Promise<Asset[]> {
  return request<Asset[]>(settings, '/assets')
}

export async function createAsset(settings: SentinelSettings, payload: {
  asset_type: string
  display_name: string
  organization_id?: string
  state?: string
  health?: string
  metadata: Record<string, unknown>
}): Promise<Asset> {
  return request<Asset>(settings, '/assets', { method: 'POST', body: JSON.stringify(payload) })
}

export async function updateAsset(settings: SentinelSettings, id: string, patch: Partial<Asset>): Promise<Asset> {
  return request<Asset>(settings, '/assets/' + encodeURIComponent(id), { method: 'PATCH', body: JSON.stringify(patch) })
}
export async function deleteAsset(settings: SentinelSettings, id: string): Promise<void> {
  const base = settings.apiBaseUrl.replace(/\/$/, '')
  const response = await fetch(base + '/assets/' + encodeURIComponent(id), { method: 'DELETE', headers: settings.apiKey ? { 'X-Sentinel-Token': settings.apiKey } : {} })
  if (!response.ok) throw new ApiError(response.status + ' ' + response.statusText, response.status)
}

export async function getObservations(
  settings: SentinelSettings,
  options: { limit?: number; offset?: number; type?: string; severity?: string; search?: string } = {},
): Promise<ObservationRecord[]> {
  const params = new URLSearchParams({ limit: String(options.limit ?? 500), offset: String(options.offset ?? 0) })
  if (options.type) params.set('type', options.type)
  if (options.severity) params.set('severity', options.severity)
  if (options.search) params.set('search', options.search)
  const raw = await request<unknown>(settings, '/observations?' + params.toString())
  const rows = Array.isArray(raw)
    ? raw
    : (raw as { observations?: unknown[] }).observations ?? []

  return rows.map((item, index) => {
    const wrapper = item as Record<string, unknown>
    const nestedEvent =
      wrapper.event && typeof wrapper.event === 'object'
        ? (wrapper.event as Record<string, unknown>)
        : wrapper
    const data =
      nestedEvent.data && typeof nestedEvent.data === 'object'
        ? (nestedEvent.data as Record<string, unknown>)
        : {}

    return {
      id: String(nestedEvent.id ?? wrapper.id ?? 'observation-' + index),
      timestamp: String(nestedEvent.timestamp ?? wrapper.timestamp ?? new Date().toISOString()),
      type: String(nestedEvent.type ?? nestedEvent.observation_type ?? 'event'),
      severity: String(nestedEvent.severity ?? 'info'),
      summary: String(nestedEvent.summary ?? nestedEvent.message ?? 'Observation received'),
      source: String(nestedEvent.source ?? 'Sentinel'),
      entity: String(nestedEvent.entity ?? data.entity ?? data.hostname ?? data.asset_id ?? '') || undefined,
      value: nestedEvent.value,
      raw: nestedEvent.raw ?? item,
    }
  })
}

export async function getConnectors(settings: SentinelSettings): Promise<Connector[]> {
  const rows = await request<Array<Record<string, unknown>>>(settings, '/connectors')
  return rows.map(normalizeConnector)
}

export interface ConnectorCreateResult extends Connector {
  webhook_token?: string | null
}
export async function createConnector(settings: SentinelSettings, payload: {
  name: string
  connector_type: 'webhook' | 'mqtt'
  enabled: boolean
  config: Record<string, unknown>
  username?: string
  password?: string
}): Promise<ConnectorCreateResult> {
  return request<ConnectorCreateResult>(settings, '/connectors', { method: 'POST', body: JSON.stringify(payload) })
}
export async function updateConnector(settings: SentinelSettings, id: string, patch: {
  enabled?: boolean
  name?: string
  translation_field_map?: Record<string, string>
}): Promise<Connector> {
  const row = await request<Record<string, unknown>>(settings, '/connectors/' + encodeURIComponent(id), { method: 'PATCH', body: JSON.stringify(patch) })
  return normalizeConnector(row)
}
function normalizeConnector(row: Record<string, unknown>): Connector {
  const state = String(row.status ?? 'unknown')
  const status: HealthState = ['ready', 'connected', 'healthy'].includes(state) ? 'healthy'
    : ['starting', 'reconnecting', 'degraded'].includes(state) ? 'degraded'
      : ['error', 'offline', 'failed'].includes(state) ? 'offline' : 'unknown'
  const checked = row.last_checked_at ? String(row.last_checked_at) : null
  const config = row.config && typeof row.config === 'object' ? row.config as Record<string, unknown> : {}
  return {
    id: String(row.id), name: String(row.name), connector_type: String(row.connector_type),
    direction: String(row.direction), enabled: Boolean(row.enabled), state, status, config,
    credential_id: row.credential_id == null ? null : String(row.credential_id),
    last_checked_at: checked, last_error: row.last_error == null ? null : String(row.last_error),
    ingest_path: row.ingest_path == null ? null : String(row.ingest_path),
    rate: String(config.topic ?? (row.connector_type === 'webhook' ? 'Webhook receiver' : 'Waiting for messages')),
    lastSeen: checked ? new Date(checked).toLocaleString() : 'Never',
  }
}
export async function testConnector(settings: SentinelSettings, id: string): Promise<{ status: string; message: string; latency_ms?: number | null }> {
  return request(settings, '/connectors/' + encodeURIComponent(id) + '/test', { method: 'POST' })
}
export async function deleteConnector(settings: SentinelSettings, id: string): Promise<void> {
  const base = settings.apiBaseUrl.replace(/\/$/, '')
  const response = await fetch(base + '/connectors/' + encodeURIComponent(id), { method: 'DELETE', headers: settings.apiKey ? { 'X-Sentinel-Token': settings.apiKey } : {} })
  if (!response.ok) throw new ApiError(response.status + ' ' + response.statusText, response.status)
}

export async function getRules(settings: SentinelSettings): Promise<RuleRecord[]> {
  return request<RuleRecord[]>(settings, '/rules')
}
export interface RulePreview {
  scanned: number
  match_count: number
  matches: Array<{ id: string; timestamp: string; summary: string; severity: string; entity?: string | null; value?: unknown }>
}
export async function previewRule(settings: SentinelSettings, rule: Omit<RuleRecord, 'id' | 'created_at' | 'updated_at'>): Promise<RulePreview> {
  return request<RulePreview>(settings, '/rules/preview', { method: 'POST', body: JSON.stringify(rule) })
}
export async function createRule(settings: SentinelSettings, rule: Omit<RuleRecord, 'id' | 'created_at' | 'updated_at'>): Promise<RuleRecord> {
  return request<RuleRecord>(settings, '/rules', { method: 'POST', body: JSON.stringify(rule) })
}
export async function updateRule(settings: SentinelSettings, id: string, patch: Partial<RuleRecord>): Promise<RuleRecord> {
  return request<RuleRecord>(settings, '/rules/' + encodeURIComponent(id), { method: 'PATCH', body: JSON.stringify(patch) })
}
export async function deleteRule(settings: SentinelSettings, id: string): Promise<void> {
  const base = settings.apiBaseUrl.replace(/\/$/, '')
  const response = await fetch(base + '/rules/' + encodeURIComponent(id), { method: 'DELETE', headers: settings.apiKey ? { 'X-Sentinel-Token': settings.apiKey } : {} })
  if (!response.ok) throw new ApiError(response.status + ' ' + response.statusText, response.status)
}
export async function getAlerts(
  settings: SentinelSettings,
  options: { limit?: number; offset?: number; status?: string; severity?: string; search?: string } = {},
): Promise<AlertRecord[]> {
  const params = new URLSearchParams({ limit: String(options.limit ?? 500), offset: String(options.offset ?? 0) })
  if (options.status && options.status !== 'all') params.set('status', options.status)
  if (options.severity && options.severity !== 'all') params.set('severity', options.severity)
  if (options.search) params.set('search', options.search)
  return request<AlertRecord[]>(settings, '/alerts?' + params.toString())
}
export async function updateAlert(settings: SentinelSettings, id: string, status: AlertRecord['status']): Promise<AlertRecord> {
  return request<AlertRecord>(settings, '/alerts/' + encodeURIComponent(id), { method: 'PATCH', body: JSON.stringify({ status }) })
}
export async function getReportSummary(settings: SentinelSettings): Promise<ReportSummary> {
  return request<ReportSummary>(settings, '/reports/summary')
}

export async function testConnection(settings: SentinelSettings) {
  const started = performance.now()
  const health = await getSystemHealth(settings)

  return {
    health,
    latencyMs: Math.round(performance.now() - started),
  }
}

export async function refreshSystemHealth(settings: SentinelSettings) {
  return request<{ systems: unknown[] }>(settings, '/assets/refresh', {
    method: 'POST',
  })
}

export async function getRelationships(
  settings: SentinelSettings,
): Promise<Relationship[]> {
  return request<Relationship[]>(settings, '/relationships')
}

export async function createRelationship(
  settings: SentinelSettings,
  relationship: Omit<Relationship, 'id' | 'metadata'>,
): Promise<Relationship> {
  return request<Relationship>(settings, '/relationships', {
    method: 'POST',
    body: JSON.stringify(relationship),
  })
}

export async function deleteRelationship(
  settings: SentinelSettings,
  id: string,
): Promise<void> {
  const base = settings.apiBaseUrl.replace(/\/$/, '')
  const response = await fetch(base + '/relationships/' + encodeURIComponent(id), {
    method: 'DELETE',
    headers: settings.apiKey ? { 'X-Sentinel-Token': settings.apiKey } : {},
  })
  if (!response.ok) throw new ApiError(response.status + ' ' + response.statusText, response.status)
}

export async function discoverSSHAsset(
  settings: SentinelSettings,
  payload: {
    host: string
    username: string
    secret: string
    credential_type: 'ssh_password' | 'ssh_private_key'
    credential_name: string
    display_name?: string
    port: number
  },
): Promise<Asset> {
  return request<Asset>(settings, '/connectors/ssh/discover', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
