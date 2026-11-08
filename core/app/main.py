import asyncio
import logging
import hmac
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect
from app.api.auth import require_api_key
from app.api.core.assets import router as assets_router
from app.api.core.alerts import router as alerts_router
from app.api.core.reports import router as reports_router
from app.api.core.rules import router as rules_router
from app.api.core.connectors.ssh import router as ssh_connector_router
from app.api.core.connector_registry import router as connectors_router, ingest_router as connector_ingest_router
from app.connectors.mqtt_runtime import mqtt_runtime
from app.api.core.health import router as health_router
from app.api.core.observations import legacy_events_router, router as observations_router
from app.api.core.relationships import router as relationships_router
from app.api.core.vault import router as vault_router
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
from app.services.observation_hub import observation_hub
from app.services.asset_monitor import refresh_assets

configure_logging()
logger = logging.getLogger(__name__)
Base.metadata.create_all(bind=engine)
apply_migrations(engine)


def _refresh_health_once():
    db = SessionLocal()
    try:
        return refresh_assets(db)
    finally:
        db.close()


async def _health_monitor_loop():
    while True:
        try:
            systems = await asyncio.to_thread(_refresh_health_once)
            for system in systems:
                if system.get("observation"):
                    await observation_hub.broadcast(system["observation"])
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Scheduled asset health refresh failed")
        await asyncio.sleep(settings.health_poll_interval_seconds)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    mqtt_runtime.start_enabled(asyncio.get_running_loop())
    task = asyncio.create_task(_health_monitor_loop())
    try:
        yield
    finally:
        task.cancel()
        mqtt_runtime.stop_all()
        await asyncio.gather(task, return_exceptions=True)


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
protected = [observations_router, rules_router, alerts_router, reports_router,
             legacy_events_router, assets_router, relationships_router, vault_router,
             ssh_connector_router, connectors_router]
for router in protected:
    app.include_router(router, prefix=settings.api_prefix, dependencies=[Depends(require_api_key)])
app.include_router(connector_ingest_router, prefix=settings.api_prefix)


@app.websocket(f"{settings.api_prefix}/events/ws")
async def observation_events(websocket: WebSocket):
    protocols = [value.strip() for value in websocket.headers.get("sec-websocket-protocol", "").split(",")]
    token = next((value[len("token."):] for value in protocols if value.startswith("token.")), None)
    if settings.api_key and (
        not token or not hmac.compare_digest(token, settings.api_key)
    ):
        await websocket.close(code=1008)
        return
    if settings.environment.casefold() == "production" and not settings.api_key:
        await websocket.close(code=1011)
        return
    await observation_hub.connect(websocket, 'sentinel' if 'sentinel' in protocols else None)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        observation_hub.disconnect(websocket)
