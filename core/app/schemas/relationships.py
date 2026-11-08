from pydantic import BaseModel, Field
from typing import Any


class RelationshipCreate(BaseModel):
    source_asset_id: str
    target_asset_id: str
    relationship_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Relationship(BaseModel):
    id: str
    source_asset_id: str
    target_asset_id: str
    relationship_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)
