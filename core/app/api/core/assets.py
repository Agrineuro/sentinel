from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.assets import Asset, AssetCreate
from app.services.asset_registry import asset_registry

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("", response_model=Asset)
async def create_asset(payload: AssetCreate, db: Session = Depends(get_db)):
    return await asset_registry.create_asset(db, payload)


@router.get("", response_model=list[Asset])
async def list_assets(db: Session = Depends(get_db)):
    return asset_registry.list_assets(db)


@router.get("/{asset_id}", response_model=Asset)
async def get_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = asset_registry.get_asset(db, asset_id)

    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    return asset
