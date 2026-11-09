import { Box, Cpu, HardDrive, Network, Pencil, Server, Trash2 } from 'lucide-react'
import type { Asset } from '../types'
import type { SentinelSettings } from '../config'
import { updateAsset, deleteAsset } from '../api/client'
import { AddSystemForm } from './AddSystemForm'

function assetIcon(assetType: string) {
  const type = assetType.toLowerCase()

  if (type.includes('server') || type.includes('linux')) return Server
  if (type.includes('storage')) return HardDrive
  if (type.includes('network')) return Network
  if (type.includes('processor')) return Cpu

  return Box
}

export function EntitiesPage({ assets, settings, onAdded, canOperate }: { assets: Asset[]; settings: SentinelSettings; onAdded: () => Promise<void>; canOperate: boolean }) {
  return (
    <section className="entities-page">
      <div className="page-title">
        <div>
          <span>Asset registry</span>
          <h1>Entities</h1>
          <p>
            Systems registered for monitoring by Sentinel using SSH, HTTP checks, or ping reachability.
          </p>
        </div>
      </div>

      {canOperate ? <AddSystemForm settings={settings} onAdded={onAdded} /> : <p className="role-readonly-note">Viewer access - systems can be viewed but not changed.</p>}

      <section className="entity-grid">
        {assets.length === 0 ? (
          <article className="panel empty-state">
            <Server size={34} />
            <h2>No assets discovered</h2>
            <p>
              Run an SSH discovery request and the resulting asset will appear
              here.
            </p>
          </article>
        ) : (
          assets.map((asset) => {
            const Icon = assetIcon(asset.asset_type)

            return (
              <article className="panel entity-card" key={asset.id}>
                <div className="entity-card-heading">
                  <span className="entity-icon">
                    <Icon size={21} />
                  </span>

                  <div>
                    <strong>{asset.display_name}</strong>
                    <small>{asset.asset_type}</small>
                  </div>

                  <span className={`health-chip ${asset.health}`}>
                    {asset.health}
                  </span>
                </div>

                {canOperate && <div className="entity-actions">
                <details className="entity-edit">
                  <summary className="secondary-button"><Pencil size={14} /> Edit system</summary>
                  <form className="entity-edit-form" onSubmit={async (event) => {
                    event.preventDefault()
                    const form = new FormData(event.currentTarget)
                    const site = String(form.get('site_id') || '').trim()
                    const ip = String(form.get('ip') || '').trim()
                    try {
                      await updateAsset(settings, asset.id, {
                        display_name: String(form.get('display_name') || '').trim(),
                        asset_type: String(form.get('asset_type') || '').trim(),
                        organization_id: String(form.get('organization_id') || '').trim(),
                        site_id: site || null,
                        metadata: { ...asset.metadata, ip },
                      })
                      await onAdded()
                    } catch (err) { window.alert(err instanceof Error ? err.message : 'Could not update system') }
                  }}>
                    <label><span>Name</span><input name="display_name" required maxLength={120} defaultValue={asset.display_name} /></label>
                    <label><span>Type</span><input name="asset_type" required maxLength={80} defaultValue={asset.asset_type} /></label>
                    <label><span>Organization</span><input name="organization_id" required maxLength={120} defaultValue={asset.organization_id} /></label>
                    <label><span>Site</span><input name="site_id" defaultValue={asset.site_id ?? ''} /></label>
                    <label><span>Host or IP</span><input name="ip" defaultValue={String(asset.metadata.ip ?? '')} /></label>
                    <div className="form-actions"><button className="primary-button">Save changes</button></div>
                  </form>
                </details>
                <button className="secondary-button danger-button" onClick={async () => {
                  if (!window.confirm('Remove ' + asset.display_name + '? Historical observations and alerts will be kept.')) return
                  try { await deleteAsset(settings, asset.id); await onAdded() }
                  catch (err) { window.alert(err instanceof Error ? err.message : 'Could not remove system') }
                }}><Trash2 size={14} /> Remove</button>
              </div>}
              <dl>
                  <dt>State</dt>
                  <dd>{asset.state}</dd>

                  <dt>Organization</dt>
                  <dd>{asset.organization_id}</dd>

                  <dt>Site</dt>
                  <dd>{asset.site_id ?? 'Unassigned'}</dd>

                  <dt>Endpoint</dt>
                  <dd>{String(asset.metadata.health_url ?? asset.metadata.ip ?? asset.metadata.hostname ?? 'Unknown')}</dd>

                  <dt>Connection</dt>
                  <dd>{String(asset.metadata.monitoring_mode ?? (asset.metadata.credential_id ? 'ssh' : 'tcp')).toUpperCase()}</dd>

                  <dt>Operating system</dt>
                  <dd>{String(asset.metadata.os ?? 'Unknown')}</dd>

                  <dt>CPU load</dt>
                  <dd>{asset.metadata.cpu_percent == null ? 'Unknown' : `${asset.metadata.cpu_percent}%`}</dd>

                  <dt>Memory used</dt>
                  <dd>{asset.metadata.memory_used_percent == null ? 'Unknown' : `${asset.metadata.memory_used_percent}% of ${asset.metadata.memory_total_gb} GiB`}</dd>

                  <dt>Root disk used</dt>
                  <dd>{asset.metadata.disk_root_used_percent == null ? 'Unknown' : `${asset.metadata.disk_root_used_percent}%`}</dd>

                  <dt>Last checked</dt>
                  <dd>{asset.metadata.last_checked_at ? new Date(String(asset.metadata.last_checked_at)).toLocaleString() : 'Unknown'}</dd>

                  <dt>Collection</dt>
                  <dd>{String(asset.metadata.health_note ?? 'Snapshot')}</dd>
                </dl>

                <small className="entity-id">{asset.id}</small>
              </article>
            )
          })
        )}
      </section>
    </section>
  )
}
