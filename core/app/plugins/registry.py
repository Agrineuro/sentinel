import importlib.util
import json
import logging
import re
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

class PluginRegistry:
    def __init__(self):
        self._plugins = {}
        self.reload()

    def reload(self):
        plugins = {}
        for root in (Path(__file__).parent / "builtins", Path(settings.plugin_dir)):
            if not root.exists():
                continue
            for manifest_path in sorted(root.glob("*/manifest.json")):
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    plugin_id = manifest.get("id")
                    module_path = manifest_path.parent / manifest.get("module", "plugin.py")
                    if not isinstance(plugin_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,100}", plugin_id):
                        raise ValueError("Invalid plugin id")
                    if not module_path.is_file() or module_path.resolve().parent != manifest_path.parent.resolve():
                        raise ValueError("Plugin module must be in its plugin directory")
                    module_name = "sentinel_plugin_" + re.sub(r"[^a-zA-Z0-9_]", "_", plugin_id)
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if spec is None or spec.loader is None:
                        raise ValueError("Could not create plugin loader")
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    factory = getattr(module, "create_plugin", None)
                    if not callable(factory):
                        raise ValueError("Plugin must expose create_plugin()")
                    plugin = factory()
                    connector_type = manifest.get("connector_type")
                    if not isinstance(connector_type, str):
                        raise ValueError("Connector plugin is missing connector_type")
                    plugins[connector_type] = {"manifest": manifest, "plugin": plugin, "path": str(manifest_path.parent)}
                except Exception:
                    logger.exception("Could not load connector plugin at %s", manifest_path)
        self._plugins = plugins

    def get_connector(self, connector_type: str):
        row = self._plugins.get(connector_type)
        return row["plugin"] if row else None

    def list_plugins(self):
        result = []
        for row in self._plugins.values():
            manifest = row["manifest"]
            result.append({
                "id": manifest["id"], "name": manifest["name"], "version": manifest["version"],
                "connector_type": manifest["connector_type"], "description": manifest.get("description", ""),
                "capabilities": manifest.get("capabilities", []), "permissions": manifest.get("permissions", []),
                "status": "loaded",
            })
        return sorted(result, key=lambda item: item["name"].casefold())

plugin_registry = PluginRegistry()
