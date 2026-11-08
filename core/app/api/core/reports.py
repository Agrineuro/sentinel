from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.alert import AlertModel
from app.models.asset import AssetModel
from app.models.observation import ObservationModel

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/summary")
async def report_summary(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)
    observation_total = db.query(func.count(ObservationModel.id)).scalar() or 0
    recent_total = (db.query(func.count(ObservationModel.id))
                    .filter(ObservationModel.timestamp >= since).scalar() or 0)
    by_type = (db.query(ObservationModel.observation_type, func.count(ObservationModel.id))
               .group_by(ObservationModel.observation_type).all())
    by_severity = (db.query(ObservationModel.severity, func.count(ObservationModel.id))
                   .group_by(ObservationModel.severity).all())
    asset_health = (db.query(AssetModel.health, func.count(AssetModel.id))
                    .group_by(AssetModel.health).all())
    open_alerts = db.query(func.count(AlertModel.id)).filter(AlertModel.status == "open").scalar() or 0
    acknowledged_alerts = db.query(func.count(AlertModel.id)).filter(AlertModel.status == "acknowledged").scalar() or 0
    latest = db.query(ObservationModel).order_by(ObservationModel.timestamp.desc()).first()
    return {
        "generated_at": now,
        "window_hours": 24,
        "observation_total": observation_total,
        "observations_last_24h": recent_total,
        "observations_by_type": {key: value for key, value in by_type},
        "observations_by_severity": {key: value for key, value in by_severity},
        "assets_by_health": {key: value for key, value in asset_health},
        "open_alerts": open_alerts,
        "acknowledged_alerts": acknowledged_alerts,
        "latest_observation_at": latest.timestamp if latest else None,
    }
