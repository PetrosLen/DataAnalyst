from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Imported so that Base.metadata is populated for Alembic autogenerate
# and for Base.metadata.create_all() in tests.
from app.db import models  # noqa: E402,F401
