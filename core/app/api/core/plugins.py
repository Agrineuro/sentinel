from fastapi import APIRouter
from app.plugins.registry import plugin_registry
router = APIRouter(prefix="/plugins",tags=["plugins"])
@router.get("")
async def list_plugins():
    return {"plugins":plugin_registry.list_plugins()}
