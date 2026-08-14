from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbDep
from app.models import Listing
from app.api.routes.listings import parse_filters
from app.schemas.filters import ListingFilters
from app.schemas.listing import MapPoint
from app.services.search import build_query

router = APIRouter(prefix="/api/map", tags=["map"])


@router.get("", response_model=list[MapPoint])
def map_points(
    db: DbDep,
    filters: Annotated[ListingFilters, Depends(parse_filters)],
    min_lat: float | None = Query(default=None),
    max_lat: float | None = Query(default=None),
    min_lon: float | None = Query(default=None),
    max_lon: float | None = Query(default=None),
    limit: int = Query(default=500, le=2000),
):
    stmt = build_query(filters).where(Listing.latitude.is_not(None), Listing.longitude.is_not(None))
    if min_lat is not None:
        stmt = stmt.where(Listing.latitude >= min_lat)
    if max_lat is not None:
        stmt = stmt.where(Listing.latitude <= max_lat)
    if min_lon is not None:
        stmt = stmt.where(Listing.longitude >= min_lon)
    if max_lon is not None:
        stmt = stmt.where(Listing.longitude <= max_lon)
    rows = db.scalars(stmt.limit(limit)).all()
    return [
        MapPoint(
            id=l.id,
            latitude=l.latitude,
            longitude=l.longitude,
            price=float(l.price) if l.price is not None else None,
            currency=l.currency,
            rooms=l.rooms,
        )
        for l in rows
    ]
