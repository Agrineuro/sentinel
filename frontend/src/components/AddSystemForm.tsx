import { useState, type FormEvent } from 'react'
import { Plus, RefreshCw } from 'lucide-react'
import { createAsset, discoverSSHAsset, refreshSystemHealth } from '../api/client'
import type { SentinelSettings } from '../config'

type ConnectionMode = 'ssh' | 'http' | 'icmp'

export function AddSystemForm({ settings, onAdded }: { settings: SentinelSettings; onAdded: () => Promise<void> }) {
  const [open, setOpen] = useState(false)
  const [mode, setMode] = useState<ConnectionMode>('ssh')
  const [host, setHost] = useState('')
  const [url, setUrl] = useState('')
  const [name, setName] = useState('')
  const [username, setUsername] = useState('')
  const [port, setPort] = useState(22)
  const [credentialType, setCredentialType] = useState<'ssh_password' | 'ssh_private_key'>('ssh_password')
  const [secret, setSecret] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true); setError(null); setMessage(null)
    try {
      if (mode === 'ssh') {
        const asset = await discoverSSHAsset(settings, {
          host: host.trim(), username: username.trim(), secret, credential_type: credentialType,
          credential_name: (name.trim() || host.trim()) + ' SSH credential',
          display_name: name.trim() || undefined, port,
        })
        setSecret('')
        setMessage(asset.display_name + ' discovered and saved to your encrypted vault.')
      } else {
        const target = mode === 'http' ? url.trim() : host.trim()
        const asset = await createAsset(settings, {
          asset_type: mode === 'http' ? 'web_service' : 'network_device',
          display_name: name.trim() || target,
          metadata: mode === 'http'
            ? { monitoring_mode: 'http', health_url: target, url: target }
            : { monitoring_mode: 'icmp', ip: target, hostname: target },
        })
        await refreshSystemHealth(settings)
        setMessage(asset.display_name + ' added. Sentinel ran its first ' + (mode === 'http' ? 'HTTP' : 'ping') + ' check.')
      }
      await onAdded()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not add system')
    } finally { setBusy(false) }
  }

  const title = mode === 'ssh' ? 'Add an SSH system' : mode === 'http' ? 'Monitor a web endpoint' : 'Monitor a host with ping'
  const description = mode === 'ssh'
    ? 'Discover a Linux host and save its credential encrypted in Sentinel.'
    : mode === 'http'
      ? 'Check a URL for availability and response time. JSON health endpoints can also report resource metrics.'
      : 'Check whether a host responds over ICMP. Ping reports reachability, not CPU or memory metrics.'

  return (
    <section className="panel add-system-panel">
      <div className="add-system-heading">
        <div><span className="eyebrow">CONNECT A SYSTEM</span><h2>{title}</h2><p>{description}</p></div>
        <button className="primary-button" onClick={() => setOpen(value => !value)}><Plus size={16} /> {open ? 'Close' : 'Add system'}</button>
      </div>
      {open && <form className="system-discovery-form" onSubmit={submit}>
        <label><span>Connection method</span><select value={mode} onChange={event => setMode(event.target.value as ConnectionMode)}><option value="ssh">SSH host metrics</option><option value="http">HTTP / HTTPS endpoint</option><option value="icmp">Ping host reachability</option></select></label>
        <label><span>System name</span><input value={name} onChange={event => setName(event.target.value)} placeholder={mode === 'http' ? 'Home Assistant' : 'Utility server'} /></label>
        {mode === 'http'
          ? <label className="wide-field"><span>Health URL</span><input required type="url" value={url} onChange={event => setUrl(event.target.value)} placeholder="https://service.example/health" /></label>
          : <label><span>Host or IP address</span><input required value={host} onChange={event => setHost(event.target.value)} placeholder="192.168.1.50" /></label>}
        {mode === 'ssh' && <>
          <label><span>SSH port</span><input required type="number" min="1" max="65535" value={port} onChange={event => setPort(Number(event.target.value))} /></label>
          <label><span>Username</span><input required value={username} onChange={event => setUsername(event.target.value)} placeholder="scott" /></label>
          <label><span>Authentication</span><select value={credentialType} onChange={event => setCredentialType(event.target.value as 'ssh_password' | 'ssh_private_key')}><option value="ssh_password">Password</option><option value="ssh_private_key">Private key</option></select></label>
          {credentialType === 'ssh_password'
            ? <label className="secret-field"><span>SSH password</span><input required type="password" autoComplete="new-password" value={secret} onChange={event => setSecret(event.target.value)} /></label>
            : <label className="secret-field"><span>Private key</span><textarea required rows={5} autoComplete="off" value={secret} onChange={event => setSecret(event.target.value)} placeholder="Paste the private key. Sentinel encrypts it after successful discovery." /></label>}
        </>}
        <div className="form-actions">
          <button className="primary-button" disabled={busy || (mode === 'ssh' && !secret)}>{busy ? <><RefreshCw size={15} className="spin" /> Adding…</> : mode === 'ssh' ? 'Discover and add' : 'Add and check now'}</button>
          {message && <span className="form-success">{message}</span>}{error && <span className="form-error">{error}</span>}
        </div>
      </form>}
    </section>
  )
}
