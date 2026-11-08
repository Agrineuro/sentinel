import os
import platform
import shutil
import socket
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.asset import AssetModel
from app.models.observation import ObservationModel
from app.schemas.observations import ObservationCreate
from app.services.observation_registry import observation_registry
from app.connectors.ssh_connector import SSHConnector
from app.connectors.http_connector import HTTPConnector
from app.connectors.icmp_connector import ICMPConnector
from app.vault.service import vault_service




def _uptime(seconds: int) -> str:
    days, remainder = divmod(max(seconds, 0), 86400)
    hours, minutes = divmod(remainder, 3600)
    minutes //= 60
    if days:
        return f"{days} days, {hours} hours"
    return f"{hours} hours, {minutes} minutes"


def _utility_metrics() -> dict:
    memory = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        memory[key] = int(value.strip().split()[0]) * 1024
    total = memory.get("MemTotal", 0)
    available = memory.get("MemAvailable", 0)
    disk = shutil.disk_usage("/")
    return {
        "hostname": platform.node(),
        "os": platform.platform(),
        "uptime_seconds": int(float(Path("/proc/uptime").read_text().split()[0])),
        "cpu_load_1m": os.getloadavg()[0],
        "cpu_count": os.cpu_count() or 1,
        "memory_total_bytes": total,
        "memory_used_percent": round((total - available) / total * 100, 1) if total else 0,
        "disk_root_used_percent": round(disk.used / disk.total * 100, 1),
    }


def _health_assessment(metadata: dict) -> tuple[str, str]:
    cpu = float(metadata.get("cpu_percent") or 0)
    memory = float(metadata.get("memory_used_percent") or 0)
    disk = float(metadata.get("disk_root_used_percent") or 0)
    if max(cpu, memory, disk) >= 95:
        return "degraded", "critical"
    if cpu >= 85 or memory >= 85 or disk >= 80:
        return "degraded", "warning"
    return "healthy", "info"


def _apply_metrics(metadata: dict, raw: dict) -> bool:
    for key in ("cpu_percent", "memory_total_gb", "memory_used_percent", "disk_root_used_percent", "uptime", "os"):
        metadata.pop(key, None)
    if "cpu_percent" in raw:
        metadata["cpu_percent"] = round(float(raw["cpu_percent"]), 1)
    elif "cpu_load_1m" in raw:
        metadata["cpu_percent"] = round(
            float(raw.get("cpu_load_1m", 0)) / max(int(raw.get("cpu_count", 1)), 1) * 100, 1
        )
    total = int(raw.get("memory_total_bytes", 0))
    if total:
        metadata["memory_total_gb"] = round(total / 1024**3, 1)
    elif "memory_total_gb" in raw:
        metadata["memory_total_gb"] = round(float(raw["memory_total_gb"]), 1)
    for key in ("memory_used_percent", "disk_root_used_percent"):
        if key in raw:
            metadata[key] = round(float(raw[key]), 1)
    if "uptime_seconds" in raw:
        metadata["uptime"] = _uptime(int(raw["uptime_seconds"]))
    if "os" in raw:
        metadata["os"] = raw["os"]
    return any(key in metadata for key in ("cpu_percent", "memory_used_percent", "disk_root_used_percent"))


