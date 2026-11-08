import asyncio
import json
import logging
import threading
from datetime import datetime, timezone
from app.database.session import SessionLocal
from app.models.connector import ConnectorModel
from app.schemas.observations import ObservationCreate
from app.services.observation_hub import observation_hub
from app.services.observation_registry import observation_registry
from app.vault.service import vault_service

logger = logging.getLogger(__name__)

def _ingest(connector_id: str, payload: dict):
    db = SessionLocal()
    try:
        connector = db.query(ConnectorModel).filter(ConnectorModel.id == connector_id).first()
        if connector is None or not connector.enabled:
            return None
        from app.services.connector_ingest import ingest_connector_payload
        result = ingest_connector_payload(db, connector, payload)
        db.commit()
        return result
    except Exception:
        db.rollback()
        logger.exception("Could not ingest MQTT observation for connector %s", connector_id)
        return None
    finally:
        db.close()

class MQTTConnectorRuntime:
    def __init__(self):
        self.clients = {}
        self.loop = None
        self.lock = threading.RLock()

    def start_enabled(self, loop):
        self.loop = loop
        db = SessionLocal()
        try:
            ids = [row.id for row in db.query(ConnectorModel).filter(
                ConnectorModel.connector_type == "mqtt", ConnectorModel.enabled.is_(True)
            ).all()]
        finally:
            db.close()
        for connector_id in ids:
            self.start(connector_id, loop)

    def start(self, connector_id: str, loop=None):
        from paho.mqtt import client as mqtt
        current_loop = loop or self.loop
        self.stop(connector_id)
        db = SessionLocal()
        try:
            row = db.query(ConnectorModel).filter(ConnectorModel.id == connector_id).first()
            if row is None or row.connector_type != "mqtt" or not row.enabled:
                return
            config = dict(row.config or {})
            credential = vault_service.get(db, row.credential_id) if row.credential_id else None
        finally:
            db.close()
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=config.get("client_id", "sentinel-" + connector_id[-12:]),
        )
        if credential:
            client.username_pw_set(credential.username, credential.secret)
        if config.get("tls"):
            client.tls_set()

        def set_status(status: str, error: str | None = None):
            session = SessionLocal()
            try:
                model = session.query(ConnectorModel).filter(ConnectorModel.id == connector_id).first()
                if model:
                    model.status = status
                    model.last_error = error
                    model.last_checked_at = datetime.now(timezone.utc)
                    session.commit()
            except Exception:
                session.rollback()
                logger.exception("Could not update MQTT connector state")
            finally:
                session.close()

        def on_connect(mqtt_client, userdata, flags, reason_code, properties):
            if int(reason_code) == 0:
                mqtt_client.subscribe(config["topic"], qos=config.get("qos", 0))
                set_status("connected")
            else:
                set_status("error", "MQTT broker rejected the connection")

        def on_disconnect(mqtt_client, userdata, disconnect_flags, reason_code, properties):
            if int(reason_code) != 0:
                set_status("reconnecting", "MQTT connection interrupted")

        def on_message(mqtt_client, userdata, message):
            try:
                if len(message.payload) > 1_048_576:
                    logger.warning("Rejected oversized MQTT payload for connector %s", connector_id)
                    return
                payload = json.loads(message.payload.decode("utf-8"))
                if not isinstance(payload, dict):
                    payload = {"data": payload, "summary": "MQTT message on " + message.topic}
                payload.setdefault("type", "mqtt.message")
                payload.setdefault("summary", "MQTT message on " + message.topic)
                payload.setdefault("value", payload.get("data"))
                result = _ingest(connector_id, payload)
                if result and current_loop and current_loop.is_running():
                    asyncio.run_coroutine_threadsafe(observation_hub.broadcast(result), current_loop)
            except (UnicodeDecodeError, json.JSONDecodeError):
                _ingest(connector_id, {"type": "mqtt.message", "summary": "MQTT message on " + message.topic,
                                       "value": message.payload[:4096].decode("utf-8", errors="replace")})
            except Exception:
                logger.exception("Could not process MQTT message for connector %s", connector_id)

        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message
        try:
            client.connect_async(config["host"], config["port"], keepalive=30)
            client.loop_start()
            with self.lock:
                self.clients[connector_id] = client
        except Exception as exc:
            set_status("error", type(exc).__name__)
            logger.exception("Could not start MQTT connector %s", connector_id)

    def stop(self, connector_id: str):
        with self.lock:
            client = self.clients.pop(connector_id, None)
        if client:
            try:
                client.disconnect()
                client.loop_stop()
            except Exception:
                logger.exception("Could not stop MQTT connector %s", connector_id)

    def stop_all(self):
        with self.lock:
            ids = list(self.clients)
        for connector_id in ids:
            self.stop(connector_id)

    def test(self, host: str, port: int, tls: bool, username: str | None, password: str | None, timeout: float = 5):
        from paho.mqtt import client as mqtt
        connected = threading.Event()
        result = {"reason": None}
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="sentinel-test")
        if username and password:
            client.username_pw_set(username, password)
        if tls:
            client.tls_set()
        def on_connect(client, userdata, flags, reason_code, properties):
            result["reason"] = int(reason_code)
            connected.set()
        client.on_connect = on_connect
        try:
            client.connect(host, port, keepalive=10)
            client.loop_start()
            if not connected.wait(timeout):
                raise TimeoutError("Timed out waiting for MQTT broker")
            if result["reason"] != 0:
                raise ConnectionError("MQTT broker rejected the connection")
        finally:
            try:
                client.disconnect()
                client.loop_stop()
            except Exception:
                pass

mqtt_runtime = MQTTConnectorRuntime()
