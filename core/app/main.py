import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect
from app.api.auth import router as auth_router, require_user
from app.api.core.assets import router as assets_router
from app.api.core.alerts import router as alerts_router
from app.api.core.reports import router as reports_router
from app.api.core.rules import router as rules_router
from app.api.core.connectors.ssh import router as ssh_connector_router
from app.api.core.connector_registry import router as connectors_router, ingest_router as connector_ingest_router
from app.connectors.mqtt_runtime import mqtt_runtime
from app.connectors.http_poll_runtime import http_poll_runtime
from app.connectors.websocket_runtime import websocket_runtime
from app.api.core.health import router as health_router
from app.api.core.observations import legacy_events_router, router as observations_router
from app.api.core.relationships import router as relationships_router
from app.api.core.vault import router as vault_router
from app.api.core.plugins import router as plugins_router
from app.api.core.notifications import router as notifications_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.database.session import Base, engine, SessionLocal
from app.database.migrations import apply_migrations
from app.models import asset  # noqa: F401
from app.models import credential  # noqa: F401
from app.models import relationship  # noqa: F401
from app.models import observation  # noqa: F401
from app.models import rule  # noqa: F401
from app.models import alert  # noqa: F401
from app.models import connector  # noqa: F401
from app.models import notification  # noqa: F401
from app.models.user import UserModel, UserSessionModel  # noqa: F401
from app.services.observation_hub import observation_hub
from app.services.asset_monitor import refresh_assets
from app.services.proxmox_monitor import refresh_proxmox_connectors
from app.services.notification_service import process_pending as process_notifications

configure_logging()
logger = logging.getLogger(__name__)
Base.metadata.create_all(bind=engine)
apply_migrations(engine)


def _refresh_health_once():
    db = SessionLocal()
    try:
        assets = refresh_assets(db)
        proxmox_observations = refresh_proxmox_connectors(db)
        return assets, proxmox_observations
    finally:
        db.close()


async def _health_monitor_loop():
    while True:
        try:
            systems, proxmox_observations = await asyncio.to_thread(_refresh_health_once)
            for system in systems:
                if system.get("observation"):
                    await observation_hub.broadcast(system["observation"])
            for observation in proxmox_observations:
                await observation_hub.broadcast(observation)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Scheduled asset health refresh failed")
        await asyncio.sleep(settings.health_poll_interval_seconds)



def _process_notifications_once():
    db = SessionLocal()
    try:
        return process_notifications(db)
    finally:
        db.close()


async def _notification_delivery_loop():
    while True:
        try:
            await asyncio.to_thread(_process_notifications_once)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Notification delivery worker failed")
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    mqtt_runtime.start_enabled(asyncio.get_running_loop())
    http_poll_runtime.start_enabled()
    websocket_runtime.start_enabled()
    task = asyncio.create_task(_health_monitor_loop())
    notifications_task = asyncio.create_task(_notification_delivery_loop())
    try:
        yield
    finally:
        task.cancel()
        notifications_task.cancel()
        mqtt_runtime.stop_all()
        await http_poll_runtime.stop_all()
        await websocket_runtime.stop_all()
        await asyncio.gather(task, notifications_task, return_exceptions=True)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Sentinel Core API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.192:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
protected = [observations_router, rules_router, alerts_router, reports_router,
             legacy_events_router, assets_router, relationships_router, vault_router,
             ssh_connector_router, connectors_router, plugins_router, notifications_router]
for router in protected:
    app.include_router(router, prefix=settings.api_prefix, dependencies=[Depends(require_user)])
app.include_router(connector_ingest_router, prefix=settings.api_prefix)


@app.websocket(f"{settings.api_prefix}/events/ws")
async def observation_events(websocket: WebSocket):
    from datetime import datetime
    import hashlib
    from app.models.user import UserModel, UserSessionModel

    token = websocket.cookies.get("sentinel_session", "")
    db = SessionLocal()
    session = None
    try:
        if token:
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            session = db.query(UserSessionModel).filter(
                UserSessionModel.token_hash == digest,
                UserSessionModel.expires_at > datetime.utcnow(),
            ).first()
        user = db.query(UserModel).filter(
            UserModel.id == session.user_id if session else "",
            UserModel.is_active.is_(True),
        ).first() if session else None
    finally:
        db.close()
    if user is None:
        await websocket.close(code=1008)
        return
    await observation_hub.connect(websocket, "sentinel")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        observation_hub.disconnect(websocket)
