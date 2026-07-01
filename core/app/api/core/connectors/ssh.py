from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.connectors.ssh_connector import SSHConnector
from app.database.session import get_db
from app.schemas.assets import Asset
from app.schemas.assets import AssetCreate
from app.schemas.ssh import SSHDiscoveryRequest
from app.services.asset_registry import asset_registry

router = APIRouter(prefix="/connectors/ssh", tags=["connectors"])


@router.post("/discover", response_model=Asset)
async def discover_linux_host(
    payload: SSHDiscoveryRequest,
    db: Session = Depends(get_db),
):
    connector = SSHConnector()

    try:
        metadata = connector.discover(
            host=payload.host,
            username=payload.username,
            password=payload.password,
            port=payload.port,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"SSH discovery failed: {exc}")

    asset_payload = AssetCreate(
        asset_type="linux_server",
        display_name=metadata.get("hostname") or payload.host,
        organization_id=payload.organization_id,
        site_id=payload.site_id,
        metadata=metadata,
    )

    return await asset_registry.create_asset(db, asset_payload)
