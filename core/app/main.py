from fastapi import FastAPI

from app.api.core.assets import router as assets_router
from app.api.core.health import router as health_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.database.session import Base, engine
from app.models import asset  # noqa: F401
from app.api.core.connectors.ssh import router as ssh_connector_router

configure_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Sentinel Core API",
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(assets_router, prefix=settings.api_prefix)
app.include_router(ssh_connector_router, prefix=settings.api_prefix)
