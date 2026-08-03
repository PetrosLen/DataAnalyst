from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Venue(Base):
    __tablename__ = "venues"
    __table_args__ = (
        CheckConstraint("price_level BETWEEN 1 AND 4", name="ck_venues_price_level"),
        CheckConstraint(
            "status IN ('pending', 'active', 'inactive', 'unverified', 'merged')",
            name="ck_venues_status",
        ),
        CheckConstraint(
            "overall_confidence BETWEEN 0 AND 1", name="ck_venues_overall_confidence"
        ),
        Index("idx_venues_status", "status"),
        Index("idx_venues_primary_category", "primary_category_id"),
        Index(
            "idx_venues_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description_short: Mapped[str | None] = mapped_column(String, nullable=True)
    description_long: Mapped[str | None] = mapped_column(String, nullable=True)
    geom: Mapped[str] = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    city_area_id: Mapped[int | None] = mapped_column(ForeignKey("city_areas.id"), nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    website: Mapped[str | None] = mapped_column(String, nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String, nullable=True)
    price_level: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    primary_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="pending")
    overall_confidence: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, server_default="0.0"
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
