"""Импорт XML/CSV/JSON-фидов агентств недвижимости.

Конфигурация (sources.config):
    {
      "feed_url": "https://agency.example/feed.json"  # или file://путь
      "format": "json" | "xml" | "csv",
      "root_tag": "listing",          # для xml
      "field_map": {...}              # переименование полей фида -> наши ключи
    }
"""
import csv
import hashlib
import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx

from app.schemas.normalized import IndexEntry, NormalizedListing
from app.sources.agency_feed.normalizer import normalize_feed_record
from app.sources.base import ListingSource


class AgencyFeedSource(ListingSource):
    code = "agency_feed"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.code = self.config.get("code", self.code)
        self._records: dict[str, dict] | None = None

    async def _load(self) -> dict[str, dict]:
        if self._records is not None:
            return self._records
        url = self.config["feed_url"]
        if url.startswith("file://"):
            content = Path(url[7:]).read_text(encoding="utf-8")
        else:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                content = resp.text
        fmt = self.config.get("format", "json")
        field_map: dict = self.config.get("field_map", {})

        if fmt == "json":
            rows = json.loads(content)
            if isinstance(rows, dict):  # {"listings": [...]}
                rows = next(v for v in rows.values() if isinstance(v, list))
        elif fmt == "xml":
            root = ET.fromstring(content)
            rows = [
                {child.tag: (child.text or "").strip() for child in item}
                for item in root.iter(self.config.get("root_tag", "listing"))
            ]
        elif fmt == "csv":
            rows = list(csv.DictReader(io.StringIO(content)))
        else:
            raise ValueError(f"Unsupported feed format: {fmt}")

        records = {}
        for row in rows:
            mapped = {field_map.get(k, k): v for k, v in row.items()}
            ext_id = str(mapped.get("id") or mapped.get("external_id"))
            records[ext_id] = mapped
        self._records = records
        return records

    async def fetch_index(self) -> list[IndexEntry]:
        records = await self._load()
        return [
            IndexEntry(
                external_id=ext_id,
                fingerprint=hashlib.sha256(
                    json.dumps(rec, sort_keys=True, default=str).encode()
                ).hexdigest()[:16],
            )
            for ext_id, rec in records.items()
        ]

    async def fetch_listing(self, external_id: str) -> dict:
        records = await self._load()
        return records[external_id]

    async def normalize(self, raw_data: dict) -> NormalizedListing:
        return normalize_feed_record(self.code, raw_data)
