import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Location(Base):
    """Иерархия географии: country -> province -> district -> neighbourhood."""

    __tablename__ = "locations"
    __table_args__ = (sa.UniqueConstraint("parent_id", "level", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(sa.ForeignKey("locations.id"), index=True)
    level: Mapped[str] = mapped_column(sa.String(16), index=True)  # country|province|district|neighbourhood
    name: Mapped[str] = mapped_column(sa.String(128))
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, index=True)
    lat: Mapped[float | None] = mapped_column()
    lon: Mapped[float | None] = mapped_column()

    parent: Mapped["Location | None"] = relationship(remote_side=[id], backref="children")
