"""Курсы валют из официального XML ЦБ Турции (TCMB).

https://www.tcmb.gov.tr/kurlar/today.xml — публичный бюллетень, обновляется
по рабочим дням ~15:30 TRT. Никакого скрейпинга — это официальный канал данных.
"""
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.currency import upsert_rate

log = logging.getLogger(__name__)

TCMB_TODAY_URL = "https://www.tcmb.gov.tr/kurlar/today.xml"

_SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£"}


def parse_tcmb_xml(content: str) -> dict[str, float]:
    """XML бюллетеня -> {код валюты: курс к TRY за 1 единицу}.

    Курс — среднее ForexBuying/ForexSelling, делённое на Unit
    (у некоторых валют, например JPY, котировка за 100 единиц).
    """
    rates: dict[str, float] = {}
    root = ET.fromstring(content)
    for cur in root.iter("Currency"):
        code = cur.get("CurrencyCode") or cur.get("Kod")
        if not code:
            continue

        def _num(tag: str) -> float | None:
            text = (cur.findtext(tag) or "").strip()
            try:
                return float(text)
            except ValueError:
                return None

        buying, selling = _num("ForexBuying"), _num("ForexSelling")
        unit = _num("Unit") or 1
        values = [v for v in (buying, selling) if v]
        if not values or unit <= 0:
            continue
        rates[code] = (sum(values) / len(values)) / unit
    return rates


async def fetch_rates() -> dict[str, float]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(TCMB_TODAY_URL)
        resp.raise_for_status()
        return parse_tcmb_xml(resp.text)


async def refresh_rates(db: Session) -> dict[str, float]:
    """Обновляет в БД курсы для display_currencies (кроме TRY).

    При недоступности TCMB бросает исключение — вызывающий решает,
    жить ли на предыдущих сохранённых курсах.
    """
    settings = get_settings()
    wanted = [c for c in settings.display_currencies if c != "TRY"]
    rates = await fetch_rates()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stored: dict[str, float] = {}
    for code in wanted:
        rate = rates.get(code)
        if rate is None:
            log.warning("TCMB bulletin has no rate for %s", code)
            continue
        upsert_rate(db, code, _SYMBOLS.get(code, code), rate, now)
        stored[code] = rate
    db.commit()
    log.info("TCMB rates updated: %s", stored)
    return stored
