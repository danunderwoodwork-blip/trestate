from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True)
    # MVP: анонимная идентификация по device-токену (заголовок X-Device-Id);
    # e-mail/полноценные аккаунты — этап 2.
    device_token: Mapped[str] = mapped_column(sa.String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(sa.String(255))
    created_at: Mapped[datetime] = mapped_column()


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (sa.UniqueConstraint("user_id", "listing_id"),)

    id: Mapped[int] = mapped_column(sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True)
    user_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id", ondelete="CASCADE"), index=True)
    listing_id: Mapped[int] = mapped_column(sa.ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column()
