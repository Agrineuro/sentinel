from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base

class RuleModel(Base):
    __tablename__ = "rules"
    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    observation_type: Mapped[str] = mapped_column(String, default="*", index=True)
    minimum_severity: Mapped[str] = mapped_column(String, default="warning")
    source_contains: Mapped[str | None] = mapped_column(String, nullable=True)
    entity_contains: Mapped[str | None] = mapped_column(String, nullable=True)
    summary_contains: Mapped[str | None] = mapped_column(String, nullable=True)
    condition_field: Mapped[str | None] = mapped_column(String(160), nullable=True)
    condition_operator: Mapped[str | None] = mapped_column(String(8), nullable=True)
    condition_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