def refresh_assets(db: Session) -> list[dict]:
    results = []
    assets = db.query(AssetModel).all()
    for asset in assets:
        metadata = dict(asset.asset_metadata or {})
        previous_state = asset.state
        previous_health = asset.health
        previous_severity = metadata.get("health_severity")
        address = metadata.get("ip") or metadata.get("hostname")
        mode = str(metadata.get("monitoring_mode") or "").casefold()
        metrics_available = False
        try:
            local_host = (
                mode == "local"
                or str(metadata.get("hostname") or "").casefold() == platform.node().casefold()
            )
            if local_host:
                raw = _utility_metrics()
                metrics_available = _apply_metrics(metadata, raw)
                metadata["hostname"] = raw.get("hostname")
                metadata["health_note"] = "Live local host check"
            elif mode == "http":
                url = str(metadata.get("health_url") or metadata.get("url") or "")
                result = HTTPConnector().health_check(url)
                if result["status"] != "healthy":
                    raise RuntimeError("HTTP endpoint returned an unhealthy status")
                metadata["http_status"] = result["http_status"]
                metadata["response_time_ms"] = result["response_time_ms"]
                metrics_available = _apply_metrics(metadata, result.get("metrics") or {})
                metadata["health_note"] = (
                    "Live HTTP endpoint and resource metrics"
                    if metrics_available else "Live HTTP endpoint check; no resource metrics returned"
                )
            elif mode == "icmp":
                result = ICMPConnector().health_check(str(address or ""))
                if result["status"] != "healthy":
                    raise RuntimeError("ICMP host did not respond")
                for key in ("cpu_percent", "memory_total_gb", "memory_used_percent", "disk_root_used_percent", "uptime", "os"):
                    metadata.pop(key, None)
                metadata["health_note"] = "Host responds to ping; resource metrics need an agent"
            elif metadata.get("credential_id"):
                credential = vault_service.get(db, str(metadata["credential_id"]))
                if credential is None:
                    raise RuntimeError("Stored SSH credential is unavailable")
                if not address:
                    raise RuntimeError("No host address is configured")
                raw = SSHConnector().health_metrics(
                    host=str(address),
                    username=credential.username,
                    secret=credential.secret,
                    port=int(metadata.get("port", 22)),
                    credential_type=credential.credential_type,
                )
                metrics_available = _apply_metrics(metadata, raw)
                metadata["hostname"] = raw.get("hostname")
                metadata["health_note"] = "Live SSH health check"
            elif address:
                with socket.create_connection((str(address), int(metadata.get("port", 22))), timeout=5):
                    pass
                for key in ("cpu_percent", "memory_total_gb", "memory_used_percent", "disk_root_used_percent", "uptime", "os"):
                    metadata.pop(key, None)
                metadata["health_note"] = "Host reachable; resource metrics need an SSH credential"
            else:
                continue

            asset.state = "online"
            if metrics_available:
                asset.health, health_severity = _health_assessment(metadata)
                if asset.health == "degraded":
                    metadata["health_note"] = "Live host check; resource thresholds exceeded"
            else:
                asset.health = "unknown"
                health_severity = "info"
            metadata["last_checked_at"] = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            asset.state = "offline"
            asset.health = "offline"
            health_severity = "critical"
            metadata["health_note"] = f"Health check failed: {type(exc).__name__}"
            metadata["last_checked_at"] = datetime.now(timezone.utc).isoformat()

        metadata["health_severity"] = health_severity
        asset.asset_metadata = metadata
        previous_observation = (
            db.query(ObservationModel.id)
            .filter(
                ObservationModel.entity_id == asset.id,
                ObservationModel.observation_type == "health",
            )
            .first()
        )
        created_observation = None
        if (
            previous_observation is None
            or previous_state != asset.state
            or previous_health != asset.health
            or previous_severity != health_severity
        ):
            if previous_observation is None:
                summary = f"Health baseline: {asset.display_name} is {asset.health}"
            elif asset.state == "offline":
                summary = f"{asset.display_name} is unreachable"
            elif previous_state == "offline":
                summary = f"{asset.display_name} is back online and {asset.health}"
            else:
                summary = f"{asset.display_name} health changed from {previous_health} to {asset.health}"
            observation_model = observation_registry.add(
                db,
                ObservationCreate(
                    type="health",
                    severity=health_severity,
                    summary=summary,
                    source="sentinel.health_monitor",
                    entity_id=asset.id,
                    entity=asset.display_name,
                    value={
                        "state": asset.state,
                        "health": asset.health,
                        "cpu_percent": metadata.get("cpu_percent"),
                        "memory_used_percent": metadata.get("memory_used_percent"),
                        "disk_root_used_percent": metadata.get("disk_root_used_percent"),
                    },
                    raw={"health_note": metadata.get("health_note")},
                    timestamp=datetime.now(timezone.utc),
                ),
                commit=False,
            )
            created_observation = observation_registry.to_schema(observation_model).model_dump(mode="json")
        results.append({"id": asset.id, "health": asset.health, "metadata": metadata, "observation": created_observation})

    db.commit()
    return results
