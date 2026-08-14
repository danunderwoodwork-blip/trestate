"""Курсы валют. Исходная цена объявления никогда не заменяется конвертированной —
конвертация только для приблизительного отображения."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Currency, ExchangeRate


def latest_rate(db: Session, code: str) -> ExchangeRate | None:
    if code == "TRY":
        return None
    return db.scalar(
        select(ExchangeRate)
        .where(ExchangeRate.currency_code == code)
        .order_by(ExchangeRate.fetched_at.desc())
        .limit(1)
    )


def to_try(db: Session, amount: float, code: str) -> float | None:
    if code == "TRY":
        return amount
    rate = latest_rate(db, code)
    return amount * float(rate.rate_to_try) if rate else None


def convert_from_try(db: Session, amount_try: float, code: str) -> float | None:
    if code == "TRY":
        return amount_try
    rate = latest_rate(db, code)
    return amount_try / float(rate.rate_to_try) if rate else None


def upsert_rate(db: Session, code: str, symbol: str, rate_to_try: float, fetched_at: datetime) -> None:
    if not db.get(Currency, code):
        db.add(Currency(code=code, symbol=symbol))
    db.add(ExchangeRate(currency_code=code, rate_to_try=rate_to_try, fetched_at=fetched_at))
