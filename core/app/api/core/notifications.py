from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.auth import require_user
from app.database.session import get_db
from app.models.notification import NotificationDestinationModel, NotificationDeliveryModel, NotificationSubscriptionModel
from app.models.alert import AlertModel
from app.models.rule import RuleModel
from app.models.user import UserModel
from app.schemas.notifications import NotificationDestinationCreate, NotificationDestinationRead, NotificationDestinationUpdate, NotificationSubscriptionUpdate
from app.services.notification_service import create_destination, destination_read, test_destination

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/destinations", response_model=list[NotificationDestinationRead])
async def list_destinations(user: UserModel = Depends(require_user), db: Session = Depends(get_db)):
    rows = (db.query(NotificationDestinationModel)
            .filter(NotificationDestinationModel.owner_user_id == user.id)
            .order_by(NotificationDestinationModel.created_at.desc()).all())
    return [destination_read(row, db) for row in rows]


@router.post("/destinations", response_model=NotificationDestinationRead, status_code=201)
async def add_destination(payload: NotificationDestinationCreate, user: UserModel = Depends(require_user), db: Session = Depends(get_db)):
    row = create_destination(db, payload, user.id)
    return destination_read(row, db)


@router.post("/destinations/{destination_id}/test")
async def send_test(destination_id: str, user: UserModel = Depends(require_user), db: Session = Depends(get_db)):
    row = db.query(NotificationDestinationModel).filter(
        NotificationDestinationModel.id == destination_id,
        NotificationDestinationModel.owner_user_id == user.id,
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Notification destination not found")
    try:
        test_destination(db, row)
    except Exception as exc:
        db.rollback()
        current = db.query(NotificationDestinationModel).filter(NotificationDestinationModel.id == destination_id).first()
        if current and current.owner_user_id == user.id:
            current.status = "error"
            current.last_error = type(exc).__name__
            db.commit()
        raise HTTPException(status_code=400, detail="Test delivery failed: " + type(exc).__name__) from exc
    return {"status": "verified", "message": "Test notification sent to the configured destination"}


@router.patch("/destinations/{destination_id}", response_model=NotificationDestinationRead)
async def set_destination_enabled(destination_id: str, payload: NotificationDestinationUpdate, user: UserModel = Depends(require_user), db: Session = Depends(get_db)):
    row = db.query(NotificationDestinationModel).filter(
        NotificationDestinationModel.id == destination_id,
        NotificationDestinationModel.owner_user_id == user.id,
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Notification destination not found")
    row.enabled = payload.enabled
    if not row.enabled:
        row.status = "disabled"
    elif row.status == "disabled":
        row.status = "unverified"
    db.commit()
    db.refresh(row)
    return destination_read(row, db)


@router.get("/subscriptions")
async def list_subscriptions(user: UserModel = Depends(require_user), db: Session = Depends(get_db)):
    rows = db.query(NotificationSubscriptionModel).filter(NotificationSubscriptionModel.user_id == user.id).all()
    result: dict[str, list[str]] = {}
    for row in rows:
        result.setdefault(row.rule_id, []).append(row.destination_id)
    return result


@router.put("/subscriptions/{rule_id}")
async def update_subscription(rule_id: str, payload: NotificationSubscriptionUpdate, user: UserModel = Depends(require_user), db: Session = Depends(get_db)):
    if db.query(RuleModel.id).filter(RuleModel.id == rule_id).first() is None:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    if payload.destination_ids:
        rows = db.query(NotificationDestinationModel).filter(
            NotificationDestinationModel.id.in_(payload.destination_ids),
            NotificationDestinationModel.owner_user_id == user.id,
            NotificationDestinationModel.enabled.is_(True),
            NotificationDestinationModel.status.in_(["verified", "error"]),
        ).all()
        if {row.id for row in rows} != set(payload.destination_ids):
            raise HTTPException(status_code=422, detail="Choose only your enabled, verified destinations")
    db.query(NotificationSubscriptionModel).filter(
        NotificationSubscriptionModel.user_id == user.id,
        NotificationSubscriptionModel.rule_id == rule_id,
    ).delete(synchronize_session=False)
    for destination_id in payload.destination_ids:
        db.add(NotificationSubscriptionModel(
            id="subscription_" + uuid4().hex, user_id=user.id,
            rule_id=rule_id, destination_id=destination_id,
        ))
    db.commit()
    return {"rule_id": rule_id, "destination_ids": payload.destination_ids}


@router.get("/deliveries")
async def list_deliveries(limit: int = Query(default=50, ge=1, le=200), user: UserModel = Depends(require_user), db: Session = Depends(get_db)):
    rows = (db.query(NotificationDeliveryModel)
            .join(NotificationDestinationModel, NotificationDestinationModel.id == NotificationDeliveryModel.destination_id)
            .filter(NotificationDestinationModel.owner_user_id == user.id)
            .order_by(NotificationDeliveryModel.next_attempt_at.desc())
            .limit(limit).all())
    result = []
    for row in rows:
        alert = db.query(AlertModel).filter(AlertModel.id == row.alert_id).first()
        destination = db.query(NotificationDestinationModel).filter(NotificationDestinationModel.id == row.destination_id).first()
        result.append({
            "id": row.id, "alert_id": row.alert_id,
            "alert_title": alert.title if alert else "Alert removed",
            "destination_name": destination.name if destination else "Destination removed",
            "channel_type": destination.channel_type if destination else "unknown",
            "status": row.status, "attempts": row.attempts,
            "last_error": row.last_error, "sent_at": row.sent_at,
        })
    return result
