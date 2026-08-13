"""Единый контракт для всех источников данных.

Любой источник (официальный API, XML/CSV/JSON-feed агентства, сайт застройщика,
лицензированный доступ к порталу) подключается как реализация ListingSource.
Замена способа импорта для источника меняет только его адаптер — ingestion,
нормализация, БД, API и frontend не затрагиваются.

Платформа НЕ содержит механизмов обхода технических ограничений сайтов
(CAPTCHA, антибот, rate limit, fingerprinting и т.п.). Если источник запрещает
или блокирует автоматический доступ — для него используется альтернативный
разрешённый канал (API/feed/лицензия), либо источник остаётся отключённым.
"""
from abc import ABC, abstractmethod
from importlib import import_module

from app.schemas.normalized import IndexEntry, NormalizedListing


class ListingSource(ABC):
    """Контракт адаптера источника."""

    #: код источника, совпадает с sources.code в БД
    code: str = ""

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abstractmethod
    async def fetch_index(self) -> list[IndexEntry]:
        """Шаг 1: лёгкий список объявлений (id + сигнал изменения), без полной загрузки."""

    @abstractmethod
    async def fetch_listing(self, external_id: str) -> dict:
        """Шаг 2: полные сырые данные одного объявления (сохраняются в raw_data)."""

    @abstractmethod
    async def normalize(self, raw_data: dict) -> NormalizedListing:
        """Преобразование сырых данных в универсальную модель."""

    async def close(self) -> None:
        """Освобождение ресурсов (http-клиенты и т.п.)."""


def load_adapter(path: str, config: dict | None = None) -> ListingSource:
    """Инстанцирует адаптер по строке 'module.path:ClassName' из sources.adapter."""
    module_path, _, class_name = path.partition(":")
    cls = getattr(import_module(module_path), class_name)
    if not issubclass(cls, ListingSource):
        raise TypeError(f"{path} is not a ListingSource")
    return cls(config)
