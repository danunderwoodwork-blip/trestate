"""Сидинг дев-среды: создаёт таблицы, регистрирует источники, запускает первый sync.

Запуск из backend/:  python -m scripts.seed_demo
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.ingestion.lifecycle import utcnow
from app.ingestion.pipeline import sync_all_enabled
from app.models import Source
from app.services.currency import upsert_rate

SOURCES = [
    # Демо-фид (агентский JSON, поставляется с репозиторием) — включён.
    {
        "code": "mock",
        "name": "Demo Agency Feed",
        "adapter": "app.sources.mock.adapter:MockSource",
        "enabled": True,
    },
    # Sahibinden — placeholder, выключен до появления разрешённого канала данных.
    {
        "code": "sahibinden",
        "name": "Sahibinden (disabled: no authorized channel)",
        "adapter": "app.sources.sahibinden.adapter:SahibindenSource",
        "enabled": False,
    },
]


def main() -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        for spec in SOURCES:
            if not db.scalar(select(Source).where(Source.code == spec["code"])):
                db.add(Source(**spec))
        now = utcnow()
        upsert_rate(db, "USD", "$", 41.0, now)
        upsert_rate(db, "EUR", "€", 46.5, now)
        db.commit()

        results = asyncio.run(sync_all_enabled(db))
        for stats in results:
            print(
                f"{stats.source}: index={stats.total_in_index} new={stats.new} "
                f"updated={stats.updated} unchanged={stats.unchanged} missing={stats.missing}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
