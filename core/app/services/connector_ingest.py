from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from app.models.connector import ConnectorModel
from app.schemas.observations import ObservationCreate
from app.services.event_translation import translate_payload
from app.services.observation_hub import observation_hub
from app.services.observation_registry import observation_registry

def ingest_connector_payload(db: Session, connector: ConnectorModel, payload: dict[str, Any]) -> dict:
    translation = (connector.config or {}).get("translation") or {}
    field_map = translation.get("field_map") if isinstance(translation, dict) else None
    canonical = translate_payload(payload, connector.name, field_map)
    observation = observation_registry.add(db, ObservationCreate(**canonical.model_dump()))
    return observation_registry.to_schema(observation).model_dump(mode="json")

async def broadcast_ingested(observation: dict):
    await observation_hub.broadcast(observation)
