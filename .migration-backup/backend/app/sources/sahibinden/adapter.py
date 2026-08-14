"""Адаптер Sahibinden — контракт без реализации доступа.

Sahibinden технически и юридически ограничивает автоматический доступ к сайту.
Платформа сознательно НЕ реализует и не будет реализовывать обход этих
ограничений (CAPTCHA, антибот, rate limit, прокси, поддельные аккаунты).

Адаптер активируется только при появлении разрешённого канала данных:
  - официальный API / партнёрская программа;
  - лицензированный доступ к данным;
  - экспорт от агентств, размещающих объявления на портале.

Когда канал появится, реализуется только этот модуль (client/parser/normalizer) —
остальная платформа не меняется. До этого источник должен быть выключен в БД
(sources.enabled = false).
"""
from app.schemas.normalized import IndexEntry, NormalizedListing
from app.sources.base import ListingSource


class SahibindenSource(ListingSource):
    code = "sahibinden"

    _MESSAGE = (
        "Sahibinden adapter is a placeholder: no authorized data channel is configured. "
        "Enable it only with an official API / licensed feed (see module docstring)."
    )

    async def fetch_index(self) -> list[IndexEntry]:
        raise NotImplementedError(self._MESSAGE)

    async def fetch_listing(self, external_id: str) -> dict:
        raise NotImplementedError(self._MESSAGE)

    async def normalize(self, raw_data: dict) -> NormalizedListing:
        raise NotImplementedError(self._MESSAGE)
