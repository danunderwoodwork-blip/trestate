from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DbDep, UserDep
from app.ingestion.lifecycle import utcnow
from app.models import Favorite, Listing
from app.schemas.listing import ListingCard

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


class FavoriteIn(BaseModel):
    listing_id: int


@router.get("", response_model=list[ListingCard])
def list_favorites(db: DbDep, user: UserDep):
    listings = db.scalars(
        select(Listing)
        .join(Favorite, Favorite.listing_id == Listing.id)
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
    ).all()
    return [ListingCard.model_validate(l, from_attributes=True) for l in listings]


@router.post("", status_code=201)
def add_favorite(payload: FavoriteIn, db: DbDep, user: UserDep):
    if db.get(Listing, payload.listing_id) is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    exists = db.scalar(
        select(Favorite).where(
            Favorite.user_id == user.id, Favorite.listing_id == payload.listing_id
        )
    )
    if exists is None:
        db.add(Favorite(user_id=user.id, listing_id=payload.listing_id, created_at=utcnow()))
        db.commit()
    return {"ok": True}


@router.delete("/{listing_id}", status_code=204)
def remove_favorite(listing_id: int, db: DbDep, user: UserDep):
    fav = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.listing_id == listing_id)
    )
    if fav:
        db.delete(fav)
        db.commit()
