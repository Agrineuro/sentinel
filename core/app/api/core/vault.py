from fastapi import APIRouter, Depends
from app.api.auth import require_operator
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.vault import CredentialCreate, CredentialMetadata
from app.vault.service import vault_service

router = APIRouter(prefix="/vault", tags=["vault"])


@router.post("/credentials", response_model=CredentialMetadata, dependencies=[Depends(require_operator)])
async def create_credential(
    payload: CredentialCreate,
    db: Session = Depends(get_db),
):
    return vault_service.create_credential(db, payload)


@router.get("/credentials", response_model=list[CredentialMetadata])
async def list_credentials(db: Session = Depends(get_db)):
    return vault_service.list_credentials(db)
