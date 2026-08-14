"""Нормализация записи агентского фида в NormalizedListing."""
from datetime import date, datetime

from app.normalization.mappings import (
    normalize_currency,
    normalize_heating,
    normalize_property_type,
    normalize_rooms,
    normalize_transaction,
    parse_bool,
    parse_float,
    parse_int,
)
from app.schemas.normalized import NormalizedImage, NormalizedListing


def _parse_date(value) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def normalize_feed_record(source_code: str, raw: dict) -> NormalizedListing:
    rooms, bedrooms = normalize_rooms(raw.get("rooms"))
    images = raw.get("images") or []
    if isinstance(images, str):
        images = [u.strip() for u in images.split("|") if u.strip()]

    return NormalizedListing(
        source=source_code,
        external_id=str(raw.get("id") or raw.get("external_id")),
        original_url=raw.get("url"),
        transaction_type=normalize_transaction(raw.get("transaction_type")) or "sale",
        property_type=normalize_property_type(raw.get("property_type")) or "apartment",
        title=raw.get("title"),
        description=raw.get("description"),
        price=parse_float(raw.get("price")),
        currency=normalize_currency(raw.get("currency")),
        gross_area_m2=parse_float(raw.get("gross_area_m2") or raw.get("gross_m2")),
        net_area_m2=parse_float(raw.get("net_area_m2") or raw.get("net_m2")),
        rooms=rooms,
        bedrooms=bedrooms if bedrooms is not None else parse_int(raw.get("bedrooms")),
        bathrooms=parse_int(raw.get("bathrooms")),
        building_age=parse_int(raw.get("building_age")),
        floor=parse_int(raw.get("floor")),
        total_floors=parse_int(raw.get("total_floors")),
        heating=normalize_heating(raw.get("heating")),
        furnished=parse_bool(raw.get("furnished")),
        balcony=parse_bool(raw.get("balcony")),
        elevator=parse_bool(raw.get("elevator")),
        parking=parse_bool(raw.get("parking")),
        pool=parse_bool(raw.get("pool")),
        residential_complex=raw.get("residential_complex"),
        deed_status=raw.get("deed_status"),
        distance_to_sea_m=parse_int(raw.get("distance_to_sea_m")),
        province=raw.get("province"),
        district=raw.get("district"),
        neighbourhood=raw.get("neighbourhood"),
        address_text=raw.get("address"),
        latitude=parse_float(raw.get("latitude") or raw.get("lat")),
        longitude=parse_float(raw.get("longitude") or raw.get("lon")),
        seller_type=raw.get("seller_type") or "agency",
        agency_name=raw.get("agency_name"),
        publication_date=_parse_date(raw.get("publication_date")),
        source_updated_at=None,
        images=[NormalizedImage(url=u, storage="feed", position=i) for i, u in enumerate(images)],
        features={k: str(v) for k, v in (raw.get("features") or {}).items()},
        raw_data=raw,
    )
