from fastapi import APIRouter, Depends, HTTPException, Response
from app.api.auth import require_operator
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.assets import Asset, AssetCreate, AssetUpdate
from app.services.asset_registry import asset_registry
from app.services.asset_monitor import refresh_assets
from app.services.observation_hub import observation_hub

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("", response_model=Asset, dependencies=[Depends(require_operator)])
async def create_asset(payload: AssetCreate, db: Session = Depends(get_db)):
    return await asset_registry.create_asset(db, payload)


@router.get("", response_model=list[Asset])
async def list_assets(
    search: str | None = None,
    asset_type: str | None = None,
    state: str | None = None,
    limit: int = 500,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    if limit < 1 or limit > 500 or offset < 0:
        raise HTTPException(status_code=422, detail="Limit must be 1-500 and offset must be non-negative")
    return asset_registry.list_assets(
        db, search=search, asset_type=asset_type, state=state, limit=limit, offset=offset,
    )


@router.patch("/{asset_id}", response_model=Asset, dependencies=[Depends(require_operator)])
async def update_asset(asset_id: str, payload: AssetUpdate, db: Session = Depends(get_db)):
    asset = asset_registry.update_asset(db, asset_id, payload)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/{asset_id}", status_code=204, dependencies=[Depends(require_operator)])
async def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    if not asset_registry.delete_asset(db, asset_id):
        raise HTTPException(status_code=404, detail="Asset not found")
    return Response(status_code=204)


@router.post("/refresh", dependencies=[Depends(require_operator)])
async def refresh_system_health(db: Session = Depends(get_db)):
    systems = refresh_assets(db)
    for system in systems:
        if system.get("observation"):
            await observation_hub.broadcast(system["observation"])
    return {"systems": systems}


@router.get("/{asset_id}", response_model=Asset)
async def get_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = asset_registry.get_asset(db, asset_id)

    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    return asset
