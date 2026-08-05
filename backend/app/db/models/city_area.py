from geoalchemy2 import Geometry
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CityArea(Base):
    __tablename__ = "city_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    geometry: Mapped[str | None] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326), nullable=True
    )
