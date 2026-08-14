"""Поиск дубликатов (MVP-эвристика).

Один физический объект может публиковаться владельцем, несколькими агентствами
и на нескольких площадках. Сходство считается по: район + площадь + комнатность +
этаж + цена + текст. Позже добавляются perceptual image hashing и embeddings.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ingestion.lifecycle import utcnow
from app.models import DuplicateGroup, Listing
from app.normalization.text import fold


def _close(a: float | None, b: float | None, tolerance: float) -> bool:
    if a is None or b is None:
        return False
    hi, lo = max(a, b), min(a, b)
    return hi > 0 and (hi - lo) / hi <= tolerance


def similarity(a: Listing, b: Listing) -> float:
    """0..1 — насколько вероятно, что это один объект."""
    s = get_settings()
    score, weight = 0.0, 0.0

    checks: list[tuple[float, bool]] = [
        (0.25, a.neighbourhood_id is not None and a.neighbourhood_id == b.neighbourhood_id),
        (0.20, _close(_f(a.net_area_m2), _f(b.net_area_m2), s.dedup_area_tolerance)),
        (0.15, bool(a.rooms) and a.rooms == b.rooms),
        (0.10, a.floor is not None and a.floor == b.floor),
        (0.20, _close(_f(a.price), _f(b.price), s.dedup_price_tolerance)),
        (0.10, _text_overlap(a.title, b.title) >= 0.5),
    ]
    for w, ok in checks:
        weight += w
        if ok:
            score += w
    return score / weight if weight else 0.0


def _f(v) -> float | None:
    return float(v) if v is not None else None


def _text_overlap(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    ta, tb = set(fold(a).split()), set(fold(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def find_duplicates(db: Session, listing: Listing) -> list[Listing]:
    """Кандидаты в дубликаты среди активных объявлений того же района и типа."""
    s = get_settings()
    candidates = db.scalars(
        select(Listing).where(
            Listing.id != listing.id,
            Listing.status == "active",
            Listing.transaction_type == listing.transaction_type,
            Listing.property_type == listing.property_type,
            Listing.neighbourhood_id == listing.neighbourhood_id,
        )
    ).all()
    return [c for c in candidates if similarity(listing, c) >= s.dedup_min_score]


def group_duplicates(db: Session, listing: Listing, duplicates: list[Listing]) -> None:
    """Объединяет объявления в duplicate_group (создаёт при необходимости)."""
    group_id = next(
        (l.duplicate_group_id for l in [listing, *duplicates] if l.duplicate_group_id), None
    )
    if group_id is None:
        group = DuplicateGroup(created_at=utcnow())
        db.add(group)
        db.flush()
        group_id = group.id
    for l in [listing, *duplicates]:
        l.duplicate_group_id = group_id
