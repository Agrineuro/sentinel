from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.observation import ObservationModel
from app.schemas.observations import Observation, ObservationCreate
from app.services.rule_engine import rule_engine

class ObservationRegistry:
    def add(self, db: Session, payload: ObservationCreate, *, commit: bool = True) -> ObservationModel:
        model = ObservationModel(
            id=f"obs_{uuid4().hex}", timestamp=payload.timestamp,
            observation_type=payload.type, severity=payload.severity,
            summary=payload.summary, source=payload.source,
            entity_id=payload.entity_id, entity=payload.entity,
            value=payload.value, confidence=payload.confidence, raw=payload.raw,
        )
        db.add(model)
        db.flush()
        rule_engine.evaluate(db, model)
        if commit:
            db.commit()
            db.refresh(model)
        return model

    def list(
        self, db: Session, limit: int = 100, offset: int = 0,
        observation_type: str | None = None, severity: str | None = None,
        source: str | None = None, entity_id: str | None = None,
        search: str | None = None,
    ) -> list[Observation]:
        query = db.query(ObservationModel)
        if observation_type:
            query = query.filter(ObservationModel.observation_type == observation_type)
        if severity:
            query = query.filter(ObservationModel.severity == severity)
        if source:
            query = query.filter(ObservationModel.source.ilike(f"%{source}%"))
        if entity_id:
            query = query.filter(ObservationModel.entity_id == entity_id)
        if search:
            term = f"%{search}%"
            query = query.filter(ObservationModel.summary.ilike(term) | ObservationModel.entity.ilike(term))
        rows = (query.order_by(ObservationModel.timestamp.desc(), ObservationModel.id.desc())
                .offset(offset).limit(limit).all())
        return [self.to_schema(row) for row in rows]

    @staticmethod
    def to_schema(model: ObservationModel) -> Observation:
        return Observation(
            id=model.id, timestamp=model.timestamp, type=model.observation_type,
            severity=model.severity, summary=model.summary, source=model.source,
            entity_id=model.entity_id, entity=model.entity, value=model.value,
            confidence=model.confidence, raw=model.raw,
        )

observation_registry = ObservationRegistry()
