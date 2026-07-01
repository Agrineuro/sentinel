from uuid import uuid4

from app.schemas.assets import Asset, AssetCreate
from app.services.event_bus import SentinelEvent, event_bus


class AssetRegistry:
    def __init__(self) -> None:
        self._assets: dict[str, Asset] = {}

    async def create_asset(self, payload: AssetCreate) -> Asset:
        asset = Asset(
            id=f"asset_{uuid4().hex}",
            asset_type=payload.asset_type,
            display_name=payload.display_name,
            organization_id=payload.organization_id,
            site_id=payload.site_id,
            metadata=payload.metadata,
        )

        self._assets[asset.id] = asset

        await event_bus.publish(
            SentinelEvent(
                type="asset.discovered",
                source="asset_registry",
                data=asset.model_dump(),
            )
        )

        return asset

    def list_assets(self) -> list[Asset]:
        return list(self._assets.values())

    def get_asset(self, asset_id: str) -> Asset | None:
        return self._assets.get(asset_id)


asset_registry = AssetRegistry()
