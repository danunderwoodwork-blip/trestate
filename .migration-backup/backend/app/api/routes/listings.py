from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import DbDep
from app.schemas.filters import ListingFilters
from app.schemas.listing import HistoryPoint, ListingCard, ListingDetail, ListingPage
from app.services.listings import build_detail, get_listing
from app.services.search import search_listings

router = APIRouter(prefix="/api/listings", tags=["listings"])


def parse_filters(
    rooms: Annotated[list[str] | None, Query()] = None,
    filters: ListingFilters = Depends(),
) -> ListingFilters:
    # list-параметр (rooms=2+1&rooms=3+1) собирается отдельно от скалярных Depends-полей
    filters.rooms = rooms
    return filters


@router.get("", response_model=ListingPage)
def list_listings(db: DbDep, filters: Annotated[ListingFilters, Depends(parse_filters)]):
    items, total = search_listings(db, filters)
    return ListingPage(
        items=[ListingCard.model_validate(i, from_attributes=True) for i in items],
        total=total,
        page=filters.page,
        per_page=filters.per_page,
    )


@router.get("/{listing_id}", response_model=ListingDetail)
def listing_detail(listing_id: int, db: DbDep):
    listing = get_listing(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return build_detail(db, listing)


@router.get("/{listing_id}/history", response_model=list[HistoryPoint])
def listing_history(listing_id: int, db: DbDep):
    listing = get_listing(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return [HistoryPoint.model_validate(h, from_attributes=True) for h in listing.history]
