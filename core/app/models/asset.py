from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class AssetModel(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    asset_type: Mapped[str] = mapped_column(String, index=True)
    display_name: Mapped[str] = mapped_column(String, index=True)
    organization_id: Mapped[str] = mapped_column(String, index=True)
    site_id: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str] = mapped_column(String, default="unknown")
    health: Mapped[str] = mapped_column(String, default="unknown")
    asset_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
