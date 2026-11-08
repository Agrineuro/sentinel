from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.auth import require_operator
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.alert import AlertModel
from app.schemas.alerts import Alert, AlertStatusUpdate

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("", response_model=list[Alert])
async def list_alerts(
    status: str | None = Query(default=None, pattern="^(open|acknowledged|resolved|active)$"),
    severity: str | None = Query(default=None, min_length=1, max_length=24),
    entity_id: str | None = Query(default=None, min_length=1, max_length=160),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(AlertModel)
    if status == "active":
        query = query.filter(AlertModel.status.in_(["open", "acknowledged"]))
    elif status:
        query = query.filter(AlertModel.status == status)
    if severity:
        query = query.filter(AlertModel.severity == severity)
    if entity_id:
        query = query.filter(AlertModel.entity_id == entity_id)
    if search:
        term = f"%{search}%"
        query = query.filter(AlertModel.title.ilike(term) | AlertModel.summary.ilike(term) | AlertModel.entity.ilike(term))
    return query.order_by(AlertModel.triggered_at.desc()).offset(offset).limit(limit).all()

@router.patch("/{alert_id}", response_model=Alert, dependencies=[Depends(require_operator)])
async def update_alert(alert_id: str, payload: AlertStatusUpdate, db: Session = Depends(get_db)):
    if payload.status not in {"open", "acknowledged", "resolved"}:
        raise HTTPException(status_code=422, detail="Status must be open, acknowledged, or resolved")
    model = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if model is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    model.status = payload.status
    now = datetime.now(timezone.utc)
    model.acknowledged_at = now if payload.status == "acknowledged" else None
    model.resolved_at = now if payload.status == "resolved" else None
    db.commit()
    db.refresh(model)
    return model
