import { useCallback, useMemo, useState, type FormEvent } from 'react'
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
  type NodeChange,
  type XYPosition,
} from '@xyflow/react'
import { Link2, Trash2 } from 'lucide-react'
import { SentinelNode } from './SentinelNode'
import type { Asset, Relationship, SystemHealth } from '../types'

const nodeTypes = {
  sentinel: SentinelNode,
}

export function SystemGraph({
  assets,
  health,
  relationships,
  onCreateRelationship,
  onDeleteRelationship,
  graphAnimation,
  canEdit,
}: {
  assets: Asset[]
  health: SystemHealth
  relationships: Relationship[]
  onCreateRelationship: (relationship: Omit<Relationship, 'id' | 'metadata'>) => Promise<void>
  onDeleteRelationship: (id: string) => Promise<void>
  graphAnimation: boolean
  canEdit: boolean
}) {
  const [showBuilder, setShowBuilder] = useState(false)
  const [graphKey, setGraphKey] = useState(0)
  const [source, setSource] = useState('')
  const [target, setTarget] = useState('')
  const [relationshipType, setRelationshipType] = useState('depends on')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [nodePositions, setNodePositions] = useState<Record<string, XYPosition>>(() => {
    try { return JSON.parse(localStorage.getItem('sentinel.graph.positions') || '{}') as Record<string, XYPosition> }
    catch { return {} }
  })

  const handleNodesChange = useCallback((changes: NodeChange[]) => {
    const moved = changes.filter(change => change.type === 'position' && 'position' in change && Boolean(change.position))
    if (!moved.length) return
    setNodePositions(current => {
      const next = { ...current }
      moved.forEach(change => {
        if (change.type === 'position' && change.position) next[change.id] = change.position
      })
      localStorage.setItem('sentinel.graph.positions', JSON.stringify(next))
      return next
    })
  }, [])

  const resetLayout = () => {
    localStorage.removeItem('sentinel.graph.positions')
    setNodePositions({})
    setGraphKey(value => value + 1)
  }

  const nodes = useMemo<Node[]>(() => {
    const coreNode: Node = {
      id: 'sentinel-core',
      type: 'sentinel',
      position: nodePositions['sentinel-core'] ?? { x: 620, y: 220 },
      data: {
        label: 'Sentinel Core',
        subtitle: health.status,
        status: health.status,
        icon: 'shield',
        kind: 'hub',
      },
    }

    const assetNodes = assets.map((asset, index): Node => {
      const angle = (index / Math.max(assets.length, 1)) * Math.PI * 2
      const radius = 350
      return {
        id: asset.id,
        type: 'sentinel',
        position: nodePositions[asset.id] ?? {
          x: 620 + Math.cos(angle) * radius,
          y: 220 + Math.sin(angle) * radius,
        },
        data: {
          label: asset.display_name,
          subtitle: asset.health,
          status: asset.health,
          icon: asset.asset_type.includes('server') ? 'database' : 'workflow',
          kind: 'leaf',
        },
      }
    })

    return [coreNode, ...assetNodes]
  }, [assets, health, nodePositions])

  const edges = useMemo<Edge[]>(() => [
    ...assets.map((asset) => ({
      id: `core-${asset.id}`,
      source: 'sentinel-core',
      target: asset.id,
      label: 'monitors',
      animated: graphAnimation,
      type: 'smoothstep',
      style: { strokeWidth: 1.6, stroke: '#3c5363' },
      labelStyle: { fill: '#a8bac8', fontSize: 10 },
      labelBgStyle: { fill: '#101b26' },
      labelBgPadding: [4, 2] as [number, number],
      labelBgBorderRadius: 4,
    })),
    ...relationships.map((relationship) => ({
      id: relationship.id,
      source: relationship.source_asset_id,
      target: relationship.target_asset_id,
      label: relationship.relationship_type,
      type: 'smoothstep',
      animated: false,
      style: { strokeWidth: 2, stroke: '#73c3a3' },
      labelStyle: { fill: '#d9e8e2', fontWeight: 600 },
      labelBgStyle: { fill: '#14221f' },
      labelBgPadding: [6, 3] as [number, number],
      labelBgBorderRadius: 5,
    })),
  ], [assets, relationships, graphAnimation])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await onCreateRelationship({
        source_asset_id: source,
        target_asset_id: target,
        relationship_type: relationshipType.trim(),
      })
      setSource('')
      setTarget('')
      setRelationshipType('depends on')
      setShowBuilder(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save connection')
    } finally {
      setSaving(false)
    }
  }

  const removeRelationship = async (id: string) => {
    setError(null)
    try { await onDeleteRelationship(id) }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not remove connection') }
  }

  return (
    <section className="panel graph-panel">
      <div className="panel-heading">
        <div>
          <h2>System Graph</h2>
          <div className="graph-legend">
            <span><i className="legend-dot healthy" />Healthy</span>
            <span><i className="legend-dot degraded" />Degraded</span>
            <span><i className="legend-dot offline" />Offline</span>
            <span><i className="legend-line" />Relationships</span>
          </div>
        </div>

        <div className="panel-actions">
          {canEdit && <button onClick={() => setShowBuilder((value) => !value)}>
            <Link2 size={15} /> {showBuilder ? 'Close' : 'Add connection'}
          </button>}
          <button className="square-button" onClick={resetLayout} aria-label="Reset graph layout" title="Reset graph layout">
            Reset layout
          </button>
        </div>
      </div>

      {canEdit && showBuilder && (
        <form className="graph-relationship-form" onSubmit={submit}>
          <label>
            <span>From</span>
            <select required value={source} onChange={(event) => setSource(event.target.value)}>
              <option value="">Choose a system</option>
              {assets.map((asset) => <option key={asset.id} value={asset.id}>{asset.display_name}</option>)}
            </select>
          </label>
          <label>
            <span>Relationship</span>
            <input required value={relationshipType} onChange={(event) => setRelationshipType(event.target.value)} placeholder="depends on" />
          </label>
          <label>
            <span>To</span>
            <select required value={target} onChange={(event) => setTarget(event.target.value)}>
              <option value="">Choose a system</option>
              {assets.filter((asset) => asset.id !== source).map((asset) => <option key={asset.id} value={asset.id}>{asset.display_name}</option>)}
            </select>
          </label>
          <button className="primary-button" disabled={saving || !source || !target || source === target}>
            {saving ? 'Saving…' : 'Create link'}
          </button>
          {error && <span className="form-error">{error}</span>}
        </form>
      )}

      {relationships.length > 0 && (
        <div className="relationship-list" aria-label="Saved relationships">
          {relationships.map(relationship => {
            const from = assets.find(asset => asset.id === relationship.source_asset_id)?.display_name ?? relationship.source_asset_id
            const to = assets.find(asset => asset.id === relationship.target_asset_id)?.display_name ?? relationship.target_asset_id
            return <div className="relationship-row" key={relationship.id}>
              <span><strong>{from}</strong> {relationship.relationship_type} <strong>{to}</strong></span>
              {canEdit && <button className="icon-button" onClick={() => void removeRelationship(relationship.id)} aria-label={'Remove relationship ' + relationship.relationship_type}><Trash2 size={15}/></button>}
            </div>
          })}
        </div>
      )}
      {error && <div className="form-error graph-error">{error}</div>}

      <div className="graph-canvas">
        <ReactFlow
          key={graphKey}
          nodes={nodes}
          edges={edges}
          onNodesChange={handleNodesChange}
          nodeTypes={nodeTypes}
          fitView
          zoomOnScroll={false}
          fitViewOptions={{ padding: 0.25 }}
          minZoom={0.45}
          maxZoom={1.8}
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={26} size={1} />
          <Controls showInteractive={false} />
          <MiniMap pannable zoomable nodeStrokeWidth={3} />
        </ReactFlow>

        {assets.length === 0 && (
          <div className="graph-empty-message">
            <strong>No connected assets</strong>
            <span>Add a system in Entities to populate the graph.</span>
          </div>
        )}
      </div>
    </section>
  )
}
