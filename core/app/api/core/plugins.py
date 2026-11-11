from fastapi import APIRouter, Depends
from app.api.auth import require_admin
from app.models.user import UserModel
from app.plugins.installer import install_plugin
from app.plugins.registry import plugin_registry

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("")
async def list_plugins():
    return {"plugins": plugin_registry.list_plugins()}


@router.post("/{plugin_id}/install")
def install_or_update_plugin(plugin_id: str, _admin: UserModel = Depends(require_admin)):
    plugin = install_plugin(plugin_id)
    return {"plugin": plugin, "message": "Plugin installed or updated. It is now active in Core."}
