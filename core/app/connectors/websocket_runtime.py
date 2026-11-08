import asyncio
import json
import logging
from datetime import datetime, timezone

from websockets.asyncio.client import connect

from app.database.session import SessionLocal
from app.models.connector import ConnectorModel
from app.services.event_translation import translate_payload
from app.services.observation_hub import observation_hub
from app.services.observation_registry import observation_registry
from app.vault.service import vault_service

logger = logging.getLogger(__name__)
MAX_MESSAGE_BYTES = 1_048_576


def _headers(config: dict, credential) -> dict[str, str]:
    if config.get("auth_type") == "bearer" and credential:
        return {"Authorization": "Bearer " + credential.secret}
    return {}


def _rows(document):
    if isinstance(document, list):
        values = document
    elif isinstance(document, dict):
        values = next((document[key] for key in ("events", "items", "results")
                       if isinstance(document.get(key), list)), None)
        if values is None and isinstance(document.get("data"), list):
            values = document["data"]
        if values is None:
            values = [document]
    else:
        values = [{"value": document}]
    return [value if isinstance(value, dict) else {"value": value} for value in values[:500]]


def _load(connector_id: str):
    db = SessionLocal()
    try:
        model = db.query(ConnectorModel).filter(ConnectorModel.id == connector_id).first()
        if model is None or not model.enabled:
            return None
        config = dict(model.config or {})
        credential = vault_service.get(db, model.credential_id) if model.credential_id else None
        return config, credential
    finally:
        db.close()


def _status(connector_id: str, status: str, error: str | None = None):
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
        logger.exception("Could not update WebSocket connector status")
    finally:
        db.close()


def _ingest(connector_id: str, payload: dict):
    db = SessionLocal()
    try:
        model = db.query(ConnectorModel).filter(ConnectorModel.id == connector_id).first()
        if model is None or not model.enabled:
            return None
        translation = (model.config or {}).get("translation") or {}
        canonical = translate_payload(payload, model.name, translation.get("field_map") or {})
        from app.schemas.observations import ObservationCreate
        observation = observation_registry.add(db, ObservationCreate(**canonical.model_dump()))
        result = observation_registry.to_schema(observation).model_dump(mode="json")
        db.commit()
        return result
    except Exception:
        db.rollback()
        logger.exception("Could not translate WebSocket event for connector %s", connector_id)
        return None
    finally:
        db.close()


class WebSocketConnectorRuntime:
    def __init__(self):
        self.tasks: dict[str, asyncio.Task] = {}

    def start_enabled(self):
        db = SessionLocal()
        try:
            ids = [row.id for row in db.query(ConnectorModel).filter(
                ConnectorModel.connector_type == "websocket",
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
        async with connect(
            config["url"],
            additional_headers=_headers(config, credential),
            open_timeout=10,
            max_size=MAX_MESSAGE_BYTES,
        ):
            pass
        return round((asyncio.get_running_loop().time() - started) * 1000, 1)

    async def _run(self, connector_id: str):
        delay = 1
        while True:
            try:
                loaded = await asyncio.to_thread(_load, connector_id)
                if loaded is None:
                    return
                config, credential = loaded
                async with connect(
                    config["url"],
                    additional_headers=_headers(config, credential),
                    open_timeout=10,
                    max_size=MAX_MESSAGE_BYTES,
                    ping_interval=20,
                    ping_timeout=20,
                ) as socket:
                    delay = 1
                    _status(connector_id, "connected")
                    async for message in socket:
                        if isinstance(message, bytes):
                            message = message.decode("utf-8")
                        try:
                            document = json.loads(message)
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            _status(connector_id, "error", "InvalidJSON")
                            continue
                        _status(connector_id, "connected")
                        for payload in _rows(document):
                            observation = await asyncio.to_thread(_ingest, connector_id, payload)
                            if observation:
                                await observation_hub.broadcast(observation)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                _status(connector_id, "reconnecting", type(exc).__name__)
                logger.warning("WebSocket connector %s reconnecting after %s", connector_id, type(exc).__name__)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)


websocket_runtime = WebSocketConnectorRuntime()
