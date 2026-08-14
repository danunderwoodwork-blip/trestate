from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Currency(Base):
    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(sa.String(3), primary_key=True)
    symbol: Mapped[str] = mapped_column(sa.String(4))


class ExchangeRate(Base):
    """Курс к TRY на момент fetched_at. Исходная цена объявления никогда не заменяется."""

    __tablename__ = "exchange_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    currency_code: Mapped[str] = mapped_column(sa.ForeignKey("currencies.code"), index=True)
    rate_to_try: Mapped[float] = mapped_column(sa.Numeric(14, 6))
    fetched_at: Mapped[datetime] = mapped_column(index=True)
