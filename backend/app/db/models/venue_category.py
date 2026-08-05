from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VenueCategory(Base):
    __tablename__ = "venue_categories"

    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), primary_key=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
