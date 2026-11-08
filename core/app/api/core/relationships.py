from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.relationships import Relationship, RelationshipCreate
from app.services.relationship_registry import relationship_registry

router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.get("", response_model=list[Relationship])
async def list_relationships(db: Session = Depends(get_db)):
    return relationship_registry.list(db)


@router.post("", response_model=Relationship)
async def create_relationship(payload: RelationshipCreate, db: Session = Depends(get_db)):
    try:
        return relationship_registry.create(db, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{relationship_id}")
async def delete_relationship(relationship_id: str, db: Session = Depends(get_db)):
    if not relationship_registry.delete(db, relationship_id):
        raise HTTPException(status_code=404, detail="Relationship not found")
    return {"status": "deleted", "id": relationship_id}
