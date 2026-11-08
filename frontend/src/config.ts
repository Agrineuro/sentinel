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

export const defaultSettings: SentinelSettings = {
  apiBaseUrl: 'http://localhost:18101/api/v1',
  apiKey: '',
  websocketUrl: 'ws://localhost:18101/api/v1/events/ws',
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
    if (settings.apiBaseUrl === 'http://192.168.1.192:18101/api/v1') {
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
