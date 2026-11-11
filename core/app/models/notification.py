from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base


class NotificationDestinationModel(Base):
    __tablename__ = "notification_destinations"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    channel_type: Mapped[str] = mapped_column(String(20), index=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    credential_id: Mapped[str] = mapped_column(ForeignKey("credentials.id"))
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    status: Mapped[str] = mapped_column(String(24), default="unverified")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class NotificationDeliveryModel(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (UniqueConstraint("alert_id", "destination_id", name="uq_notification_alert_destination"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    alert_id: Mapped[str] = mapped_column(ForeignKey("alerts.id"), index=True)
    destination_id: Mapped[str] = mapped_column(ForeignKey("notification_destinations.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationSubscriptionModel(Base):
    __tablename__ = "notification_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "rule_id", "destination_id", name="uq_notification_subscription"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("rules.id"), index=True)
    destination_id: Mapped[str] = mapped_column(ForeignKey("notification_destinations.id"), index=True)
