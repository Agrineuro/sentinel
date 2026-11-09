import { useEffect, useState } from 'react'
import { ArrowUpRight, Cable, Download, Puzzle, RefreshCw } from 'lucide-react'

const CATALOG_URL = 'https://raw.githubusercontent.com/Agrineuro/sentinel/master/plugins/catalog.json'
const PLUGINS_DIRECTORY = 'https://github.com/Agrineuro/sentinel/tree/master/plugins'

type PluginEntry = {
  id: string
  name: string
  category: string
  status: 'available' | 'template' | 'planned' | string
  description: string
  capabilities: string[]
  source_path?: string | null
}
type PluginCatalog = { schema_version: number; repository: string; plugins: PluginEntry[] }

function statusLabel(status: string) {
  if (status === 'available') return 'Available'
  if (status === 'template') return 'Starter template'
  if (status === 'in_development') return 'In development'
  return 'Planned'
}

export function PluginsPage() {
  const [catalog, setCatalog] = useState<PluginCatalog | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function loadCatalog() {
    setLoading(true)
    setError('')
    try {
      const response = await fetch(CATALOG_URL, { headers: { Accept: 'application/json' }, cache: 'no-store' })
      if (!response.ok) throw new Error('GitHub returned ' + response.status)
      const result = await response.json() as PluginCatalog
      if (result.schema_version !== 1 || !Array.isArray(result.plugins)) throw new Error('The GitHub catalog has an unsupported format')
      setCatalog(result)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not load the GitHub catalog')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void loadCatalog() }, [])

  return <section className="functional-page plugins-page">
    <div className="page-title"><div><span>Optional integrations</span><h1>Plugins</h1><p>Keep Sentinel Core small and add connector capabilities when you need them.</p></div><a className="secondary-button plugin-github-link" href={PLUGINS_DIRECTORY} target="_blank" rel="noreferrer"><ArrowUpRight size={15}/> GitHub plugin source</a></div>
    <div className="plugin-intro panel"><Puzzle size={19}/><div><strong>Extend Sentinel without bloating the base install</strong><p>The official catalog loads from the Sentinel GitHub repository. Planned entries are ideas for future plugins; only entries marked Available can be installed.</p></div></div>
    {error && <div className="panel plugin-load-error" role="status"><span>Could not load the live GitHub catalog: {error}</span><button className="secondary-button" onClick={() => void loadCatalog()}><RefreshCw size={14}/> Retry</button></div>}
    {loading && <div className="panel large-panel-empty"><strong>Loading plugin catalog...</strong></div>}
    {!loading && catalog && <div className="plugin-grid">{catalog.plugins.map(plugin => {
      const sourceUrl = plugin.source_path ? PLUGINS_DIRECTORY + '/' + plugin.source_path : PLUGINS_DIRECTORY
      return <article className="panel plugin-card" key={plugin.id}>
        <div className="plugin-card-head"><span className="plugin-icon"><Cable size={17}/></span><span className={'plugin-status ' + plugin.status}>{statusLabel(plugin.status)}</span></div>
        <span className="plugin-category">{plugin.category}</span><h2>{plugin.name}</h2><p>{plugin.description}</p>
        <div className="plugin-capabilities">{plugin.capabilities.map(capability => <span key={capability}>{capability}</span>)}</div>
        <a className="secondary-button" href={sourceUrl} target="_blank" rel="noreferrer"><ArrowUpRight size={14}/> {plugin.source_path ? 'View plugin template' : 'View GitHub catalog'}</a>
      </article>
    })}</div>}
    {!loading && !catalog && <div className="panel large-panel-empty"><strong>Plugin catalog unavailable</strong><span>Sentinel still works. Check the GitHub connection and retry.</span></div>}
    <p className="plugin-install-note"><Download size={14}/> Plugin installation and runtime loading are not wired up yet. This page is the GitHub-backed catalog; the next step is building the install flow and first working optional connector.</p>
  </section>
}
