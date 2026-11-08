from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from app.models.connector import ConnectorModel
from app.schemas.observations import ObservationCreate
from app.services.observation_hub import observation_hub
from app.services.observation_registry import observation_registry

ALLOWED_SEVERITIES = {"info", "warning", "error", "critical"}

def ingest_connector_payload(db: Session, connector: ConnectorModel, payload: dict[str, Any]) -> dict:
    severity = str(payload.get("severity") or "info").lower()
    if severity not in ALLOWED_SEVERITIES:
        raise ValueError("Event severity must be info, warning, error, or critical")
    timestamp = payload.get("timestamp") or datetime.now(timezone.utc)
    observation = observation_registry.add(db, ObservationCreate(
        type=str(payload.get("type") or payload.get("event_type") or "connector.event")[:80],
        severity=severity,
        summary=str(payload.get("summary") or payload.get("message") or "Event received from " + connector.name)[:2000],
        source=connector.name,
        entity_id=str(payload.get("entity_id")) if payload.get("entity_id") is not None else None,
        entity=str(payload.get("entity")) if payload.get("entity") is not None else None,
        value=payload.get("value", payload.get("data")),
        raw=payload,
        timestamp=timestamp,
    ))
    result = observation_registry.to_schema(observation).model_dump(mode="json")
    return result

async def broadcast_ingested(observation: dict):
    await observation_hub.broadcast(observation)
