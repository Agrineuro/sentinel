from fastapi import APIRouter, HTTPException

from app.schemas.assets import Asset, AssetCreate
from app.services.asset_registry import asset_registry

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("", response_model=Asset)
async def create_asset(payload: AssetCreate):
    return await asset_registry.create_asset(payload)


@router.get("", response_model=list[Asset])
async def list_assets():
    return asset_registry.list_assets()


@router.get("/{asset_id}", response_model=Asset)
async def get_asset(asset_id: str):
    asset = asset_registry.get_asset(asset_id)

    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    return asset
