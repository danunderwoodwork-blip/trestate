"""Демо-источник: агентский JSON-фид, поставляемый вместе с репозиторием.

Используется для сидинга дев-среды и как пример подключения нового источника.
"""
from pathlib import Path

from app.sources.agency_feed.importer import AgencyFeedSource

_SAMPLE = Path(__file__).parent / "sample_data.json"


class MockSource(AgencyFeedSource):
    code = "mock"

    def __init__(self, config: dict | None = None):
        cfg = {"feed_url": f"file://{_SAMPLE}", "format": "json", "code": "mock"}
        cfg.update(config or {})
        super().__init__(cfg)
