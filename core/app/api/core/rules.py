from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.rule import RuleModel
from app.models.alert import AlertModel
from app.models.observation import ObservationModel
from app.schemas.rules import Rule, RuleCreate, RuleUpdate
from app.services.rule_engine import rule_engine

router = APIRouter(prefix="/rules", tags=["rules"])


def _validate_condition(field, operator, value):
    parts = (field, operator, value)
    if any(part is not None for part in parts) and not all(part is not None for part in parts):
        raise HTTPException(status_code=422, detail="Numeric conditions require a field, operator, and threshold")


@router.get("", response_model=list[Rule])
async def list_rules(db: Session = Depends(get_db)):
    return db.query(RuleModel).order_by(RuleModel.created_at.desc()).all()


@router.post("/preview")
async def preview_rule(payload: RuleCreate, db: Session = Depends(get_db)):
    rows = (db.query(ObservationModel)
            .order_by(ObservationModel.timestamp.desc(), ObservationModel.id.desc())
            .limit(500).all())
    matches = [row for row in rows if rule_engine.matches(payload, row)]
    return {
        "scanned": len(rows),
        "match_count": len(matches),
        "matches": [{
            "id": row.id,
            "timestamp": row.timestamp,
            "summary": row.summary,
            "severity": row.severity,
            "entity": row.entity,
            "value": row.value,
        } for row in matches[:20]],
    }


@router.post("", response_model=Rule, status_code=201)
async def create_rule(payload: RuleCreate, db: Session = Depends(get_db)):
    model = RuleModel(id=f"rule_{uuid4().hex}", **payload.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.patch("/{rule_id}", response_model=Rule)
async def update_rule(rule_id: str, payload: RuleUpdate, db: Session = Depends(get_db)):
    model = db.query(RuleModel).filter(RuleModel.id == rule_id).first()
    if model is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(model, key, value)
    _validate_condition(model.condition_field, model.condition_operator, model.condition_value)
    db.commit()
    db.refresh(model)
    return model


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    model = db.query(RuleModel).filter(RuleModel.id == rule_id).first()
    if model is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.query(AlertModel).filter(AlertModel.rule_id == rule_id).update(
        {AlertModel.rule_id: None}, synchronize_session=False
    )
    db.delete(model)
    db.commit()
    return Response(status_code=204)
