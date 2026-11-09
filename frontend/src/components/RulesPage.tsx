import { useState, type FormEvent } from 'react'
import { Eye, Plus, Trash2, ToggleLeft, ToggleRight } from 'lucide-react'
import type { RuleRecord } from '../types'
import type { SentinelSettings } from '../config'
import { previewRule, type RulePreview } from '../api/client'

type NewRule = Omit<RuleRecord, 'id' | 'created_at' | 'updated_at'>
export function RulesPage({ rules, settings, onCreate, onToggle, onDelete, canOperate }: {
  rules: RuleRecord[]
  settings: SentinelSettings
  onCreate: (rule: NewRule) => Promise<void>
  onToggle: (rule: RuleRecord) => Promise<void>
  onDelete: (rule: RuleRecord) => Promise<void>
  canOperate: boolean
}) {
  const [name, setName] = useState('')
  const [type, setType] = useState('health')
  const [severity, setSeverity] = useState('warning')
  const [entity, setEntity] = useState('')
  const [summary, setSummary] = useState('')
  const [field, setField] = useState('')
  const [operator, setOperator] = useState<'gt' | 'gte' | 'lt' | 'lte'>('gte')
  const [threshold, setThreshold] = useState('')
  const [busy, setBusy] = useState(false)
  const [previewing, setPreviewing] = useState(false)
  const [error, setError] = useState('')
  const [preview, setPreview] = useState<RulePreview | null>(null)

  const draft = (): NewRule => ({
    name: name.trim(), description: '', observation_type: type.trim() || '*',
    minimum_severity: severity, source_contains: null,
    entity_contains: entity.trim() || null, summary_contains: summary.trim() || null,
    condition_field: field.trim() || null,
    condition_operator: field.trim() ? operator : null,
    condition_value: field.trim() && threshold !== '' ? Number(threshold) : null,
    enabled: true,
  })
  const validNumericDraft = !field.trim() || (threshold !== '' && Number.isFinite(Number(threshold)))

  const runPreview = async () => {
    setPreviewing(true); setError('')
    try {
      setPreview(await previewRule(settings, draft()))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not preview this rule')
    } finally {
      setPreviewing(false)
    }
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true); setError('')
    try {
      await onCreate(draft())
      setName(''); setEntity(''); setSummary(''); setField(''); setThreshold(''); setPreview(null)
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not create rule') }
    finally { setBusy(false) }
  }

  return <section className="functional-page">
    <div className="page-title"><div><span>Deterministic evaluation</span><h1>Rules</h1><p>Match observations by type, severity, text, or numeric values to create alerts.</p></div></div>
    {canOperate && <form className="panel rule-form" onSubmit={submit}>
      <h2>Create a rule</h2>
      <label><span>Name</span><input required value={name} onChange={e=>setName(e.target.value)} placeholder="High host resource use"/></label>
      <label><span>Observation type</span><input value={type} onChange={e=>setType(e.target.value)} placeholder="health or *"/></label>
      <label><span>Minimum severity</span><select value={severity} onChange={e=>setSeverity(e.target.value)}><option value="info">Info</option><option value="warning">Warning</option><option value="error">Error</option><option value="critical">Critical</option></select></label>
      <label><span>Entity contains (optional)</span><input value={entity} onChange={e=>setEntity(e.target.value)} placeholder="system name"/></label>
      <label><span>Summary contains (optional)</span><input value={summary} onChange={e=>setSummary(e.target.value)} placeholder="unreachable"/></label>
      <label><span>Numeric field (optional)</span><input value={field} onChange={e=>setField(e.target.value)} placeholder="cpu_percent or metrics.cpu"/></label>
      {field.trim() && <>
        <label><span>Comparison</span><select value={operator} onChange={e=>setOperator(e.target.value as typeof operator)}><option value="gte">At least (≥)</option><option value="gt">Greater than (&gt;)</option><option value="lte">At most (≤)</option><option value="lt">Less than (&lt;)</option></select></label>
        <label><span>Threshold</span><input type="number" step="any" required value={threshold} onChange={e=>setThreshold(e.target.value)} placeholder="85"/></label>
      </>}
      <div className="rule-form-actions">
        <button type="button" className="secondary-button" disabled={previewing || !name.trim() || !validNumericDraft} onClick={()=>void runPreview()}><Eye size={15}/>{previewing ? 'Checking…' : 'Preview matches'}</button>
        <button className="primary-button" disabled={busy || !validNumericDraft}><Plus size={15}/>{busy ? 'Saving…' : 'Create rule'}</button>
      </div>
      {error && <span className="form-error">{error}</span>}
      {preview && <div className="rule-preview" role="status">
        <strong>{preview.match_count} matching observations</strong><span>Scanned {preview.scanned} recent observations. Preview does not create alerts.</span>
        {preview.matches.slice(0,5).map(row=><small key={row.id}>{row.entity || 'No system'} · {row.severity} · {row.summary}</small>)}
      </div>}
    </form>}
    {!canOperate && <p className="role-readonly-note">Viewer access - rules can be viewed but not changed.</p>}
    <div className="rule-list">
      {rules.length ? rules.map(rule=><article className="panel rule-card" key={rule.id}>
        <div><span className={'health-chip ' + (rule.enabled?'healthy':'unknown')}>{rule.enabled?'Enabled':'Paused'}</span><h2>{rule.name}</h2><p>{rule.observation_type} observations · {rule.minimum_severity}+ severity{rule.entity_contains ? ' · entity contains “' + rule.entity_contains + '”' : ''}{rule.summary_contains ? ' · summary contains “' + rule.summary_contains + '”' : ''}{rule.condition_field ? ' · ' + rule.condition_field + ' ' + (rule.condition_operator || '') + ' ' + rule.condition_value : ''}</p></div>
        {canOperate && <><button className="secondary-button" onClick={()=>void onToggle(rule)} aria-label={rule.enabled?'Pause rule':'Enable rule'}>{rule.enabled?<ToggleRight size={17}/>:<ToggleLeft size={17}/>} {rule.enabled?'Pause':'Enable'}</button>
        <button className="icon-button" onClick={()=>void onDelete(rule)} aria-label={'Delete ' + rule.name}><Trash2 size={16}/></button></>}
      </article>) : <div className="panel large-panel-empty"><strong>No rules yet</strong><span>Create a rule to turn observations into alerts.</span></div>}
    </div>
  </section>
}
