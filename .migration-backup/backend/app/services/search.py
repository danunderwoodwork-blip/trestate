"""Поиск по нормализованным колонкам нашей БД. Никаких внешних запросов."""
from datetime import timedelta

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, aliased, selectinload

from app.ingestion.lifecycle import utcnow
from app.models import Listing, ListingHistory, Location
from app.schemas.filters import ListingFilters

_SORTS = {
    "newest": Listing.first_seen_at.desc(),
    "oldest": Listing.first_seen_at.asc(),
    "price_asc": Listing.price.asc(),
    "price_desc": Listing.price.desc(),
    "ppm2_asc": Listing.price_per_gross_m2.asc(),
}


def _location_filter(stmt: Select, column, slug: str) -> Select:
    loc = aliased(Location)
    return stmt.join(loc, column == loc.id).where(loc.slug == slug)


def build_query(f: ListingFilters) -> Select:
    stmt = select(Listing)

    if f.status:
        stmt = stmt.where(Listing.status == f.status)
    if f.transaction_type:
        stmt = stmt.where(Listing.transaction_type == f.transaction_type)
    if f.property_type:
        stmt = stmt.where(Listing.property_type == f.property_type)
    if f.province:
        stmt = _location_filter(stmt, Listing.province_id, f.province)
    if f.district:
        stmt = _location_filter(stmt, Listing.district_id, f.district)
    if f.neighbourhood:
        stmt = _location_filter(stmt, Listing.neighbourhood_id, f.neighbourhood)
    if f.currency:
        stmt = stmt.where(Listing.currency == f.currency)
    if f.min_price is not None:
        stmt = stmt.where(Listing.price >= f.min_price)
    if f.max_price is not None:
        stmt = stmt.where(Listing.price <= f.max_price)
    if f.min_m2 is not None:
        stmt = stmt.where(Listing.net_area_m2 >= f.min_m2)
    if f.max_m2 is not None:
        stmt = stmt.where(Listing.net_area_m2 <= f.max_m2)
    if f.rooms:
        stmt = stmt.where(Listing.rooms.in_(f.rooms))
    if f.min_floor is not None:
        stmt = stmt.where(Listing.floor >= f.min_floor)
    if f.max_floor is not None:
        stmt = stmt.where(Listing.floor <= f.max_floor)
    if f.max_building_age is not None:
        stmt = stmt.where(Listing.building_age <= f.max_building_age)
    for flag in ("furnished", "pool", "parking", "balcony", "elevator"):
        val = getattr(f, flag)
        if val is not None:
            stmt = stmt.where(getattr(Listing, flag).is_(val))
    if f.max_distance_to_sea_m is not None:
        stmt = stmt.where(Listing.distance_to_sea_m <= f.max_distance_to_sea_m)
    if f.max_price_per_m2 is not None:
        stmt = stmt.where(Listing.price_per_gross_m2 <= f.max_price_per_m2)
    if f.max_days_in_db is not None:
        stmt = stmt.where(Listing.first_seen_at >= utcnow() - timedelta(days=f.max_days_in_db))
    if f.only_price_drops:
        first_price = (
            select(ListingHistory.price)
            .where(ListingHistory.listing_id == Listing.id)
            .order_by(ListingHistory.observed_at.asc())
            .limit(1)
            .scalar_subquery()
        )
        stmt = stmt.where(Listing.price < first_price)
    if f.q:
        # MVP: LIKE-поиск; на PostgreSQL заменяется на full-text (to_tsvector) без изменения API
        pattern = f"%{f.q}%"
        stmt = stmt.where(or_(Listing.title.ilike(pattern), Listing.description.ilike(pattern)))

    return stmt


def search_listings(db: Session, f: ListingFilters) -> tuple[list[Listing], int]:
    stmt = build_query(f)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.order_by(_SORTS.get(f.sort, _SORTS["newest"]))
        .offset((f.page - 1) * f.per_page)
        .limit(f.per_page)
        .options(
            selectinload(Listing.images),
            selectinload(Listing.province),
            selectinload(Listing.district),
            selectinload(Listing.neighbourhood),
        )
    )
    return list(db.scalars(stmt).all()), total
