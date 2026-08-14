import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, JSONVariant


class Source(Base):
    """Зарегистрированный источник данных. adapter — точка входа python-класса."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(sa.String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(sa.String(255))
    adapter: Mapped[str] = mapped_column(sa.String(255))  # e.g. "app.sources.mock.adapter:MockSource"
    enabled: Mapped[bool] = mapped_column(default=True)
    config: Mapped[dict | None] = mapped_column(JSONVariant, default=None)
