from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


class CanonicalEvent(BaseModel):
    """Sentinel's common event shape before rules, storage, or routing."""

    type: str = Field(min_length=1, max_length=80)
    severity: str
    summary: str = Field(min_length=1, max_length=2000)
    source: str = Field(min_length=1, max_length=200)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entity_id: str | None = None
    entity: str | None = None
    value: Any = None
    raw: Any = None
