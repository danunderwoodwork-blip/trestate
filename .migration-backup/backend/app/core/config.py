"""Конфигурация приложения. Все интервалы обновления настраиваются здесь/через env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TRE_", extra="ignore")

    app_name: str = "TREstate"
    debug: bool = False

    # dev/tests — SQLite; prod — postgresql+psycopg2://user:pass@host/trestate
    database_url: str = "sqlite:///./trestate.db"

    # --- Инкрементальное обновление / lifecycle ---
    # Сколько подряд «пропусков» в индексе переводят possibly_inactive -> inactive.
    inactive_after_misses: int = 2

    # Адаптивный график перепроверки: (макс. возраст в днях, интервал в часах).
    # Последнее правило — для всего, что старше.
    recheck_schedule: list[tuple[int, int]] = [
        (7, 24),      # 0–7 дней: ежедневно
        (30, 36),     # 8–30 дней: раз в 1.5 суток
        (90, 60),     # 31–90 дней: раз в 2.5 суток
        (10**9, 96),  # 90+ дней: раз в 4 суток
    ]
    # Множитель интервала по типу сделки (аренда — чаще, продажа — реже).
    recheck_multiplier: dict[str, float] = {
        "rent_long": 1.0,
        "rent_short": 1.0,
        "sale": 1.5,
    }

    # --- Валюты ---
    display_currencies: list[str] = ["TRY", "USD", "EUR"]

    # --- Изображения ---
    image_storage_mode: str = "remote_url"  # local_s3 | remote_url | feed
    s3_endpoint: str = ""
    s3_bucket: str = ""

    # --- Дедупликация (эвристика MVP) ---
    dedup_price_tolerance: float = 0.12   # ±12% к цене
    dedup_area_tolerance: float = 0.05    # ±5% к площади
    dedup_min_score: float = 0.8


@lru_cache
def get_settings() -> Settings:
    return Settings()
