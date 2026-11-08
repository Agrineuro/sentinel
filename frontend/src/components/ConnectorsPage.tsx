import { useState, type FormEvent } from 'react'
import { Cable, Check, Copy, Plus, RefreshCw, Trash2, ToggleLeft, ToggleRight } from 'lucide-react'
import type { Asset, Connector } from '../types'
import { AddSystemForm } from './AddSystemForm'
import type { SentinelSettings } from '../config'
import { createConnector, deleteConnector, testConnector, updateConnector } from '../api/client'

type ConnectorKind = 'webhook' | 'mqtt'

export function ConnectorsPage({ connectors, assets, settings, onRefresh, onNavigate }: {
  connectors: Connector[]
  assets: Asset[]
  settings: SentinelSettings
  onRefresh: () => Promise<void>
  onNavigate: (page: 'entities') => void
}) {
  const [kind, setKind] = useState<ConnectorKind>('webhook')
  const [busy, setBusy] = useState(false)
  const [workingId, setWorkingId] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [webhookToken, setWebhookToken] = useState('')
  const [copied, setCopied] = useState(false)

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const formElement = event.currentTarget
    const form = new FormData(formElement)
    setBusy(true); setError(''); setNotice(''); setWebhookToken('')
    try {
      const name = String(form.get('name') || '').trim()
      const config = kind === 'webhook' ? {} : {
        host: String(form.get('host') || '').trim(),
        port: Number(form.get('port') || 1883),
        topic: String(form.get('topic') || '').trim(),
        qos: Number(form.get('qos') || 0),
        tls: form.get('tls') === 'on',
        ...(String(form.get('client_id') || '').trim() ? { client_id: String(form.get('client_id')).trim() } : {}),
      }
      const result = await createConnector(settings, {
        name, connector_type: kind, enabled: true, config,
        ...(kind === 'mqtt' && String(form.get('username') || '').trim() ? {
          username: String(form.get('username')).trim(),
          password: String(form.get('password') || ''),
        } : {}),
      })
      if (result.webhook_token) setWebhookToken(result.webhook_token)
      setNotice(kind === 'webhook' ? 'Webhook receiver created. Copy its secret now; Sentinel will not show it again.' : 'MQTT connector created. Sentinel is attempting to subscribe.')
      formElement.reset()
      await onRefresh()
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not create connector') }
    finally { setBusy(false) }
  }

  async function runAction(id: string, action: () => Promise<unknown>) {
    setWorkingId(id); setError(''); setNotice('')
    try { await action(); await onRefresh() }
    catch (err) { setError(err instanceof Error ? err.message : 'Connector action failed') }
    finally { setWorkingId('') }
  }

  const webhookUrl = (path: string) => settings.apiBaseUrl.replace(/\/$/, '') + path

  return <section className="functional-page connectors-page">
    <div className="page-title"><div><span>Inbound integrations</span><h1>Connectors</h1><p>Receive events from other systems with signed webhooks or an MQTT topic subscription.</p></div><button className="secondary-button" onClick={()=>void onRefresh()}><RefreshCw size={15}/> Refresh</button></div>
    <div className="connector-explainer panel"><Cable size={19}/><span>Sentinel has system monitoring connections (SSH, HTTP/HTTPS, ping) and event integrations (webhooks, MQTT). Monitoring connections attach to systems; event integrations receive data directly.</span></div>
    <AddSystemForm settings={settings} onAdded={onRefresh} />
    <section className="connector-section">
      <div className="connector-section-heading"><div><span>System monitoring</span><h2>SSH, HTTP/HTTPS, ping, and TCP checks</h2></div><span>{assets.length} systems</span></div>
      <div className="connector-cards">
        {assets.length ? assets.map(asset => {
          const metadata = asset.metadata || {}
          const mode = String(metadata.monitoring_mode || (metadata.credential_id ? 'ssh' : metadata.health_url || metadata.url ? 'http' : metadata.ip || metadata.hostname ? 'tcp' : 'unknown')).toLowerCase()
          const label = mode === 'ssh' ? 'SSH' : mode === 'http' ? (String(metadata.health_url || metadata.url || '').startsWith('https:') ? 'HTTPS' : 'HTTP') : mode === 'icmp' ? 'Ping / ICMP' : mode === 'tcp' ? 'TCP reachability' : mode.toUpperCase()
          const endpoint = metadata.health_url || metadata.ip || metadata.hostname || 'No endpoint recorded'
          return <article className="panel connector-card system-connection-card" key={asset.id}>
            <div className="connector-card-heading"><span className={'connector-dot ' + asset.health}/><div><h2>{asset.display_name}</h2><small>{label} · {asset.asset_type}</small></div><span className={'health-chip ' + asset.health}>{asset.health}</span></div>
            <dl><dt>Endpoint</dt><dd>{String(endpoint)}</dd><dt>State</dt><dd>{asset.state}</dd><dt>Last checked</dt><dd>{metadata.last_checked_at ? new Date(String(metadata.last_checked_at)).toLocaleString() : 'Not checked'}</dd><dt>Check result</dt><dd>{String(metadata.health_note || 'No check recorded yet')}</dd></dl>
            <div className="connector-card-actions"><button className="secondary-button" onClick={()=>onNavigate('entities')}>Manage system</button></div>
          </article>
        }) : <div className="panel large-panel-empty"><strong>No system connections yet</strong><span>Add a system above using SSH, HTTP/HTTPS, or ping.</span></div>}
      </div>
    </section>
    <section className="connector-section">
      <div className="connector-section-heading"><div><span>Inbound event integrations</span><h2>Webhook and MQTT</h2></div><span>{connectors.length} integrations</span></div>
    <form className="panel connector-form" onSubmit={create}>
      <h2>Add an inbound connector</h2>
      <p className="connector-form-intro">{kind === 'webhook'
        ? 'A webhook lets another app send events to Sentinel over HTTP. Create it, then copy the one-time secret into that app’s webhook settings.'
        : 'MQTT lets Sentinel subscribe to messages from your broker. Start with the broker host and topic; the usual port and QoS defaults are already set.'}</p>
      {kind === 'webhook' && <div className="connector-payload-guide">
        <strong>What Sentinel expects</strong>
        <span>Send a JSON object. These fields are optional; Sentinel fills in sensible defaults.</span>
        <pre><code>{JSON.stringify({
          type: "sensor.reading",
          severity: "info",
          summary: "Water temperature updated",
          entity: "North tank",
          value: { temperature_c: 22.4 },
        }, null, 2)}</code></pre>
        <small>Allowed severity values: info, warning, error, critical. Authenticate with the X-Sentinel-Webhook-Token header.</small>
      </div>}
      <label><span>Connector name</span><input name="name" required maxLength={120} placeholder="Home Assistant events"/></label>
      <label><span>Type</span><select value={kind} onChange={e=>setKind(e.target.value as ConnectorKind)}><option value="webhook">Webhook receiver</option><option value="mqtt">MQTT subscription</option></select></label>
      {kind === 'mqtt' && <>
        <label><span>Broker host</span><input name="host" required placeholder="mqtt.example.lan"/><small>Hostname or IP address that the Sentinel server can reach.</small></label>
        <label><span>Topic filter</span><input name="topic" required placeholder="sensors/+/state"/><small>Use + or # only if the broker should send multiple topics.</small></label>
        <label><span>Username (optional)</span><input name="username" autoComplete="username" placeholder="Broker username"/><small>If your broker uses login credentials, provide both username and password.</small></label>
        <label><span>Password (optional)</span><input name="password" type="password" autoComplete="new-password" placeholder="Stored in Sentinel vault"/></label>
        <details className="connector-advanced"><summary>Advanced connection options</summary>
          <div className="connector-advanced-grid">
            <label><span>Broker port</span><input name="port" type="number" min="1" max="65535" defaultValue="1883" required/><small>Usually 1883 without TLS or 8883 with TLS.</small></label>
            <label><span>Quality of Service (QoS)</span><select name="qos" defaultValue="0"><option value="0">0 · At most once</option><option value="1">1 · At least once</option><option value="2">2 · Exactly once</option></select></label>
            <label className="connector-checkbox"><input name="tls" type="checkbox"/><span>Use TLS encryption</span></label>
            <label><span>Client ID (optional)</span><input name="client_id" placeholder="Generated automatically if blank"/><small>Set this only if your broker requires a specific client ID.</small></label>
          </div>
        </details>
      </>}
      <button className="primary-button" disabled={busy}><Plus size={15}/>{busy ? 'Creating…' : 'Create connector'}</button>
      {error && <span className="form-error" role="alert">{error}</span>}
      {notice && <span className="connector-notice" role="status">{notice}</span>}
      {webhookToken && <div className="webhook-secret"><strong>Webhook secret · shown once</strong><code>{webhookToken}</code><button type="button" className="secondary-button" onClick={async()=>{await navigator.clipboard.writeText(webhookToken);setCopied(true)}}>{copied?<Check size={14}/>:<Copy size={14}/>} {copied?'Copied':'Copy secret'}</button><small>Send it as the X-Sentinel-Webhook-Token header. Treat it like a password.</small></div>}
    </form>
    <div className="connector-cards">
      {connectors.length ? connectors.map(connector => {
        const id = connector.id || ''
        const webhook = connector.connector_type === 'webhook'
        const endpoint = connector.ingest_path ? webhookUrl(connector.ingest_path) : ''
        return <article className="panel connector-card" key={id}>
          <div className="connector-card-heading"><span className={'connector-dot ' + connector.status}/><div><h2>{connector.name}</h2><small>{webhook?'Webhook receiver':'MQTT subscription'} · {connector.direction || 'inbound'}</small></div><span className={'health-chip ' + connector.status}>{connector.state || connector.status}</span></div>
          <dl><dt>State</dt><dd>{connector.enabled ? (connector.state || 'enabled') : 'paused'}</dd>
            {webhook ? <><dt>Ingest URL</dt><dd><code>{endpoint}</code></dd><dt>Secret</dt><dd>Stored as a hash; visible only when created</dd></> :
              <><dt>Broker</dt><dd>{String(connector.config?.host || 'Unknown')}:{String(connector.config?.port || 1883)}</dd><dt>Topic</dt><dd><code>{String(connector.config?.topic || 'Not set')}</code></dd><dt>Last check</dt><dd>{connector.last_checked_at ? new Date(connector.last_checked_at).toLocaleString() : 'Not checked'}</dd></>}
            {connector.last_error && <><dt>Last error</dt><dd className="form-error">{connector.last_error}</dd></>}
          </dl>
          {webhook && <small className="connector-help">The sender must be able to reach this URL. If the API address above uses localhost, change the dashboard API address to a host reachable by that sender.</small>}
          <div className="connector-card-actions">
            <button className="secondary-button" disabled={workingId===id} onClick={()=>void runAction(id,async()=>{const result=await testConnector(settings,id);setNotice(result.message)})}>{workingId===id?'Working…':'Test'}</button>
            <button className="secondary-button" disabled={workingId===id} onClick={()=>void runAction(id,()=>updateConnector(settings,id,{enabled:!connector.enabled}))}>{connector.enabled?<><ToggleRight size={15}/> Pause</>:<><ToggleLeft size={15}/> Resume</>}</button>
            <button className="secondary-button danger-button" disabled={workingId===id} onClick={()=>{if(window.confirm('Remove connector “'+connector.name+'”?'))void runAction(id,()=>deleteConnector(settings,id))}}><Trash2 size={14}/> Remove</button>
          </div>
        </article>
      }) : <div className="panel large-panel-empty"><strong>No event integrations configured</strong><span>Create a webhook for HTTP event delivery or an MQTT subscription for a broker topic.</span></div>}
    </div>
    </section>
  </section>
}
