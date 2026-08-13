from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbDep
from app.core.config import get_settings
from app.models import ExchangeRate, Location

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/locations")
def location_tree(db: DbDep):
    """Дерево географии для фильтров."""
    locations = db.scalars(select(Location).order_by(Location.level, Location.name)).all()
    by_parent: dict[int | None, list[Location]] = {}
    for loc in locations:
        by_parent.setdefault(loc.parent_id, []).append(loc)

    def node(loc: Location) -> dict:
        return {
            "id": loc.id,
            "level": loc.level,
            "name": loc.name,
            "slug": loc.slug,
            "children": [node(c) for c in by_parent.get(loc.id, [])],
        }

    return [node(root) for root in by_parent.get(None, [])]


@router.get("/meta")
def meta(db: DbDep):
    """Справочники и последние курсы валют."""
    settings = get_settings()
    rates = {}
    for code in settings.display_currencies:
        if code == "TRY":
            continue
        rate = db.scalar(
            select(ExchangeRate)
            .where(ExchangeRate.currency_code == code)
            .order_by(ExchangeRate.fetched_at.desc())
            .limit(1)
        )
        if rate:
            rates[code] = {"rate_to_try": float(rate.rate_to_try), "fetched_at": rate.fetched_at}
    return {
        "transaction_types": ["sale", "rent_long", "rent_short"],
        "property_types": ["apartment", "house", "villa", "commercial", "land"],
        "currencies": settings.display_currencies,
        "exchange_rates": rates,
        "sorts": ["newest", "oldest", "price_asc", "price_desc", "ppm2_asc"],
    }
