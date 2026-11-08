from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

class ObservationCreate(BaseModel):
    type: str = Field(min_length=1, max_length=80)
    severity: str = Field(default="info", min_length=1, max_length=30)
    summary: str = Field(min_length=1, max_length=2000)
    source: str = Field(min_length=1, max_length=200)
    entity_id: str | None = None
    entity: str | None = None
    value: Any = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    raw: Any = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Observation(BaseModel):
    id: str
    timestamp: datetime
    type: str
    severity: str
    summary: str
    source: str
    entity_id: str | None = None
    entity: str | None = None
    value: Any = None
    confidence: float | None = None
    raw: Any = None
