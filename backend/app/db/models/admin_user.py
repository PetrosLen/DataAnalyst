from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AdminUser(Base):
    __tablename__ = "admin_users"
    __table_args__ = (
        CheckConstraint("role IN ('owner', 'editor', 'viewer')", name="ck_admin_users_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
