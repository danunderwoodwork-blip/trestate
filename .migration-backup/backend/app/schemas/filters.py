from pydantic import BaseModel, Field


class ListingFilters(BaseModel):
    """Фильтры поиска. Все — по нормализованным колонкам нашей БД."""

    transaction_type: str | None = None
    property_type: str | None = None
    province: str | None = None        # slug
    district: str | None = None        # slug
    neighbourhood: str | None = None   # slug
    min_price: float | None = None
    max_price: float | None = None
    currency: str | None = None
    min_m2: float | None = None        # по net-площади
    max_m2: float | None = None
    rooms: list[str] | None = None     # ["2+1", "3+1"]
    min_floor: int | None = None
    max_floor: int | None = None
    max_building_age: int | None = None
    furnished: bool | None = None
    pool: bool | None = None
    parking: bool | None = None
    balcony: bool | None = None
    elevator: bool | None = None
    max_distance_to_sea_m: int | None = None
    max_price_per_m2: float | None = None      # по gross
    max_days_in_db: int | None = None
    only_price_drops: bool = False
    status: str = "active"
    q: str | None = None               # полнотекстовый поиск по title/description

    sort: str = Field(default="newest")  # newest|price_asc|price_desc|ppm2_asc|oldest
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
