from datetime import datetime
from sqlalchemy import DateTime, Float, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base

class ObservationModel(Base):
    __tablename__ = "observations"
    __table_args__ = (Index("ix_observations_entity_timestamp", "entity_id", "timestamp"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    observation_type: Mapped[str] = mapped_column(String, index=True)
    severity: Mapped[str] = mapped_column(String, default="info", index=True)
    summary: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String, index=True)
    entity_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    entity: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    value: Mapped[object | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw: Mapped[object | None] = mapped_column(JSON, nullable=True)
