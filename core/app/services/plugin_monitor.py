import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.asset import AssetModel
from app.models.connector import ConnectorModel
from app.plugins.registry import plugin_registry
from app.schemas.observations import ObservationCreate
from app.services.observation_registry import observation_registry
from app.vault.service import vault_service


def refresh_plugin_monitors(db: Session) -> list[dict]:
    broadcasts = []
    now = datetime.now(timezone.utc)
    for connector_type, entry in plugin_registry.iter_connectors():
        manifest = entry["manifest"]
        if manifest.get("connection_mode") != "monitoring" or connector_type == "proxmox":
            continue
        plugin = entry["plugin"]
        if not callable(getattr(plugin, "collect", None)):
            continue
        connectors = db.query(ConnectorModel).filter(
            ConnectorModel.connector_type == connector_type,
            ConnectorModel.enabled.is_(True),
        ).all()
        for connector in connectors:
            interval = max(15, min(int((connector.config or {}).get("poll_interval_seconds", 60)), 3600))
            checked = connector.last_checked_at
            if checked and checked.replace(tzinfo=timezone.utc) + timedelta(seconds=interval) > now:
                continue
            credential_spec = manifest.get("credentials", {})
            credential = vault_service.get(db, connector.credential_id) if connector.credential_id else None
            if credential_spec.get("required") and credential is None:
                connector.status = "error"
                connector.last_error = "MissingCredential"
                connector.last_checked_at = now
                db.commit()
                continue
            try:
                if credential and credential.credential_type != credential_spec.get("credential_type"):
                    raise ValueError("InvalidCredentialType")
                rows = plugin.collect(
                    connector.config or {},
                    credential.username if credential else None,
                    credential.secret if credential else None,
                )
                if not isinstance(rows, list) or len(rows) > 1000:
                    raise ValueError("InvalidPluginInventory")
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    identity = str(row.get("identity") or "").strip()
                    if not identity or len(identity) > 500:
                        continue
                    asset_id = "asset_plugin_" + hashlib.sha256((connector.id + ":" + identity).encode()).hexdigest()[:24]
                    asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                    old_state = asset.state if asset else None
                    old_health = asset.health if asset else None
                    state = str(row.get("state") or "observed")[:64]
                    health = str(row.get("health") or "unknown")[:32]
                    name = str(row.get("name") or identity)[:200]
                    metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
                    labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
                    metadata = {
                        "source": "sentinel.plugin." + manifest["id"],
                        "monitoring_mode": "plugin",
                        "plugin_id": manifest["id"],
                        "connector_id": connector.id,
                        "identity": identity,
                        "last_checked_at": now.isoformat(),
                        "metrics": metrics,
                        "labels": labels,
                    }
                    if asset is None:
                        asset = AssetModel(
                            id=asset_id, asset_type=str(row.get("asset_type") or "plugin_" + connector_type)[:80],
                            display_name=name, organization_id="org_default", site_id=None,
                            state=state, health=health, asset_metadata=metadata,
                        )
                        db.add(asset)
                    else:
                        asset.display_name = name
                        asset.state = state
                        asset.health = health
                        asset.asset_metadata = metadata
                    if old_state != state or old_health != health:
                        severity = "critical" if health in {"critical", "offline", "unhealthy"} else "warning" if health in {"degraded", "warning"} else "info"
                        observation = observation_registry.add(db, ObservationCreate(
                            type="health", severity=severity,
                            summary=manifest["name"] + " reports " + state + " for " + name,
                            source="sentinel.plugin." + manifest["id"],
                            entity_id=asset_id, entity=name,
                            value={"state": state, "health": health, **metrics},
                            raw={"identity": identity, "labels": labels},
                            timestamp=now,
                        ), commit=False)
                        broadcasts.append(observation_registry.to_schema(observation).model_dump(mode="json"))
                connector.status = "connected"
                connector.last_error = None
                connector.last_checked_at = now
            except Exception as exc:
                connector.status = "error"
                connector.last_error = type(exc).__name__
                connector.last_checked_at = now
            db.commit()
    return broadcasts
