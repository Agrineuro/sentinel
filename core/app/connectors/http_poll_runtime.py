import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.database.session import SessionLocal
from app.models.connector import ConnectorModel
from app.services.event_translation import translate_payload
from app.services.observation_hub import observation_hub
from app.services.observation_registry import observation_registry
from app.vault.service import vault_service

logger = logging.getLogger(__name__)
MAX_RESPONSE_BYTES = 1_048_576
MAX_EVENTS_PER_POLL = 500


def _headers(config: dict, credential) -> dict[str, str]:
    headers = {"Accept": "application/json", "User-Agent": "Sentinel/0.1"}
    auth_type = config.get("auth_type", "none")
    if auth_type == "bearer" and credential:
        headers["Authorization"] = "Bearer " + credential.secret
    elif auth_type == "basic" and credential:
        import base64
        raw = (credential.username + ":" + credential.secret).encode()
        headers["Authorization"] = "Basic " + base64.b64encode(raw).decode("ascii")
    return headers


def _events(document):
    if isinstance(document, list):
        rows = document
    elif isinstance(document, dict):
        rows = next((document[key] for key in ("events", "items", "results")
                     if isinstance(document.get(key), list)), None)
        if rows is None and isinstance(document.get("data"), list):
            rows = document["data"]
        if rows is None:
            rows = [document]
    else:
        rows = [{"value": document}]
    return [row if isinstance(row, dict) else {"value": row} for row in rows[:MAX_EVENTS_PER_POLL]]


def _poll_once(connector_id: str):
    db = SessionLocal()
    try:
        model = db.query(ConnectorModel).filter(ConnectorModel.id == connector_id).first()
        if model is None or not model.enabled:
            return None, []
        config = dict(model.config or {})
        url = config.get("url", "")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Invalid HTTP connector URL")
        credential = vault_service.get(db, model.credential_id) if model.credential_id else None
        request = Request(url, headers=_headers(config, credential), method="GET")
        with urlopen(request, timeout=int(config.get("timeout_seconds", 10))) as response:
            if not 200 <= int(response.status) < 300:
                raise RuntimeError("HTTP endpoint returned an unsuccessful status")
            body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ValueError("HTTP response exceeds 1 MiB")
        try:
            document = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("HTTP endpoint did not return valid JSON") from exc

        runtime = dict(config.get("_runtime") or {})
        known = set(runtime.get("recent_fingerprints") or [])
        next_known = []
        observations = []
        field_map = (config.get("translation") or {}).get("field_map") or {}
        for item in _events(document):
            fingerprint = hashlib.sha256(
                json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            ).hexdigest()
            next_known.append(fingerprint)
            if fingerprint in known:
                continue
            canonical = translate_payload(item, model.name, field_map)
            observation = observation_registry.add(db, canonical_to_observation(canonical), commit=False)
            observations.append(observation_registry.to_schema(observation).model_dump(mode="json"))
        # Keep a bounded sliding set so repeated API snapshots do not re-emit old rows.
        config["_runtime"] = {"recent_fingerprints": next_known[-1000:]}
        model.config = config
        model.status = "connected"
        model.last_error = None
        model.last_checked_at = datetime.now(timezone.utc)
        db.commit()
        return int(config.get("poll_interval_seconds", 60)), observations
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def canonical_to_observation(canonical):
    from app.schemas.observations import ObservationCreate
    return ObservationCreate(**canonical.model_dump())


def _set_status(connector_id: str, status: str, error: str | None = None):
    db = SessionLocal()
    try:
        model = db.query(ConnectorModel).filter(ConnectorModel.id == connector_id).first()
        if model:
            model.status = status
            model.last_error = error
            model.last_checked_at = datetime.now(timezone.utc)
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not update HTTP connector state")
    finally:
        db.close()


class HTTPPollRuntime:
    def __init__(self):
        self.tasks: dict[str, asyncio.Task] = {}

    def start_enabled(self):
        db = SessionLocal()
        try:
            ids = [row.id for row in db.query(ConnectorModel).filter(
                ConnectorModel.connector_type == "http_poll",
                ConnectorModel.enabled.is_(True),
            ).all()]
        finally:
            db.close()
        for connector_id in ids:
            self.start(connector_id)

    def start(self, connector_id: str):
        self.stop(connector_id)
        self.tasks[connector_id] = asyncio.create_task(self._run(connector_id))

    def stop(self, connector_id: str):
        task = self.tasks.pop(connector_id, None)
        if task:
            task.cancel()

    async def stop_all(self):
        tasks = list(self.tasks.values())
        self.tasks.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def test(self, config: dict, credential) -> float:
        started = asyncio.get_running_loop().time()
        url = config["url"]
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Invalid HTTP connector URL")
        request = Request(url, headers=_headers(config, credential), method="GET")
        def fetch():
            with urlopen(request, timeout=int(config.get("timeout_seconds", 10))) as response:
                if not 200 <= int(response.status) < 300:
                    raise RuntimeError("HTTP endpoint returned an unsuccessful status")
                body = response.read(MAX_RESPONSE_BYTES + 1)
                if len(body) > MAX_RESPONSE_BYTES:
                    raise ValueError("HTTP response exceeds 1 MiB")
                json.loads(body.decode("utf-8"))
        await asyncio.to_thread(fetch)
        return round((asyncio.get_running_loop().time() - started) * 1000, 1)

    async def _run(self, connector_id: str):
        while True:
            try:
                interval, observations = await asyncio.to_thread(_poll_once, connector_id)
                if interval is None:
                    return
                _set_status(connector_id, "connected")
                for observation in observations:
                    await observation_hub.broadcast(observation)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                _set_status(connector_id, "error", type(exc).__name__)
                logger.warning("HTTP connector %s poll failed: %s", connector_id, type(exc).__name__)
                db = SessionLocal()
                try:
                    model = db.query(ConnectorModel).filter(ConnectorModel.id == connector_id).first()
                    interval = int((model.config or {}).get("poll_interval_seconds", 60)) if model else 60
                    enabled = bool(model and model.enabled)
                finally:
                    db.close()
                if not enabled:
                    return
                await asyncio.sleep(interval)


http_poll_runtime = HTTPPollRuntime()
