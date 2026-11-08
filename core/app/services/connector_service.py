import hashlib
import secrets
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.connector import ConnectorModel
from app.schemas.connectors import ConnectorCreate, ConnectorRead, ConnectorUpdate
from app.schemas.vault import CredentialCreate
from app.vault.service import vault_service

class ConnectorService:
    def list(self, db: Session) -> list[ConnectorRead]:
        rows = db.query(ConnectorModel).order_by(ConnectorModel.name.asc()).all()
        return [self.to_schema(row) for row in rows]

    def get(self, db: Session, connector_id: str) -> ConnectorModel | None:
        return db.query(ConnectorModel).filter(ConnectorModel.id == connector_id).first()

    def create(self, db: Session, payload: ConnectorCreate) -> tuple[ConnectorModel, str | None]:
        credential_id = None
        if payload.connector_type == "mqtt" and payload.username and payload.password:
            credential = vault_service.create_credential(
                db,
                CredentialCreate(name=payload.name + " MQTT credentials", username=payload.username,
                                 password=payload.password, credential_type="mqtt_password"),
            )
            credential_id = credential.id
        elif payload.connector_type in {"http_poll", "websocket"} and payload.config.get("auth_type") in {"basic", "bearer"}:
            auth_type = str(payload.config["auth_type"])
            credential = vault_service.create_credential(
                db,
                CredentialCreate(
                    name=payload.name + " " + ("WebSocket" if payload.connector_type == "websocket" else "HTTP") + " credentials",
                    username=payload.username or "token",
                    password=payload.password or "",
                    credential_type=("http_" if payload.connector_type == "http_poll" else "websocket_") + auth_type,
                ),
            )
            credential_id = credential.id
        token = secrets.token_urlsafe(32) if payload.connector_type == "webhook" else None
        config = {}
        translation = payload.config.get("translation") or {}
        config = {"translation": {"field_map": dict(translation.get("field_map") or {})}} if translation.get("field_map") else {}
        if payload.connector_type == "websocket":
            config.update({"url": str(payload.config["url"]).strip(),
                           "auth_type": str(payload.config.get("auth_type", "none"))})
        if payload.connector_type == "http_poll":
            config.update({
                "url": str(payload.config["url"]).strip(),
                "poll_interval_seconds": int(payload.config.get("poll_interval_seconds", 60)),
                "timeout_seconds": int(payload.config.get("timeout_seconds", 10)),
                "auth_type": str(payload.config.get("auth_type", "none")),
            })
        if payload.connector_type == "mqtt":
            config.update({
                "host": str(payload.config["host"]).strip(),
                "port": int(payload.config.get("port", 1883)),
                "topic": str(payload.config["topic"]).strip(),
                "qos": int(payload.config.get("qos", 0)),
                "tls": bool(payload.config.get("tls", False)),
                "client_id": str(payload.config.get("client_id") or ("sentinel-" + uuid4().hex[:12])),
            })
        model = ConnectorModel(
            id="conn_" + uuid4().hex,
            name=payload.name.strip(),
            connector_type=payload.connector_type,
            direction="inbound",
            enabled=payload.enabled,
            status=("starting" if payload.enabled and payload.connector_type in {"mqtt", "http_poll", "websocket"}
                    else "ready" if payload.enabled else "disabled"),
            config=config,
            credential_id=credential_id,
            webhook_token_hash=hashlib.sha256(token.encode()).hexdigest() if token else None,
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model, token

    def update(self, db: Session, model: ConnectorModel, payload: ConnectorUpdate) -> ConnectorModel:
        if payload.name is not None:
            model.name = payload.name.strip()
        if payload.enabled is not None:
            model.enabled = payload.enabled
            if not payload.enabled:
                model.status = "disabled"
                model.last_error = None
            elif model.connector_type == "webhook":
                model.status = "ready"
                model.last_error = None
            else:
                model.status = "starting"
        if "translation_field_map" in payload.model_fields_set:
            config = dict(model.config or {})
            config["translation"] = {"field_map": payload.translation_field_map or {}}
            model.config = config
        model.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(model)
        return model

    def to_schema(self, model: ConnectorModel) -> ConnectorRead:
        return ConnectorRead(
            id=model.id, name=model.name, connector_type=model.connector_type,
            direction=model.direction, enabled=model.enabled, status=model.status,
            config={key: value for key, value in (model.config or {}).items() if key != "_runtime"}, credential_id=model.credential_id,
            last_checked_at=model.last_checked_at, last_error=model.last_error,
            created_at=model.created_at, updated_at=model.updated_at,
            ingest_path=("/connectors/ingest/" + model.id) if model.connector_type == "webhook" else None,
        )

connector_service = ConnectorService()
