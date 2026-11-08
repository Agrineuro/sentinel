from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.asset import AssetModel
from app.models.relationship import RelationshipModel
from app.schemas.relationships import Relationship, RelationshipCreate


class RelationshipRegistry:
    def list(self, db: Session) -> list[Relationship]:
        return [self._to_schema(item) for item in db.query(RelationshipModel).all()]

    def create(self, db: Session, payload: RelationshipCreate) -> Relationship:
        if payload.source_asset_id == payload.target_asset_id:
            raise ValueError("A relationship must connect two different assets")
        source = db.query(AssetModel).filter(AssetModel.id == payload.source_asset_id).first()
        target = db.query(AssetModel).filter(AssetModel.id == payload.target_asset_id).first()
        if source is None or target is None:
            raise LookupError("Both assets must exist before connecting them")
        existing = db.query(RelationshipModel).filter(
            RelationshipModel.source_asset_id == payload.source_asset_id,
            RelationshipModel.target_asset_id == payload.target_asset_id,
            RelationshipModel.relationship_type == payload.relationship_type,
        ).first()
        if existing:
            return self._to_schema(existing)
        model = RelationshipModel(
            id=f"rel_{uuid4().hex}",
            source_asset_id=payload.source_asset_id,
            target_asset_id=payload.target_asset_id,
            relationship_type=payload.relationship_type.strip(),
            metadata_json=payload.metadata,
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return self._to_schema(model)

    def delete(self, db: Session, relationship_id: str) -> bool:
        model = db.query(RelationshipModel).filter(RelationshipModel.id == relationship_id).first()
        if model is None:
            return False
        db.delete(model)
        db.commit()
        return True

    def _to_schema(self, model: RelationshipModel) -> Relationship:
        return Relationship(
            id=model.id,
            source_asset_id=model.source_asset_id,
            target_asset_id=model.target_asset_id,
            relationship_type=model.relationship_type,
            metadata=model.metadata_json or {},
        )


relationship_registry = RelationshipRegistry()
