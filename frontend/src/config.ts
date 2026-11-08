export type ThemeMode = 'dark' | 'light'

export interface SentinelSettings {
  apiBaseUrl: string
  apiKey: string
  websocketUrl: string
  useMockFallback: boolean
  reconnectSeconds: number
  graphAnimation: boolean
  compactMode: boolean
  theme: ThemeMode
  displayName: string
  roleName: string
}

function getDefaultApiBaseUrl(): string {
  if (import.meta.env.PROD && typeof window !== 'undefined') {
    return window.location.origin + '/api/v1'
  }
  return 'http://localhost:18101/api/v1'
}

function getDefaultWebsocketUrl(): string {
  if (import.meta.env.PROD && typeof window !== 'undefined') {
    const scheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return scheme + '//' + window.location.host + '/api/v1/events/ws'
  }
  return 'ws://localhost:18101/api/v1/events/ws'
}

export const defaultSettings: SentinelSettings = {
  apiBaseUrl: getDefaultApiBaseUrl(),
  apiKey: '',
  websocketUrl: getDefaultWebsocketUrl(),
  useMockFallback: false,
  reconnectSeconds: 5,
  graphAnimation: true,
  compactMode: false,
  theme: 'dark',
  displayName: 'Administrator',
  roleName: 'Administrator',
}

const STORAGE_KEY = 'sentinel.settings.v1'

export function loadSettings(): SentinelSettings {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)

    if (!saved) return defaultSettings
    const settings = { ...defaultSettings, ...JSON.parse(saved) }
    const previousDevelopmentUrls = new Set([
      'http://localhost:18101/api/v1',
      'http://127.0.0.1:18101/api/v1',
      'http://192.168.1.192:18101/api/v1',
    ])
    if (previousDevelopmentUrls.has(settings.apiBaseUrl)) {
      settings.apiBaseUrl = defaultSettings.apiBaseUrl
      settings.websocketUrl = defaultSettings.websocketUrl
    }
    return settings
  } catch {
    return defaultSettings
  }
}

export function saveSettings(settings: SentinelSettings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
}
