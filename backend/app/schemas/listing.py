"""Схемы ответов API."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    level: str
    name: str
    slug: str


class ImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    url: str
    storage: str
    position: int


class PriceInfo(BaseModel):
    """Аналитика цены по listing_history."""

    initial_price: float | None = None
    current_price: float | None = None
    currency: str = "TRY"
    change_abs: float | None = None      # текущая − первоначальная (минус = снижение)
    change_pct: float | None = None
    price_changes_count: int = 0
    last_change_at: datetime | None = None
    days_in_db: int = 0
    converted: dict[str, float] = {}     # приблизительно, в display-валютах


class FreshnessInfo(BaseModel):
    first_seen_at: datetime
    last_seen_at: datetime
    last_checked_at: datetime
    last_changed_at: datetime | None = None
    status: str


class ListingCard(BaseModel):
    """Компактная карточка для списка/карты."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_type: str
    property_type: str
    title: str | None
    price: float | None
    currency: str
    price_per_gross_m2: float | None
    price_per_net_m2: float | None
    gross_area_m2: float | None
    net_area_m2: float | None
    rooms: str | None
    floor: int | None
    total_floors: int | None
    building_age: int | None
    furnished: bool | None
    pool: bool | None
    balcony: bool | None
    parking: bool | None
    latitude: float | None
    longitude: float | None
    status: str
    first_seen_at: datetime
    last_checked_at: datetime
    province: LocationOut | None = None
    district: LocationOut | None = None
    neighbourhood: LocationOut | None = None
    images: list[ImageOut] = []


class ListingDetail(ListingCard):
    description: str | None
    bedrooms: int | None
    bathrooms: int | None
    heating: str | None
    elevator: bool | None
    residential_complex: str | None
    deed_status: str | None
    distance_to_sea_m: int | None
    address_text: str | None
    seller_type: str | None
    agency_name: str | None
    publication_date: date | None
    source_code: str = ""
    external_id: str
    original_url: str | None
    price_info: PriceInfo | None = None
    freshness: FreshnessInfo | None = None
    features: dict[str, str | None] = {}

    @field_validator("features", mode="before")
    @classmethod
    def _features_from_orm(cls, v):
        if isinstance(v, list):  # список ListingFeature из ORM
            return {f.name: f.value for f in v}
        return v


class HistoryPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    observed_at: datetime
    price: float | None
    currency: str | None
    status: str | None
    gross_area_m2: float | None
    net_area_m2: float | None
    changed_fields: dict | None = None


class ListingPage(BaseModel):
    items: list[ListingCard]
    total: int
    page: int
    per_page: int


class MapPoint(BaseModel):
    id: int
    latitude: float
    longitude: float
    price: float | None
    currency: str
    rooms: str | None
