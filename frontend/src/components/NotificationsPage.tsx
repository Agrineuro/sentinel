import { useEffect, useState, type FormEvent } from 'react'
import { Bell, Check, Mail, MessageSquare, Pause, Play, RefreshCw, Send } from 'lucide-react'
import type { SentinelSettings } from '../config'
import type { RuleRecord } from '../types'
import {
  createNotificationDestination, getNotificationDeliveries, getNotificationDestinations,
  getNotificationSubscriptions, getRules, testNotificationDestination,
  updateNotificationDestination, updateNotificationSubscriptions,
  type NotificationDelivery, type NotificationDestination,
} from '../api/client'

export function NotificationsPage({ settings }: { settings: SentinelSettings }) {
  const [channel, setChannel] = useState<'email' | 'sms'>('email')
  const [destinations, setDestinations] = useState<NotificationDestination[]>([])
  const [deliveries, setDeliveries] = useState<NotificationDelivery[]>([])
  const [rules, setRules] = useState<RuleRecord[]>([])
  const [subscriptions, setSubscriptions] = useState<Record<string, string[]>>({})
  const [busy, setBusy] = useState(false)
  const [working, setWorking] = useState('')
  const [savingRule, setSavingRule] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  async function refresh() {
    const [nextDestinations, nextDeliveries, nextRules, nextSubscriptions] = await Promise.all([
      getNotificationDestinations(settings), getNotificationDeliveries(settings),
      getRules(settings), getNotificationSubscriptions(settings),
    ])
    setDestinations(nextDestinations)
    setDeliveries(nextDeliveries)
    setRules(nextRules)
    setSubscriptions(nextSubscriptions)
  }

  useEffect(() => { void refresh().catch(err => setError(err instanceof Error ? err.message : 'Could not load notifications')) }, [settings])

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const formElement = event.currentTarget
    const form = new FormData(formElement)
    setBusy(true); setError(''); setNotice('')
    try {
      const config = channel === 'email' ? {
        smtp_host: String(form.get('smtp_host') || '').trim(),
        smtp_port: Number(form.get('smtp_port') || 587),
        security: String(form.get('security') || 'starttls'),
        from_address: String(form.get('from_address') || '').trim(),
        smtp_username: String(form.get('smtp_username') || '').trim(),
      } : {
        account_sid: String(form.get('account_sid') || '').trim(),
        from_number: String(form.get('from_number') || '').trim(),
      }
      await createNotificationDestination(settings, {
        name: String(form.get('name') || '').trim(),
        channel_type: channel,
        destination: String(form.get('destination') || '').trim(),
        provider_secret: String(form.get('provider_secret') || ''),
        config,
      })
      formElement.reset()
      await refresh()
      setNotice('Destination saved separately from account sign-in. Send a test to verify delivery.')
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not save notification destination') }
    finally { setBusy(false) }
  }

  async function test(row: NotificationDestination) {
    if (row.channel_type === 'sms' && !window.confirm('Send a real test SMS to ' + row.masked_destination + '? Your carrier or provider may charge for it.')) return
    setWorking(row.id); setError(''); setNotice('')
    try {
      const result = await testNotificationDestination(settings, row.id)
      setNotice(result.message)
      await refresh()
    } catch (err) { setError(err instanceof Error ? err.message : 'Test delivery failed') }
    finally { setWorking('') }
  }

  async function toggle(row: NotificationDestination) {
    setWorking(row.id); setError('')
    try { await updateNotificationDestination(settings, row.id, !row.enabled); await refresh() }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not update destination') }
    finally { setWorking('') }
  }

  function toggleRuleDestination(ruleId: string, destinationId: string, checked: boolean) {
    setSubscriptions(current => ({
      ...current,
      [ruleId]: checked
        ? [...new Set([...(current[ruleId] || []), destinationId])]
        : (current[ruleId] || []).filter(id => id !== destinationId),
    }))
  }

  async function saveRuleSubscriptions(ruleId: string) {
    setSavingRule(ruleId); setError('')
    try {
      const saved = await updateNotificationSubscriptions(settings, ruleId, subscriptions[ruleId] || [])
      setSubscriptions(current => ({ ...current, [ruleId]: saved }))
      setNotice('Your notification choices were saved.')
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not save notification choices') }
    finally { setSavingRule('') }
  }

  const verifiedDestinations = destinations.filter(destination => destination.enabled && ['verified', 'error'].includes(destination.status))

  return <section className="functional-page notifications-page">
    <div className="page-title"><div><span>Outbound delivery</span><h1>Notifications</h1><p>Choose where Sentinel sends your alerts. Destinations are separate from account sign-in email.</p></div><button className="secondary-button" onClick={() => void refresh()}><RefreshCw size={15}/> Refresh</button></div>
    <div className="plugin-intro panel"><Bell size={18}/><div><strong>Alerts become useful when they reach you</strong><p>Add an email or SMS destination, verify it with a test, then choose which alert rules send to it. Each user manages their own destinations and subscriptions.</p></div></div>
    <form className="panel notification-form" onSubmit={create}>
      <h2>Add a destination</h2>
      <label><span>Destination name</span><input name="name" maxLength={120} required placeholder="On-call phone or work email"/></label>
      <label><span>Channel</span><select value={channel} onChange={event => setChannel(event.target.value as 'email' | 'sms')}><option value="email">Email via SMTP</option><option value="sms">Text message via Twilio</option></select></label>
      <label><span>{channel === 'email' ? 'Recipient email' : 'Recipient phone number'}</span><input name="destination" required type={channel === 'email' ? 'email' : 'tel'} placeholder={channel === 'email' ? 'alerts@example.com' : '+14155550123'}/><small>{channel === 'email' ? 'This destination is independent of any Sentinel account email.' : 'Use E.164 format. Your SMS provider or carrier may charge for sent messages.'}</small></label>
      {channel === 'email' ? <div className="notification-form-grid">
        <label><span>SMTP server</span><input name="smtp_host" required placeholder="smtp.example.com"/></label>
        <label><span>Port</span><input name="smtp_port" type="number" min="1" max="65535" defaultValue="587" required/></label>
        <label><span>Connection security</span><select name="security" defaultValue="starttls"><option value="starttls">STARTTLS</option><option value="ssl">SSL/TLS</option></select></label>
        <label><span>From email</span><input name="from_address" type="email" required placeholder="sentinel@example.com"/></label>
        <label><span>SMTP username (optional)</span><input name="smtp_username" autoComplete="username"/></label>
        <label><span>SMTP password (optional)</span><input name="provider_secret" type="password" autoComplete="new-password"/><small>Encrypted in Sentinel’s vault.</small></label>
      </div> : <div className="notification-form-grid">
        <label><span>Twilio Account SID</span><input name="account_sid" required placeholder="AC…"/></label>
        <label><span>Twilio sender number</span><input name="from_number" type="tel" required placeholder="+14155550100"/></label>
        <label><span>Twilio Auth Token</span><input name="provider_secret" type="password" required autoComplete="new-password"/><small>Encrypted in Sentinel’s vault.</small></label>
      </div>}
      <button className="primary-button" disabled={busy}><Send size={15}/>{busy ? 'Saving…' : 'Save destination'}</button>
    </form>
    {error && <div className="panel form-error" role="alert">{error}</div>}
    {notice && <div className="panel connector-notice" role="status"><Check size={15}/>{notice}</div>}
    <section className="notification-section"><h2>Your destinations</h2><div className="notification-grid">
      {destinations.length ? destinations.map(row => <article className="panel notification-card" key={row.id}>
        <div className="notification-card-title">{row.channel_type === 'email' ? <Mail size={17}/> : <MessageSquare size={17}/>}<div><strong>{row.name}</strong><small>{row.channel_type === 'email' ? 'Email' : 'SMS'} · {row.masked_destination}</small></div><span className={'health-chip ' + (row.status === 'verified' ? 'healthy' : row.status === 'error' ? 'offline' : 'unknown')}>{row.enabled ? row.status : 'disabled'}</span></div>
        {row.last_error && <small className="form-error">Last delivery error: {row.last_error}</small>}
        <div className="connector-card-actions"><button className="secondary-button" disabled={working === row.id || !row.enabled} onClick={() => void test(row)}><Send size={14}/>{working === row.id ? 'Sending…' : 'Send test'}</button><button className="secondary-button" disabled={working === row.id} onClick={() => void toggle(row)}>{row.enabled ? <><Pause size={14}/>Pause</> : <><Play size={14}/>Enable</>}</button></div>
      </article>) : <div className="panel large-panel-empty"><strong>No notification destinations yet</strong><span>Add a separate email or phone above. Sentinel never uses account email automatically.</span></div>}
    </div></section>
    <section className="notification-section"><h2>Your alert subscriptions</h2><p>Choose which rules send alerts to your destinations. These preferences are private to your account.</p><div className="notification-rules">
      {rules.length ? rules.map((rule: RuleRecord) => <article className="panel notification-rule" key={rule.id}>
        <div className="notification-rule-heading"><div><strong>{rule.name}</strong><small>{rule.minimum_severity}+ · {rule.observation_type}</small></div><button className="secondary-button" disabled={savingRule === rule.id} onClick={() => void saveRuleSubscriptions(rule.id)}>{savingRule === rule.id ? 'Saving…' : 'Save choices'}</button></div>
        {verifiedDestinations.length ? verifiedDestinations.map(destination =>
          <label key={destination.id}><input type="checkbox" checked={(subscriptions[rule.id] || []).includes(destination.id)} onChange={event => toggleRuleDestination(rule.id, destination.id, event.target.checked)}/><span>{destination.name} · {destination.channel_type.toUpperCase()} · {destination.masked_destination}</span></label>)
          : <small>Add and test a destination above to choose where this rule sends alerts.</small>}
      </article>) : <div className="panel large-panel-empty"><span>Create an alert rule first. Then choose your destinations for it.</span></div>}
    </div></section>
    <section className="notification-section"><h2>Recent delivery history</h2><div className="notification-deliveries">
      {deliveries.length ? deliveries.map(row => <article className="panel notification-delivery" key={row.id}><div><strong>{row.alert_title}</strong><small>{row.destination_name} · {row.channel_type}</small></div><span className={'health-chip ' + (row.status === 'sent' ? 'healthy' : row.status === 'failed' ? 'offline' : 'unknown')}>{row.status}</span><small>{row.status === 'sent' && row.sent_at ? new Date(row.sent_at).toLocaleString() : row.status === 'pending' ? 'Attempts: ' + row.attempts : row.last_error || 'No detail'}</small></article>) : <div className="panel large-panel-empty"><span>Delivery attempts will appear here when a subscribed rule opens an alert.</span></div>}
    </div></section>
  </section>
}
