import hashlib
from datetime import datetime,timedelta,timezone
from sqlalchemy.orm import Session
from app.models.asset import AssetModel
from app.models.connector import ConnectorModel
from app.models.relationship import RelationshipModel
from app.plugins.registry import plugin_registry
from app.schemas.observations import ObservationCreate
from app.services.observation_registry import observation_registry
from app.vault.service import vault_service


def _resource_key(connector_id,row):
    return ":".join(str(row.get(k) or "") for k in ("type","node","vmid","storage","name"))+":"+connector_id

def _display_name(row):
    kind=str(row.get("type") or "resource")
    name=str(row.get("name") or row.get("node") or row.get("storage") or "Unnamed resource")
    if kind=="node": return "Proxmox node: "+name
    if kind=="qemu": return "VM "+str(row.get("vmid","?"))+": "+name
    if kind=="lxc": return "Container "+str(row.get("vmid","?"))+": "+name
    if kind=="storage": return "Storage: "+name
    return "Proxmox "+kind+": "+name

def _state(row):
    kind=str(row.get("type") or "")
    status=str(row.get("status") or "unknown").lower()
    if kind=="node":
        if status=="online":
            cpu=row.get("cpu")
            mem,maxmem=row.get("mem"),row.get("maxmem")
            disk,maxdisk=row.get("disk"),row.get("maxdisk")
            cpu_pct=float(cpu)*100 if isinstance(cpu,(int,float)) else 0
            mem_pct=float(mem)/float(maxmem)*100 if isinstance(mem,(int,float)) and isinstance(maxmem,(int,float)) and maxmem>0 else 0
            disk_pct=float(disk)/float(maxdisk)*100 if isinstance(disk,(int,float)) and isinstance(maxdisk,(int,float)) and maxdisk>0 else 0
            if max(cpu_pct,mem_pct,disk_pct)>=95: return "online","critical","critical"
            if cpu_pct>=85 or mem_pct>=85 or disk_pct>=80: return "online","degraded","warning"
            return "online","healthy","info"
        if status=="offline": return "offline","offline","critical"
    if kind in ("qemu","lxc"):
        if status=="running": return "running","healthy","info"
        if status in ("stopped","paused"): return status,"unknown","info"
    if kind=="storage" and status in ("available","active","online"): return status,"healthy","info"
    return status,"unknown","info"

def _metrics(row):
    out={}
    cpu=row.get("cpu")
    if isinstance(cpu,(int,float)): out["cpu_percent"]=round(float(cpu)*100,1)
    mem,maxmem=row.get("mem"),row.get("maxmem")
    if isinstance(mem,(int,float)) and isinstance(maxmem,(int,float)) and maxmem>0:
        out.update(memory_used_percent=round(float(mem)/float(maxmem)*100,1),memory_used_bytes=int(mem),memory_total_bytes=int(maxmem))
    disk,maxdisk=row.get("disk"),row.get("maxdisk")
    if isinstance(disk,(int,float)) and isinstance(maxdisk,(int,float)) and maxdisk>0:
        out.update(disk_used_percent=round(float(disk)/float(maxdisk)*100,1),disk_used_bytes=int(disk),disk_total_bytes=int(maxdisk))
    if isinstance(row.get("uptime"),(int,float)): out["uptime_seconds"]=int(row["uptime"])
    if isinstance(row.get("maxcpu"),(int,float)): out["cpu_count"]=int(row["maxcpu"])
    return out

def refresh_proxmox_connectors(db:Session):
    broadcasts=[]
    plugin=plugin_registry.get_connector("proxmox")
    if plugin is None: return broadcasts
    now=datetime.now(timezone.utc)
    connectors=db.query(ConnectorModel).filter(ConnectorModel.connector_type=="proxmox",ConnectorModel.enabled.is_(True)).all()
    for connector in connectors:
        interval=max(30,min(int((connector.config or {}).get("poll_interval_seconds",60)),3600))
        checked=connector.last_checked_at
        if checked and checked.replace(tzinfo=timezone.utc)+timedelta(seconds=interval)>now: continue
        credential=vault_service.get(db,connector.credential_id) if connector.credential_id else None
        if credential is None or credential.credential_type!="proxmox_api_token":
            connector.status="error"; connector.last_error="MissingCredential"; connector.last_checked_at=now
            db.commit(); continue
        try:
            resources=plugin.collect(connector.config or {},credential.username,credential.secret)
            node_asset_ids={}
            for resource in resources:
                if not isinstance(resource,dict) or resource.get("type") not in ("node","qemu","lxc","storage"): continue
                key=_resource_key(connector.id,resource)
                asset_id="asset_pve_"+hashlib.sha256(key.encode()).hexdigest()[:24]
                asset=db.query(AssetModel).filter(AssetModel.id==asset_id).first()
                old_state=asset.state if asset else None
                old_health=asset.health if asset else None
                state,health,severity=_state(resource); metrics=_metrics(resource); display=_display_name(resource)
                metadata={"source":"sentinel.connector.proxmox","monitoring_mode":"proxmox",
                  "proxmox_connector_id":connector.id,"proxmox_resource_key":key,
                  "proxmox_type":resource.get("type"),"proxmox_node":resource.get("node"),
                  "vmid":resource.get("vmid"),"status":resource.get("status"),
                  "last_checked_at":now.isoformat(),"health_note":"Read-only Proxmox API inventory",**metrics}
                if asset is None:
                    asset=AssetModel(id=asset_id,asset_type="proxmox_"+str(resource.get("type")),display_name=display,
                      organization_id="org_default",site_id=None,state=state,health=health,asset_metadata=metadata)
                    db.add(asset)
                else:
                    asset.display_name=display; asset.state=state; asset.health=health; asset.asset_metadata=metadata
                if resource.get("type")=="node" and resource.get("node"):
                    node_asset_ids[str(resource.get("node"))]=asset_id
                if old_state!=state or old_health!=health:
                    observation=observation_registry.add(db,ObservationCreate(type="health",severity=severity,
                      summary="Proxmox discovered "+display+" in state "+state,source="sentinel.connector.proxmox",
                      entity_id=asset_id,entity=display,value={"state":state,"health":health,**metrics},
                      raw={"resource_type":resource.get("type"),"node":resource.get("node"),"vmid":resource.get("vmid")},
                      timestamp=now),commit=False)
                    broadcasts.append(observation_registry.to_schema(observation).model_dump(mode="json"))
            for resource in resources:
                if not isinstance(resource,dict) or resource.get("type") not in ("qemu","lxc"):
                    continue
                node_id=node_asset_ids.get(str(resource.get("node") or ""))
                if not node_id:
                    continue
                key=_resource_key(connector.id,resource)
                guest_id="asset_pve_"+hashlib.sha256(key.encode()).hexdigest()[:24]
                relationship_key=node_id+":hosts:"+guest_id
                relationship_id="rel_pve_"+hashlib.sha256(relationship_key.encode()).hexdigest()[:24]
                relationship=db.query(RelationshipModel).filter(RelationshipModel.id==relationship_id).first()
                if relationship is None:
                    db.add(RelationshipModel(id=relationship_id,source_asset_id=node_id,
                        target_asset_id=guest_id,relationship_type="hosts",
                        metadata_json={"source":"sentinel.connector.proxmox","connector_id":connector.id}))
            connector.status="connected"; connector.last_error=None; connector.last_checked_at=now
        except Exception as exc:
            connector.status="error"; connector.last_error=type(exc).__name__; connector.last_checked_at=now
        db.commit()
    return broadcasts
