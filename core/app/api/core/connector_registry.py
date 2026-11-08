import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from app.connectors.mqtt_runtime import mqtt_runtime
from app.connectors.http_poll_runtime import http_poll_runtime
from app.connectors.websocket_runtime import websocket_runtime
from app.database.session import get_db
from app.models.connector import ConnectorModel
from app.schemas.connectors import ConnectorCreate, ConnectorCreated, ConnectorRead, ConnectorTestResult, ConnectorUpdate
from app.services.connector_ingest import broadcast_ingested, ingest_connector_payload
from app.services.connector_service import connector_service
from app.vault.service import vault_service

router = APIRouter(prefix="/connectors", tags=["connectors"])
ingest_router = APIRouter(prefix="/connectors/ingest", tags=["connector-ingest"])

@router.get("", response_model=list[ConnectorRead])
async def list_connectors(db: Session = Depends(get_db)):
    return connector_service.list(db)

@router.post("", response_model=ConnectorCreated)
async def create_connector(payload: ConnectorCreate, db: Session = Depends(get_db)):
    try:
        model, webhook_token = connector_service.create(db, payload)
    except Exception:
        db.rollback()
        raise
    if model.enabled and model.connector_type == "mqtt":
        mqtt_runtime.start(model.id, asyncio.get_running_loop())
    elif model.enabled and model.connector_type == "http_poll":
        http_poll_runtime.start(model.id)
    elif model.enabled and model.connector_type == "websocket":
        websocket_runtime.start(model.id)
    result = connector_service.to_schema(model).model_dump()
    result["webhook_token"] = webhook_token
    return result

@router.patch("/{connector_id}", response_model=ConnectorRead)
async def update_connector(connector_id: str, payload: ConnectorUpdate, db: Session = Depends(get_db)):
    model = connector_service.get(db, connector_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    model = connector_service.update(db, model, payload)
    if model.connector_type == "mqtt" and payload.enabled is not None:
        if model.enabled:
            mqtt_runtime.start(model.id, asyncio.get_running_loop())
        else:
            mqtt_runtime.stop(model.id)
    elif model.connector_type == "http_poll" and payload.enabled is not None:
        if model.enabled:
            http_poll_runtime.start(model.id)
        else:
            http_poll_runtime.stop(model.id)
    elif model.connector_type == "websocket" and payload.enabled is not None:
        if model.enabled:
            websocket_runtime.start(model.id)
        else:
            websocket_runtime.stop(model.id)
    return connector_service.to_schema(model)

@router.delete("/{connector_id}", status_code=204)
async def delete_connector(connector_id: str, db: Session = Depends(get_db)):
    model = connector_service.get(db, connector_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    mqtt_runtime.stop(model.id)
    http_poll_runtime.stop(model.id)
    websocket_runtime.stop(model.id)
    db.delete(model)
    db.commit()
    return Response(status_code=204)

@router.post("/{connector_id}/test", response_model=ConnectorTestResult)
async def test_connector(connector_id: str, db: Session = Depends(get_db)):
    model = connector_service.get(db, connector_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    started = time.monotonic()
    try:
        if model.connector_type == "webhook":
            if not model.webhook_token_hash:
                raise RuntimeError("Webhook secret is missing")
            message = "Webhook receiver is ready; send a signed JSON event to the ingest URL"
        elif model.connector_type == "mqtt":
            credential = vault_service.get(db, model.credential_id) if model.credential_id else None
            await asyncio.to_thread(
                mqtt_runtime.test, model.config["host"], int(model.config.get("port", 1883)),
                bool(model.config.get("tls", False)),
                credential.username if credential else None,
                credential.secret if credential else None,
            )
            message = "Connected to MQTT broker"
        elif model.connector_type == "http_poll":
            credential = vault_service.get(db, model.credential_id) if model.credential_id else None
            await http_poll_runtime.test(model.config, credential)
            message = "HTTP endpoint returned valid JSON"
        elif model.connector_type == "websocket":
            credential = vault_service.get(db, model.credential_id) if model.credential_id else None
            await websocket_runtime.test(model.config, credential)
            message = "WebSocket handshake succeeded"
        else:
            raise RuntimeError("Unsupported connector type")
        model.status = "ready" if model.connector_type == "webhook" else "connected"
        model.last_error = None
        model.last_checked_at = datetime.now(timezone.utc)
        db.commit()
        return ConnectorTestResult(status="healthy", message=message, latency_ms=round((time.monotonic() - started) * 1000, 1))
    except Exception as exc:
        db.rollback()
        current = connector_service.get(db, connector_id)
        if current:
            current.status = "error"
            current.last_error = type(exc).__name__
            current.last_checked_at = datetime.now(timezone.utc)
            db.commit()
        raise HTTPException(status_code=400, detail="Connection check failed: " + type(exc).__name__) from exc

@ingest_router.post("/{connector_id}")
async def receive_webhook(connector_id: str, request: Request, db: Session = Depends(get_db)):
    raw_token = request.headers.get("x-sentinel-webhook-token", "")
    if not raw_token:
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            raw_token = authorization[7:].strip()
    model = db.query(ConnectorModel).filter(
        ConnectorModel.id == connector_id,
        ConnectorModel.connector_type == "webhook",
        ConnectorModel.enabled.is_(True),
    ).first()
    if model is None or not model.webhook_token_hash:
        raise HTTPException(status_code=404, detail="Webhook connector not found or disabled")
    supplied_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    if not raw_token or not hmac.compare_digest(supplied_hash, model.webhook_token_hash):
        raise HTTPException(status_code=401, detail="Valid connector webhook token required")
    body = await request.body()
    if len(body) > 1_048_576:
        raise HTTPException(status_code=413, detail="Webhook payload exceeds 1 MiB")
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail="Webhook body must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Webhook body must be a JSON object")
    try:
        observation = ingest_connector_payload(db, model, payload)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await broadcast_ingested(observation)
    return {"accepted": True, "observation": observation}
