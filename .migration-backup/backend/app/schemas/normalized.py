"""Универсальная модель, в которую каждый адаптер обязан преобразовать свой источник.

Frontend и бизнес-логика видят только её — никакой зависимости от конкретного портала.
"""
from datetime import date, datetime

from pydantic import BaseModel, Field


class NormalizedImage(BaseModel):
    url: str
    storage: str = "remote_url"  # local_s3 | remote_url | feed
    position: int = 0
    meta: dict | None = None


class NormalizedListing(BaseModel):
    source: str                      # код источника (sources.code)
    external_id: str
    original_url: str | None = None  # хранится только как метаданные происхождения

    transaction_type: str            # sale | rent_long | rent_short
    property_type: str               # apartment | house | villa | commercial | land

    title: str | None = None
    description: str | None = None

    price: float | None = None
    currency: str = "TRY"

    gross_area_m2: float | None = None
    net_area_m2: float | None = None
    rooms: str | None = None         # каноническая форма "2+1"
    bedrooms: int | None = None
    bathrooms: int | None = None
    building_age: int | None = None
    floor: int | None = None
    total_floors: int | None = None
    heating: str | None = None
    furnished: bool | None = None
    balcony: bool | None = None
    elevator: bool | None = None
    parking: bool | None = None
    pool: bool | None = None
    residential_complex: str | None = None
    deed_status: str | None = None
    distance_to_sea_m: int | None = None

    province: str | None = None      # канонические имена; резолвятся в locations
    district: str | None = None
    neighbourhood: str | None = None
    address_text: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    seller_type: str | None = None   # owner | agency | developer
    agency_name: str | None = None

    publication_date: date | None = None
    source_updated_at: datetime | None = None

    images: list[NormalizedImage] = Field(default_factory=list)
    features: dict[str, str | None] = Field(default_factory=dict)

    raw_data: dict = Field(default_factory=dict)  # оригинал источника, сохраняется как есть


class IndexEntry(BaseModel):
    """Элемент лёгкого индекса источника (шаг 1 двухступенчатой схемы)."""

    external_id: str
    # Быстрый сигнал изменения без полной загрузки: hash/updated_at/цена из списка.
    fingerprint: str | None = None
