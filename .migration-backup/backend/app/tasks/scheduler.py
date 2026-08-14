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
from app.services.tcmb import refresh_rates

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


def run_rates_refresh() -> None:
    db = SessionLocal()
    try:
        asyncio.run(refresh_rates(db))
    except Exception:
        # живём на предыдущих сохранённых курсах до следующего запуска
        log.exception("TCMB rates refresh failed; keeping previous rates")
    finally:
        db.close()


def main() -> None:
    scheduler = BlockingScheduler()
    # Каждый час пробуждаемся; какие объявления реально перепроверять, решает
    # адаптивный график (next_check_at) внутри pipeline — лишней работы нет.
    scheduler.add_job(run_sync_cycle, "interval", hours=1, next_run_time=None)
    # Бюллетень TCMB выходит раз в рабочий день (~15:30 TRT); проверяем каждые 6 ч.
    scheduler.add_job(run_rates_refresh, "interval", hours=6, next_run_time=None)
    log.info("scheduler started; running initial rates refresh and sync")
    run_rates_refresh()
    run_sync_cycle()
    scheduler.start()


if __name__ == "__main__":
    main()
