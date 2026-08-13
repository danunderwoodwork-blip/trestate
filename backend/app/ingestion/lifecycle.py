"""Жизненный цикл объявления и адаптивный график перепроверки.

active -> possibly_inactive -> inactive, с подтверждением исчезновения повторной
проверкой (см. docs/ARCHITECTURE.md). Интервалы конфигурируются в core/config.py.
"""
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.models import Listing, ListingStatus


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def next_check_at(listing: Listing, now: datetime) -> datetime:
    """Возраст объявления + тип сделки -> момент следующей плановой перепроверки."""
    settings = get_settings()
    age_days = max(0, (now - listing.first_seen_at).days)
    hours = settings.recheck_schedule[-1][1]
    for max_age, interval_hours in settings.recheck_schedule:
        if age_days <= max_age:
            hours = interval_hours
            break
    hours *= settings.recheck_multiplier.get(listing.transaction_type, 1.0)
    return now + timedelta(hours=hours)


def register_miss(listing: Listing) -> str | None:
    """Объявление не найдено в индексе. Возвращает новый статус, если он изменился."""
    settings = get_settings()
    listing.miss_count += 1
    if listing.status == ListingStatus.ACTIVE:
        listing.status = ListingStatus.POSSIBLY_INACTIVE
        return listing.status
    if (
        listing.status == ListingStatus.POSSIBLY_INACTIVE
        and listing.miss_count >= settings.inactive_after_misses
    ):
        listing.status = ListingStatus.INACTIVE
        return listing.status
    return None


def register_seen(listing: Listing) -> str | None:
    """Объявление снова в индексе. Возвращает новый статус при реактивации."""
    listing.miss_count = 0
    if listing.status != ListingStatus.ACTIVE:
        listing.status = ListingStatus.ACTIVE
        return listing.status
    return None
