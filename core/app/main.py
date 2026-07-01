from fastapi import FastAPI

from app.api.core.assets import router as assets_router
from app.api.core.health import router as health_router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Sentinel backend API",
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(assets_router, prefix=settings.api_prefix)
