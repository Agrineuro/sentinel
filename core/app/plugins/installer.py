import hashlib
import json
import os
import re
import shutil
import ssl
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException
from app.core.config import settings
from app.plugins.registry import plugin_registry

CATALOG_URL = "https://raw.githubusercontent.com/Agrineuro/sentinel/master/plugins/catalog.json"
RAW_ROOT = "https://raw.githubusercontent.com/Agrineuro/sentinel/master/"
MAX_FILE_BYTES = 1_048_576
ALLOWED_FILES = {"manifest.json", "plugin.py", "__init__.py"}
PLUGIN_ID = re.compile(r"[a-z0-9][a-z0-9_.-]{2,100}\Z")
SOURCE_PATH = re.compile(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\Z")


def _fetch(url: str, limit: int) -> bytes:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "Sentinel-Plugin-Manager/1"})
    try:
        with urlopen(request, timeout=12, context=ssl.create_default_context()) as response:
            if response.status != 200:
                raise HTTPException(status_code=502, detail="GitHub did not return the requested plugin file")
            body = response.read(limit + 1)
    except HTTPException:
        raise
    except (HTTPError, URLError, TimeoutError, ssl.SSLError) as exc:
        raise HTTPException(status_code=502, detail="Could not download the plugin from GitHub") from exc
    if len(body) > limit:
        raise HTTPException(status_code=413, detail="Plugin file exceeds the 1 MiB safety limit")
    return body


def _catalog_entry(plugin_id: str) -> dict:
    if not PLUGIN_ID.fullmatch(plugin_id):
        raise HTTPException(status_code=422, detail="Invalid plugin id")
    try:
        catalog = json.loads(_fetch(CATALOG_URL, 1_048_576).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail="GitHub returned an invalid plugin catalog") from exc
    if not isinstance(catalog, dict) or catalog.get("schema_version") != 1 or not isinstance(catalog.get("plugins"), list):
        raise HTTPException(status_code=502, detail="GitHub plugin catalog has an unsupported format")
    entry = next((item for item in catalog["plugins"] if isinstance(item, dict) and item.get("id") == plugin_id), None)
    if not entry or entry.get("status") != "available":
        raise HTTPException(status_code=404, detail="This plugin is not marked available in the official catalog")
    source_path = entry.get("source_path")
    hashes = entry.get("install_files")
    if not isinstance(source_path, str) or not SOURCE_PATH.fullmatch(source_path) or any(part in {"", ".", ".."} for part in source_path.split("/")):
        raise HTTPException(status_code=422, detail="Plugin source path is not valid")
    if not isinstance(hashes, dict) or not {"manifest.json", "plugin.py"}.issubset(hashes):
        raise HTTPException(status_code=422, detail="Plugin catalog entry has no verifiable package files")
    if any(name not in ALLOWED_FILES or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest) for name, digest in hashes.items()):
        raise HTTPException(status_code=422, detail="Plugin catalog contains invalid file checksums")
    return entry


def install_plugin(plugin_id: str) -> dict:
    entry = _catalog_entry(plugin_id)
    files: dict[str, bytes] = {}
    for name, expected_hash in entry["install_files"].items():
        url = RAW_ROOT + entry["source_path"] + "/" + name
        body = _fetch(url, MAX_FILE_BYTES)
        if not hashlib.sha256(body).hexdigest() == expected_hash:
            raise HTTPException(status_code=502, detail="Plugin file checksum does not match the official catalog")
        files[name] = body
    try:
        manifest = json.loads(files["manifest.json"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail="Plugin package has an invalid manifest") from exc
    if manifest.get("id") != plugin_id or manifest.get("connector_type") != entry.get("connector_type"):
        raise HTTPException(status_code=422, detail="Plugin manifest does not match the catalog entry")
    if manifest.get("module", "plugin.py") != "plugin.py":
        raise HTTPException(status_code=422, detail="Only plugin.py packages are supported by the installer")
    if b"create_plugin" not in files["plugin.py"]:
        raise HTTPException(status_code=422, detail="Plugin module does not expose the required factory")

    plugin_root = Path(settings.plugin_dir).resolve()
    plugin_root.mkdir(parents=True, exist_ok=True)
    destination = (plugin_root / plugin_id).resolve()
    if destination.parent != plugin_root:
        raise HTTPException(status_code=422, detail="Plugin destination is invalid")
    stage = Path(tempfile.mkdtemp(prefix=".install-", dir=plugin_root))
    backup = plugin_root / (".backup-" + plugin_id)
    try:
        for name, body in files.items():
            target = stage / name
            target.write_bytes(body)
            target.chmod(0o640)
        if backup.exists():
            shutil.rmtree(backup)
        if destination.exists():
            os.replace(destination, backup)
        os.replace(stage, destination)
        plugin_registry.reload()
        loaded = next((item for item in plugin_registry.list_plugins() if item["id"] == plugin_id), None)
        if loaded is None:
            raise HTTPException(status_code=422, detail="Plugin was downloaded but Core could not load it")
        if backup.exists():
            shutil.rmtree(backup)
        return loaded
    except Exception:
        if destination.exists():
            shutil.rmtree(destination)
        if backup.exists():
            os.replace(backup, destination)
        plugin_registry.reload()
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)
