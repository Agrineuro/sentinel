from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.observations import Observation, ObservationCreate
from app.services.observation_registry import observation_registry
from app.services.observation_hub import observation_hub

router = APIRouter(prefix="/observations", tags=["observations"])
legacy_events_router = APIRouter(prefix="/events", tags=["observations"])

@router.get("", response_model=list[Observation])
async def list_observations(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    type: str | None = Query(default=None, min_length=1, max_length=80),
    severity: str | None = Query(default=None, min_length=1, max_length=24),
    source: str | None = Query(default=None, min_length=1, max_length=120),
    entity_id: str | None = Query(default=None, min_length=1, max_length=160),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    db: Session = Depends(get_db),
):
    return observation_registry.list(
        db, limit=limit, offset=offset, observation_type=type,
        severity=severity, source=source, entity_id=entity_id, search=search,
    )

@router.post("", response_model=Observation, status_code=201)
async def create_observation(payload: ObservationCreate, db: Session = Depends(get_db)):
    row = observation_registry.add(db, payload)
    result = observation_registry.to_schema(row)
    await observation_hub.broadcast(result.model_dump(mode="json"))
    return result

@legacy_events_router.get("", response_model=list[Observation])
async def list_events(limit: int = Query(default=100, ge=1, le=500),
                      offset: int = Query(default=0, ge=0),
                      db: Session = Depends(get_db)):
    return observation_registry.list(db, limit=limit, offset=offset)
