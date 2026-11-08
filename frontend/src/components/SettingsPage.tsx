import { useState } from 'react'
import {
  CheckCircle2,
  RefreshCw,
  Save,
  Server,
  Wifi,
  XCircle,
} from 'lucide-react'

import { testConnection } from '../api/client'
import type { SentinelSettings } from '../config'
import { AccountManagementPanel } from './AccountManagementPanel'

interface Props {
  settings: SentinelSettings
  onSave: (settings: SentinelSettings) => void
}

export function SettingsPage({ settings, onSave }: Props) {
  const [draft, setDraft] = useState<SentinelSettings>(settings)
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<{
    ok: boolean
    message: string
  } | null>(null)

  const test = async () => {
    setTesting(true)
    setResult(null)

    try {
      const response = await testConnection(draft)

      setResult({
        ok: true,
        message: 'Connected in ' + response.latencyMs + ' ms - ' + response.health.status + ' - account sign-in is enabled',
      })
    } catch (error) {
      setResult({
        ok: false,
        message:
          error instanceof Error
            ? error.message
            : 'Connection failed',
      })
    } finally {
      setTesting(false)
    }
  }

  const save = () => {
    onSave(draft)

    setResult({
      ok: true,
      message: 'Settings saved',
    })
  }

  return (
    <section className="settings-page">
      <div className="page-title">
        <div>
          <span>Configuration</span>
          <h1>Sentinel Settings</h1>
          <p>
            Connect the dashboard to Sentinel Core and configure frontend
            behavior.
          </p>
        </div>
      </div>

      <div className="settings-grid">
        <AccountManagementPanel />
        <section className="panel settings-card">
          <div className="settings-card-title">
            <Server size={19} />

            <div>
              <h2>Backend connection</h2>
              <p>
                REST and WebSocket endpoints used by the Sentinel dashboard.
              </p>
            </div>
          </div>

          <label>
            <span>API base URL</span>

            <input
              value={draft.apiBaseUrl}
              onChange={(event) =>
                setDraft({
                  ...draft,
                  apiBaseUrl: event.target.value,
                })
              }
              placeholder="http://192.168.1.192:18101/api/v1"
            />
          </label>


          <label>
            <span>WebSocket URL</span>

            <input
              value={draft.websocketUrl}
              onChange={(event) =>
                setDraft({
                  ...draft,
                  websocketUrl: event.target.value,
                })
              }
              placeholder="ws://192.168.1.192:18101/api/v1/events/ws"
            />
          </label>

          <label>
            <span>Reconnect interval</span>

            <div className="number-field">
              <input
                type="number"
                min="1"
                max="60"
                value={draft.reconnectSeconds}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    reconnectSeconds: Number(event.target.value),
                  })
                }
              />

              <b>seconds</b>
            </div>
          </label>

          <div className="settings-actions">
            <button
              className="secondary-button"
              onClick={test}
              disabled={testing}
            >
              <RefreshCw
                size={15}
                className={testing ? 'spin' : ''}
              />

              {testing ? 'Testing...' : 'Test connection'}
            </button>

            <button
              className="primary-button"
              onClick={save}
            >
              <Save size={15} />
              Save settings
            </button>
          </div>

          {result && (
            <div
              className={`test-result ${
                result.ok ? 'ok' : 'bad'
              }`}
            >
              {result.ok ? (
                <CheckCircle2 size={16} />
              ) : (
                <XCircle size={16} />
              )}

              {result.message}
            </div>
          )}
        </section>

        <section className="panel settings-card">
          <div className="settings-card-title">
            <Wifi size={19} />

            <div>
              <h2>Dashboard behavior</h2>
              <p>
                Choose how the dashboard behaves during development and normal
                operation.
              </p>
            </div>
          </div>

          <Toggle
            label="Use cached snapshot"
            description="Keep the last successful dashboard snapshot visible if Core is unavailable."
            checked={draft.useMockFallback}
            onChange={(value) =>
              setDraft({
                ...draft,
                useMockFallback: value,
              })
            }
          />

          <Toggle
            label="Animate graph flow"
            description="Animate active graph edges and observation paths."
            checked={draft.graphAnimation}
            onChange={(value) =>
              setDraft({
                ...draft,
                graphAnimation: value,
              })
            }
          />

          <Toggle
            label="Compact dashboard"
            description="Reduce panel spacing for smaller displays."
            checked={draft.compactMode}
            onChange={(value) =>
              setDraft({
                ...draft,
                compactMode: value,
              })
            }
          />
        </section>
      </div>
    </section>
  )
}

function Toggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string
  description: string
  checked: boolean
  onChange: (value: boolean) => void
}) {
  return (
    <button
      type="button"
      className="toggle-row"
      onClick={() => onChange(!checked)}
    >
      <span>
        <strong>{label}</strong>
        <small>{description}</small>
      </span>

      <i className={checked ? 'on' : ''}>
        <b />
      </i>
    </button>
  )
}
