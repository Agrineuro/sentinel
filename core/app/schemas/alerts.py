from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Literal

class AlertStatusUpdate(BaseModel):
    status: Literal["open", "acknowledged", "resolved"]

class Alert(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    rule_id: str | None = None
    source_observation_id: str
    title: str
    summary: str
    severity: str
    entity_id: str | None = None
    entity: str | None = None
    status: str
    occurrence_count: int
    triggered_at: datetime
    last_seen_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
