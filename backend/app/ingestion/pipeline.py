"""Ingestion pipeline: инкрементальная синхронизация одного источника.

Двухступенчатая схема:
  1. fetch_index() — лёгкий список external_id (+fingerprint).
  2. Diff с БД: NEW / CHANGED / EXISTING / MISSING.
  3. Полная загрузка и нормализация — только для NEW и CHANGED.
  4. MISSING — переходы статусов с подтверждением (lifecycle).
"""
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Listing, ListingFeature, ListingHistory, ListingImage, Source
from app.normalization.locations import resolve_locations
from app.normalization.prices import price_per_m2
from app.ingestion.lifecycle import next_check_at, register_miss, register_seen, utcnow
from app.schemas.normalized import NormalizedListing
from app.sources.base import ListingSource, load_adapter

log = logging.getLogger(__name__)

# Поля Listing, обновляемые из NormalizedListing при повторной обработке.
_SYNCED_FIELDS = [
    "original_url", "transaction_type", "property_type", "title", "description",
    "price", "currency", "gross_area_m2", "net_area_m2", "rooms", "bedrooms",
    "bathrooms", "building_age", "floor", "total_floors", "heating", "furnished",
    "balcony", "elevator", "parking", "pool", "residential_complex", "deed_status",
    "distance_to_sea_m", "address_text", "latitude", "longitude", "seller_type",
    "agency_name", "publication_date", "source_updated_at",
]
# Изменение этих полей фиксируется отдельной записью в listing_history.
_HISTORY_FIELDS = {"price", "currency", "gross_area_m2", "net_area_m2"}


@dataclass
class SyncStats:
    source: str = ""
    total_in_index: int = 0
    new: int = 0
    updated: int = 0
    unchanged: int = 0
    missing: int = 0
    status_changes: dict[str, int] = field(default_factory=dict)


def _json_safe(value):
    """Decimal/date/datetime -> сериализуемые типы для JSON-колонок."""
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):  # date / datetime
        return value.isoformat()
    return value


