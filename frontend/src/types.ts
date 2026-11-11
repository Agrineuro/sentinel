import type { LucideIcon } from 'lucide-react'
export type HealthState = 'healthy' | 'degraded' | 'offline' | 'unknown'
export type PageKey = 'overview' | 'observations' | 'graph' | 'entities' | 'connectors' | 'rules' | 'alerts' | 'reports' | 'plugins' | 'notifications' | 'settings'
export interface Metric { label:string; value:string; detail:string; tone:'blue'|'green'|'amber'|'red'; icon:LucideIcon }
export interface Observation { time:string; title:string; source:string; category:string; tone:'blue'|'green'|'amber'|'red'; icon:LucideIcon }
export interface ObservationRecord { id:string; timestamp:string; type:string; severity:string; summary:string; source:string; entity?:string; value?:unknown; raw?:unknown }
export interface Connector {
  id?: string
  name: string
  status: HealthState
  rate: string
  lastSeen: string
  connector_type?: 'webhook' | 'mqtt' | 'http_poll' | 'websocket' | string
  direction?: string
  enabled?: boolean
  state?: string
  config?: Record<string, unknown>
  credential_id?: string | null
  last_checked_at?: string | null
  last_error?: string | null
  ingest_path?: string | null
}
export interface SystemHealth { authenticationRequired?:boolean; status:HealthState; cpu:number; memory:number; queueDepth:number; uptime:string; version:string }
export interface Asset {
  id: string
  asset_type: string
  display_name: string
  organization_id: string
  site_id?: string | null
  state: string
  health: HealthState
  metadata: Record<string, unknown>
}

export interface Relationship {
  id: string
  source_asset_id: string
  target_asset_id: string
  relationship_type: string
  metadata: Record<string, unknown>
}

export interface RuleRecord {
  id: string
  name: string
  description: string
  observation_type: string
  minimum_severity: string
  source_contains?: string | null
  entity_contains?: string | null
  summary_contains?: string | null
  condition_field?: string | null
  condition_operator?: 'gt' | 'gte' | 'lt' | 'lte' | null
  condition_value?: number | null
  enabled: boolean
  created_at: string
  updated_at: string
}
export interface AlertRecord {
  id: string
  rule_id?: string | null
  source_observation_id: string
  title: string
  summary: string
  severity: string
  entity_id?: string | null
  entity?: string | null
  status: 'open' | 'acknowledged' | 'resolved'
  occurrence_count: number
  triggered_at: string
  last_seen_at: string
  acknowledged_at?: string | null
  resolved_at?: string | null
}
export interface ReportSummary {
  generated_at: string
  window_hours: number
  observation_total: number
  observations_last_24h: number
  observations_by_type: Record<string, number>
  observations_by_severity: Record<string, number>
  assets_by_health: Record<string, number>
  open_alerts: number
  acknowledged_alerts: number
  latest_observation_at?: string | null
}
