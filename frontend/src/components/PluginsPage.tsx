import { useEffect, useState } from 'react'
import { ArrowUpRight, Cable, Download, Puzzle, RefreshCw, Settings2 } from 'lucide-react'
import { getPlugins, type PluginRecord } from '../api/client'
import type { SentinelSettings } from '../config'

const CATALOG_URL = 'https://raw.githubusercontent.com/Agrineuro/sentinel/master/plugins/catalog.json'
const REPOSITORY_TREE = 'https://github.com/Agrineuro/sentinel/tree/master'
const PLUGINS_DIRECTORY = REPOSITORY_TREE + '/plugins'

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

export function PluginsPage({ settings, onConfigure }: { settings: SentinelSettings; onConfigure: () => void }) {
  const [catalog, setCatalog] = useState<PluginCatalog | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [loadedPlugins, setLoadedPlugins] = useState<PluginRecord[]>([])

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

  useEffect(() => {
    void loadCatalog()
    void getPlugins(settings).then(records => {
      setLoadedPlugins(records)
      setCatalog(current => current ?? {
        schema_version: 1,
        repository: 'https://github.com/Agrineuro/sentinel',
        plugins: records.map(plugin => ({
          id: plugin.id, name: plugin.name, category: 'Connector',
          status: 'available', description: plugin.description,
          capabilities: plugin.capabilities,
        })),
      })
    }).catch(() => setLoadedPlugins([]))
  }, [settings])

  return <section className="functional-page plugins-page">
    <div className="page-title"><div><span>Optional integrations</span><h1>Plugins</h1><p>Keep Sentinel Core small and add connector capabilities when you need them.</p></div><a className="secondary-button plugin-github-link" href={PLUGINS_DIRECTORY} target="_blank" rel="noreferrer"><ArrowUpRight size={15}/> GitHub plugin source</a></div>
    <div className="plugin-intro panel"><Puzzle size={19}/><div><strong>Extend Sentinel without bloating the base install</strong><p>The catalog loads from Sentinel on GitHub. Loaded in Core means the connector is ready to configure; other entries link to source or planned work. GitHub installation from this page is not enabled yet.</p></div></div>
    {error && <div className="panel plugin-load-error" role="status"><span>Could not load the live GitHub catalog: {error}</span><button className="secondary-button" onClick={() => void loadCatalog()}><RefreshCw size={14}/> Retry</button></div>}
    {loading && <div className="panel large-panel-empty"><strong>Loading plugin catalog...</strong></div>}
    {!loading && catalog && <div className="plugin-grid">{catalog.plugins.map(plugin => {
      const sourceUrl = plugin.source_path ? REPOSITORY_TREE + '/' + plugin.source_path : PLUGINS_DIRECTORY
      const loaded = loadedPlugins.find(item => item.id === plugin.id)
      return <article className="panel plugin-card" key={plugin.id}>
        <div className="plugin-card-head"><span className="plugin-icon"><Cable size={17}/></span><span className={'plugin-status ' + (loaded ? 'available' : plugin.status)}>{loaded ? 'Loaded in Core' : statusLabel(plugin.status)}</span></div>
        <span className="plugin-category">{plugin.category}</span><h2>{plugin.name}</h2><p>{plugin.description}</p>
        <div className="plugin-capabilities">{plugin.capabilities.map(capability => <span key={capability}>{capability}</span>)}</div>
        {loaded ? <button className="secondary-button" onClick={onConfigure}><Settings2 size={14}/> Configure connection</button> : <a className="secondary-button" href={sourceUrl} target="_blank" rel="noreferrer"><ArrowUpRight size={14}/> {plugin.source_path ? 'View source on GitHub' : 'View GitHub catalog'}</a>}
      </article>
    })}</div>}
    {!loading && !catalog && <div className="panel large-panel-empty"><strong>Plugin catalog unavailable</strong><span>Sentinel still works. Check the GitHub connection and retry.</span></div>}
    <p className="plugin-install-note"><Download size={14}/> Loaded plugins run through the Sentinel connector registry. Planned connectors remain catalog entries until their packages are added to GitHub and the install workflow is enabled.</p>
  </section>
}
