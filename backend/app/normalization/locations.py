"""Нормализация географии и резолвинг в иерархию locations.

Алиасы: 'MAHMUTLAR', 'Mahmutlar Mah.', 'Mahmutlar Mahallesi' -> Neighbourhood
Mahmutlar (Alanya, Antalya). Словарь расширяется по мере подключения регионов.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Location
from app.normalization.text import fold, slugify

# folded alias -> (province, district, neighbourhood|None)
# MVP-география: Turkey -> Antalya -> Alanya.
KNOWN_PLACES: dict[str, tuple[str, str, str | None]] = {
    "alanya": ("Antalya", "Alanya", None),
    "mahmutlar": ("Antalya", "Alanya", "Mahmutlar"),
    "oba": ("Antalya", "Alanya", "Oba"),
    "kestel": ("Antalya", "Alanya", "Kestel"),
    "tosmur": ("Antalya", "Alanya", "Tosmur"),
    "cikcilli": ("Antalya", "Alanya", "Cikcilli"),
    "avsallar": ("Antalya", "Alanya", "Avsallar"),
    "kargicak": ("Antalya", "Alanya", "Kargicak"),
    "demirtas": ("Antalya", "Alanya", "Demirtas"),
    "payallar": ("Antalya", "Alanya", "Payallar"),
    "konakli": ("Antalya", "Alanya", "Konakli"),
    "saray": ("Antalya", "Alanya", "Saray"),
    "hacet": ("Antalya", "Alanya", "Hacet"),
}


def canonicalize(
    province: str | None, district: str | None, neighbourhood: str | None
) -> tuple[str | None, str | None, str | None]:
    """Приводит сырые названия к каноническим. Сначала — точечный словарь алиасов."""
    if neighbourhood and (hit := KNOWN_PLACES.get(fold(neighbourhood))):
        return hit
    if district and (hit := KNOWN_PLACES.get(fold(district))):
        return hit[0], hit[1], neighbourhood and neighbourhood.strip().title() or hit[2]
    return (
        province and province.strip().title(),
        district and district.strip().title(),
        neighbourhood and neighbourhood.strip().title(),
    )


def _get_or_create(
    db: Session, level: str, name: str, parent: Location | None
) -> Location:
    # слаг строится от province и ниже: 'antalya', 'antalya-alanya', 'antalya-alanya-mahmutlar'
    use_parent = parent is not None and parent.level != "country"
    slug = slugify(*([parent.slug] if use_parent else []), name)
    loc = db.scalar(select(Location).where(Location.slug == slug))
    if loc is None:
        loc = Location(
            parent_id=parent.id if parent else None, level=level, name=name, slug=slug
        )
        db.add(loc)
        db.flush()
    return loc


def resolve_locations(
    db: Session,
    province: str | None,
    district: str | None,
    neighbourhood: str | None,
) -> tuple[Location | None, Location | None, Location | None]:
    """Резолвит (и при необходимости создаёт) цепочку country->province->district->neighbourhood."""
    province, district, neighbourhood = canonicalize(province, district, neighbourhood)
    country = _get_or_create(db, "country", "Turkey", None)
    prov = _get_or_create(db, "province", province, country) if province else None
    dist = _get_or_create(db, "district", district, prov) if district and prov else None
    hood = _get_or_create(db, "neighbourhood", neighbourhood, dist) if neighbourhood and dist else None
    return prov, dist, hood