def normalized_fingerprint(nl: NormalizedListing) -> str:
    """Стабильный hash ключевых нормализованных полей — fallback-детектор изменений."""
    key = {f: getattr(nl, f) for f in _SYNCED_FIELDS}
    return hashlib.sha256(json.dumps(key, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _add_history(db: Session, listing: Listing, now: datetime, changed: dict | None = None) -> None:
    db.add(
        ListingHistory(
            listing_id=listing.id,
            observed_at=now,
            price=listing.price,
            currency=listing.currency,
            status=listing.status,
            gross_area_m2=listing.gross_area_m2,
            net_area_m2=listing.net_area_m2,
            changed_fields=changed,
        )
    )


def _apply_normalized(db: Session, listing: Listing, nl: NormalizedListing) -> dict:
    """Переносит NormalizedListing в колонки. Возвращает {поле: (старое, новое)}."""
    changed: dict[str, tuple] = {}
    for f in _SYNCED_FIELDS:
        old, new = getattr(listing, f), getattr(nl, f)
        if old is not None and not isinstance(old, (dict, list)) and old != new:
            # сравнение с приведением Numeric/Decimal к float
            try:
                if float(old) == float(new):  # type: ignore[arg-type]
                    continue
            except (TypeError, ValueError):
                pass
        if old != new:
            changed[f] = (old, new)
        setattr(listing, f, new)

    prov, dist, hood = resolve_locations(db, nl.province, nl.district, nl.neighbourhood)
    listing.province_id = prov.id if prov else None
    listing.district_id = dist.id if dist else None
    listing.neighbourhood_id = hood.id if hood else None

    listing.price_per_gross_m2 = price_per_m2(nl.price, nl.gross_area_m2)
    listing.price_per_net_m2 = price_per_m2(nl.price, nl.net_area_m2)
    listing.raw_data = nl.raw_data

    # изображения и характеристики — полная замена текущего набора
    listing.images = [
        ListingImage(url=img.url, storage=img.storage, position=img.position, meta=img.meta)
        for img in nl.images
    ]
    listing.features = [ListingFeature(name=k, value=v) for k, v in nl.features.items()]
    return changed


async def sync_source(db: Session, source_row: Source, adapter: ListingSource | None = None) -> SyncStats:
    """Полный инкрементальный цикл для одного источника."""
    adapter = adapter or load_adapter(source_row.adapter, source_row.config)
    stats = SyncStats(source=source_row.code)
    now = utcnow()

    index = await adapter.fetch_index()
    stats.total_in_index = len(index)

    existing_rows = db.scalars(select(Listing).where(Listing.source_id == source_row.id)).all()
    by_external = {l.external_id: l for l in existing_rows}
    index_ids = {e.external_id for e in index}

    for entry in index:
        listing = by_external.get(entry.external_id)

        if listing is None:  # -------- NEW --------
            raw = await adapter.fetch_listing(entry.external_id)
            nl = await adapter.normalize(raw)
            listing = Listing(
                source_id=source_row.id,
                external_id=nl.external_id,
                first_seen_at=now,
                last_seen_at=now,
                last_checked_at=now,
                status="active",
            )
            _apply_normalized(db, listing, nl)
            listing.fingerprint = entry.fingerprint or normalized_fingerprint(nl)
            listing.next_check_at = next_check_at(listing, now)
            db.add(listing)
            db.flush()
            _add_history(db, listing, now)  # первичное наблюдение
            stats.new += 1
            continue

        # -------- EXISTING --------
        reactivated = register_seen(listing)
        listing.last_seen_at = now

        fingerprint_changed = bool(entry.fingerprint) and entry.fingerprint != listing.fingerprint
        due_for_recheck = listing.next_check_at is None or listing.next_check_at <= now

        if fingerprint_changed or due_for_recheck or reactivated:
            raw = await adapter.fetch_listing(entry.external_id)
            nl = await adapter.normalize(raw)
            changed = _apply_normalized(db, listing, nl)
            listing.fingerprint = entry.fingerprint or normalized_fingerprint(nl)
            listing.last_checked_at = now
            history_worthy = {k: v for k, v in changed.items() if k in _HISTORY_FIELDS}
            if history_worthy or reactivated:
                extra = {k: [_json_safe(v[0]), _json_safe(v[1])] for k, v in changed.items()}
                _add_history(db, listing, now, changed=extra or None)
                stats.updated += 1
                if reactivated:
                    stats.status_changes["active"] = stats.status_changes.get("active", 0) + 1
            elif changed:
                stats.updated += 1
            else:
                stats.unchanged += 1
        else:
            stats.unchanged += 1

        listing.next_check_at = next_check_at(listing, now)

    # -------- MISSING (возможно снято с публикации) --------
    for ext_id, listing in by_external.items():
        if ext_id in index_ids or listing.status == "inactive":
            continue
        new_status = register_miss(listing)
        listing.last_checked_at = now
        listing.next_check_at = next_check_at(listing, now)
        stats.missing += 1
        if new_status:
            _add_history(db, listing, now, changed={"status": new_status})
            stats.status_changes[new_status] = stats.status_changes.get(new_status, 0) + 1

    await adapter.close()
    db.commit()
    log.info("sync %s: %s", source_row.code, stats)
    return stats


async def sync_all_enabled(db: Session) -> list[SyncStats]:
    """Синхронизация всех включённых источников. Ошибка одного не роняет остальные."""
    results = []
    for source_row in db.scalars(select(Source).where(Source.enabled)).all():
        try:
            results.append(await sync_source(db, source_row))
        except NotImplementedError as exc:
            log.warning("source %s skipped: %s", source_row.code, exc)
        except Exception:
            db.rollback()
            log.exception("source %s failed", source_row.code)
    return results
