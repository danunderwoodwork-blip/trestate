"""Сборка детальной карточки: аналитика цены и свежесть данных."""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.ingestion.lifecycle import utcnow
from app.models import Listing, ListingHistory
from app.schemas.listing import FreshnessInfo, ListingDetail, PriceInfo
from app.services.currency import convert_from_try, to_try


def get_listing(db: Session, listing_id: int) -> Listing | None:
    return db.scalar(
        select(Listing)
        .where(Listing.id == listing_id)
        .options(
            selectinload(Listing.images),
            selectinload(Listing.features),
            selectinload(Listing.history),
            selectinload(Listing.province),
            selectinload(Listing.district),
            selectinload(Listing.neighbourhood),
            selectinload(Listing.source),
        )
    )


def build_price_info(db: Session, listing: Listing) -> PriceInfo:
    history: list[ListingHistory] = listing.history
    price_points = [h for h in history if h.price is not None]
    initial = float(price_points[0].price) if price_points else None
    current = float(listing.price) if listing.price is not None else None

    changes = 0
    last_change_at = None
    prev = None
    for h in price_points:
        p = float(h.price)
        if prev is not None and p != prev:
            changes += 1
            last_change_at = h.observed_at
        prev = p

    change_abs = change_pct = None
    if initial is not None and current is not None:
        change_abs = round(current - initial, 2)
        change_pct = round(change_abs / initial * 100, 2) if initial else None

    converted = {}
    if current is not None:
        in_try = to_try(db, current, listing.currency)
        if in_try is not None:
            for code in get_settings().display_currencies:
                if code == listing.currency:
                    continue
                value = convert_from_try(db, in_try, code)
                if value is not None:
                    converted[code] = round(value, 0)

    return PriceInfo(
        initial_price=initial,
        current_price=current,
        currency=listing.currency,
        change_abs=change_abs,
        change_pct=change_pct,
        price_changes_count=changes,
        last_change_at=last_change_at,
        days_in_db=(utcnow() - listing.first_seen_at).days,
        converted=converted,
    )


def build_freshness(listing: Listing) -> FreshnessInfo:
    last_changed = None
    for h in reversed(listing.history):
        if h.changed_fields:
            last_changed = h.observed_at
            break
    return FreshnessInfo(
        first_seen_at=listing.first_seen_at,
        last_seen_at=listing.last_seen_at,
        last_checked_at=listing.last_checked_at,
        last_changed_at=last_changed,
        status=listing.status,
    )


def build_detail(db: Session, listing: Listing) -> ListingDetail:
    detail = ListingDetail.model_validate(listing, from_attributes=True)
    detail.source_code = listing.source.code
    detail.price_info = build_price_info(db, listing)
    detail.freshness = build_freshness(listing)
    return detail
