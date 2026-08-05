from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        CheckConstraint("tag_type IN ('vibe', 'amenity', 'audience')", name="ck_tags_tag_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    tag_type: Mapped[str] = mapped_column(String, nullable=False)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)
