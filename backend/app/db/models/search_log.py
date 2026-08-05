from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SearchLog(Base):
    __tablename__ = "search_logs"
    __table_args__ = (
        Index("idx_search_logs_session", "session_id"),
        Index("idx_search_logs_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False)
    origin_geom: Mapped[str | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=True
    )
    city_area_id: Mapped[int | None] = mapped_column(ForeignKey("city_areas.id"), nullable=True)
    result_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
