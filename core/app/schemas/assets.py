from pydantic import BaseModel, Field
from typing import Any


class AssetCreate(BaseModel):
    asset_type: str
    display_name: str
    organization_id: str = "org_default"
    site_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Asset(BaseModel):
    id: str
    asset_type: str
    display_name: str
    organization_id: str
    site_id: str | None = None
    state: str = "unknown"
    health: str = "unknown"
    metadata: dict[str, Any] = Field(default_factory=dict)
