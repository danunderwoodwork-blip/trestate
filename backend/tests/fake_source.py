"""Тестовый источник: in-memory записи в формате агентского фида."""
import hashlib
import json

from app.schemas.normalized import IndexEntry, NormalizedListing
from app.sources.agency_feed.normalizer import normalize_feed_record
from app.sources.base import ListingSource


def make_record(ext_id: str, **overrides) -> dict:
    base = {
        "id": ext_id,
        "transaction_type": "Satılık",
        "property_type": "Daire",
        "title": f"Mahmutlar 2+1 daire {ext_id}",
        "description": "Havuzlu sitede daire",
        "price": "5500000",
        "currency": "TL",
        "gross_m2": "120",
        "net_m2": "105",
        "rooms": "2+1",
        "floor": "4",
        "total_floors": "9",
        "building_age": "5",
        "furnished": "Evet",
        "pool": "Var",
        "balcony": "Var",
        "province": "Antalya",
        "district": "Alanya",
        "neighbourhood": "Mahmutlar Mah.",
        "latitude": "36.49",
        "longitude": "32.09",
    }
    base.update(overrides)
    return base


class FakeSource(ListingSource):
    code = "fake"

    def __init__(self, records: dict[str, dict]):
        super().__init__()
        self.records = records
        self.full_fetches: list[str] = []  # для проверки инкрементальности

    async def fetch_index(self) -> list[IndexEntry]:
        return [
            IndexEntry(
                external_id=ext_id,
                fingerprint=hashlib.sha256(
                    json.dumps(rec, sort_keys=True).encode()
                ).hexdigest()[:16],
            )
            for ext_id, rec in self.records.items()
        ]

    async def fetch_listing(self, external_id: str) -> dict:
        self.full_fetches.append(external_id)
        return self.records[external_id]

    async def normalize(self, raw_data: dict) -> NormalizedListing:
        return normalize_feed_record("fake", raw_data)
