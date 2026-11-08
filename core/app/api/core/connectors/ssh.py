from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.connectors.ssh_connector import SSHConnector
from app.database.session import get_db
from app.schemas.assets import Asset, AssetCreate
from app.schemas.ssh import SSHDiscoveryRequest
from app.schemas.vault import CredentialCreate
from app.services.asset_registry import asset_registry
from app.vault.service import vault_service

router = APIRouter(prefix="/connectors/ssh", tags=["connectors"])


@router.post("/discover", response_model=Asset)
async def discover_linux_host(
    payload: SSHDiscoveryRequest,
    db: Session = Depends(get_db),
):
    if payload.credential_type not in {"ssh_password", "ssh_private_key"}:
        raise HTTPException(status_code=400, detail="Unsupported SSH credential type")
    connector = SSHConnector()
    try:
        event = connector.discover(
            host=payload.host,
            username=payload.username,
            password=payload.secret,
            port=payload.port,
            credential_type=payload.credential_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"SSH discovery failed: {exc}") from exc

    metadata = event["data"]
    credential = vault_service.create_credential(
        db,
        CredentialCreate(
            name=payload.credential_name,
            username=payload.username,
            password=payload.secret,
            credential_type=payload.credential_type,
        ),
    )
    metadata["credential_id"] = credential.id
    metadata["port"] = payload.port
    asset_payload = AssetCreate(
        asset_type="linux_server",
        display_name=payload.display_name or metadata.get("hostname") or payload.host,
        organization_id=payload.organization_id,
        site_id=payload.site_id,
        state="online",
        health="healthy",
        metadata=metadata,
    )
    return await asset_registry.create_asset(db, asset_payload)
