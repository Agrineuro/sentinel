import os
import platform
import shutil
import time
from fastapi import APIRouter
from sqlalchemy import text
from app.database.session import engine
from app.core.config import settings

router = APIRouter(tags=["health"])
_STARTED = time.monotonic()


def _memory():
    values = {}
    try:
        for line in open("/proc/meminfo", encoding="utf-8"):
            key, value = line.split(":", 1)
            values[key] = int(value.strip().split()[0]) * 1024
        total = values.get("MemTotal", 0)
        available = values.get("MemAvailable", 0)
        return round((total - available) / total * 100, 1) if total else 0
    except (OSError, ValueError):
        return 0


@router.get("/health")
async def health_check():
    disk = shutil.disk_usage("/")
    load = os.getloadavg()[0] if hasattr(os, "getloadavg") else 0
    cpu = round(min(load / max(os.cpu_count() or 1, 1) * 100, 100), 1)
    mem = _memory()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception:
        database_status = "unavailable"
    auth_ready = settings.environment.casefold() != "production" or bool(settings.api_key)
    return {
        "status": "healthy" if database_status == "healthy" and auth_ready else "degraded",
        "service": "sentinel-backend",
        "database": database_status,
        "authentication_required": bool(settings.api_key) or settings.environment.casefold() == "production",
        "version": "0.1.0",
        "hostname": platform.node(),
        "cpu_percent": cpu,
        "memory_percent": mem,
        "disk_percent": round(disk.used / disk.total * 100, 1),
        "uptime_seconds": int(float(open("/proc/uptime", encoding="utf-8").read().split()[0])),
    }
