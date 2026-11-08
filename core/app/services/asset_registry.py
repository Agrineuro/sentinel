from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.asset import AssetModel
from app.schemas.assets import Asset, AssetCreate, AssetUpdate
from app.services.event_bus import SentinelEvent, event_bus


class AssetRegistry:
    async def create_asset(self, db: Session, payload: AssetCreate) -> Asset:
        existing = self._find_existing_asset(db, payload)

        if existing is not None:
            existing.asset_type = payload.asset_type
            existing.display_name = payload.display_name
            existing.organization_id = payload.organization_id
            existing.site_id = payload.site_id
            existing.asset_metadata = payload.metadata
            existing.state = payload.state
            existing.health = payload.health

            db.commit()
            db.refresh(existing)

            asset = self._to_schema(existing)

            await event_bus.publish(
                SentinelEvent(
                    type="asset.updated",
                    source="asset_registry",
                    data=asset.model_dump(),
                )
            )

            return asset

        model = AssetModel(
            id=f"asset_{uuid4().hex}",
            asset_type=payload.asset_type,
            display_name=payload.display_name,
            organization_id=payload.organization_id,
            site_id=payload.site_id,
            asset_metadata=payload.metadata,
            state=payload.state,
            health=payload.health,
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        asset = self._to_schema(model)

        await event_bus.publish(
            SentinelEvent(
                type="asset.discovered",
                source="asset_registry",
                data=asset.model_dump(),
            )
        )

        return asset

    def list_assets(
        self, db: Session, search: str | None = None, asset_type: str | None = None,
        state: str | None = None, limit: int = 500, offset: int = 0,
    ) -> list[Asset]:
        query = db.query(AssetModel)
        if search:
            query = query.filter(AssetModel.display_name.ilike(f"%{search}%"))
        if asset_type:
            query = query.filter(AssetModel.asset_type == asset_type)
        if state:
            query = query.filter(AssetModel.state == state)
        rows = query.order_by(AssetModel.display_name.asc()).offset(offset).limit(limit).all()
        return [self._to_schema(model) for model in rows]

    def get_asset(self, db: Session, asset_id: str) -> Asset | None:
        model = db.query(AssetModel).filter(AssetModel.id == asset_id).first()

        if model is None:
            return None

        return self._to_schema(model)

    def update_asset(self, db: Session, asset_id: str, payload: AssetUpdate) -> Asset | None:
        model = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
        if model is None:
            return None
        values = payload.model_dump(exclude_unset=True)
        for key, value in values.items():
            if key == "metadata":
                model.asset_metadata = value or {}
            else:
                setattr(model, key, value)
        db.commit()
        db.refresh(model)
        return self._to_schema(model)

    def delete_asset(self, db: Session, asset_id: str) -> bool:
        model = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
        if model is None:
            return False
        from app.models.relationship import RelationshipModel
        db.query(RelationshipModel).filter(
            (RelationshipModel.source_asset_id == asset_id) |
            (RelationshipModel.target_asset_id == asset_id)
        ).delete(synchronize_session=False)
        db.delete(model)
        db.commit()
        return True

    def _find_existing_asset(
        self,
        db: Session,
        payload: AssetCreate,
    ) -> AssetModel | None:
        ip = payload.metadata.get("ip")
        hostname = payload.metadata.get("hostname")
        health_url = payload.metadata.get("health_url") or payload.metadata.get("url")
        requested_mode = payload.metadata.get("monitoring_mode")
        if not ip and not hostname and not health_url:
            return None

        existing_assets = (
            db.query(AssetModel)
            .filter(AssetModel.organization_id == payload.organization_id)
            .all()
        )

        for asset in existing_assets:
            metadata = asset.asset_metadata or {}
            existing_mode = metadata.get("monitoring_mode")
            if not existing_mode:
                existing_mode = "ssh" if metadata.get("credential_id") else "tcp"

            if health_url:
                existing_url = metadata.get("health_url") or metadata.get("url")
                if existing_url == health_url:
                    return asset
                continue

            if requested_mode and requested_mode != existing_mode:
                continue
            if ip and metadata.get("ip") == ip:
                return asset
            if hostname and metadata.get("hostname") == hostname:
                return asset

        return None

    def _to_schema(self, model: AssetModel) -> Asset:
        return Asset(
            id=model.id,
            asset_type=model.asset_type,
            display_name=model.display_name,
            organization_id=model.organization_id,
            site_id=model.site_id,
            state=model.state,
            health=model.health,
            metadata=model.asset_metadata or {},
        )


asset_registry = AssetRegistry()
