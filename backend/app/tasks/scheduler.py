"""Планировщик фоновой синхронизации (MVP: APScheduler в отдельном процессе).

Запуск:  python -m app.tasks.scheduler
При росте нагрузки заменяется на Celery + Redis без изменения pipeline —
sync_all_enabled остаётся точкой входа.
"""
import asyncio
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from app.db.session import SessionLocal
from app.ingestion.pipeline import sync_all_enabled

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def run_sync_cycle() -> None:
    db = SessionLocal()
    try:
        results = asyncio.run(sync_all_enabled(db))
        for stats in results:
            log.info(
                "%s: index=%s new=%s updated=%s unchanged=%s missing=%s statuses=%s",
                stats.source, stats.total_in_index, stats.new, stats.updated,
                stats.unchanged, stats.missing, stats.status_changes,
            )
    finally:
        db.close()


def main() -> None:
    scheduler = BlockingScheduler()
    # Каждый час пробуждаемся; какие объявления реально перепроверять, решает
    # адаптивный график (next_check_at) внутри pipeline — лишней работы нет.
    scheduler.add_job(run_sync_cycle, "interval", hours=1, next_run_time=None)
    log.info("scheduler started; running initial sync")
    run_sync_cycle()
    scheduler.start()


if __name__ == "__main__":
    main()
