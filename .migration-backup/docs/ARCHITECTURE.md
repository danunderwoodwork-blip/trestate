# TREstate — независимый агрегатор недвижимости Турции

## Архитектура системы

Продукт — **платформа данных о недвижимости**, а не парсер. Пользователь никогда не
взаимодействует с исходными порталами: все запросы обслуживаются нашей БД.

```
┌─────────────────────────────────────────────────────────────────┐
│  SOURCE ADAPTERS (плагины, единый интерфейс ListingSource)      │
│  sahibinden* | agency_feed (XML/CSV/JSON) | official APIs | ... │
└──────────────┬──────────────────────────────────────────────────┘
               ▼
        INGESTION PIPELINE          (инкрементальный diff, планировщик)
               ▼
        NORMALIZER                  (гео, комнатность, валюты, признаки)
               ▼
        POSTGRESQL                  (listings + history + raw_data JSONB)
               ▼
        SEARCH / ANALYTICS          (PG full-text + нормализованные колонки)
               ▼
        REST API (FastAPI)          (работает ТОЛЬКО с нашей БД)
               ▼
        FRONTEND (Next.js)          (собственный UI, независимый от источников)
```

`*` Адаптер Sahibinden — заглушка-контракт: активируется только при появлении
разрешённого канала данных (официальный API, лицензированный доступ, партнёрский
feed). Система **не** содержит и не будет содержать механизмов обхода
CAPTCHA/антибот-защиты/rate-limit. Если источник блокирует автоматический доступ —
данные для него получаются альтернативным разрешённым способом, и это меняет
только адаптер, не платформу.

### Ключевые принципы

1. **Мульти-source**: каждый источник — изолированный адаптер, реализующий
   `ListingSource`. Замена способа импорта (API → XML feed) не затрагивает ничего
   вне каталога адаптера.
2. **Пользовательский путь**: `USER → FRONTEND → API → DATABASE`. Ни одного
   обращения к внешним сайтам во время пользовательского запроса.
3. **Modular monolith**: один деплой, чёткие границы модулей
   (`sources / ingestion / normalization / services / api`). Микросервисы — только
   когда появится реальная необходимость.
4. **raw_data сохраняется всегда** (JSONB) — любую нормализацию можно перезапустить
   ретроспективно без повторного импорта.

## ER-схема

```mermaid
erDiagram
    sources ||--o{ listings : provides
    locations ||--o{ listings : "province/district/neighbourhood"
    locations ||--o{ locations : parent
    listings ||--o{ listing_history : history
    listings ||--o{ listing_images : images
    listings ||--o{ listing_features : features
    listings ||--o{ favorites : "favorited by"
    users ||--o{ favorites : has
    duplicate_groups ||--o{ listings : groups
    currencies ||--o{ exchange_rates : rates

    sources {
        int id PK
        string code UK "sahibinden, agency_feed_x, mock"
        string name
        string adapter "python-класс адаптера"
        bool enabled
        json config
    }
    locations {
        int id PK
        int parent_id FK
        string level "country|province|district|neighbourhood"
        string name
        string slug UK
        float lat
        float lon
    }
    listings {
        bigint id PK "internal_id"
        int source_id FK
        string external_id UK "уникален в паре с source_id"
        string original_url
        string transaction_type "sale|rent_long|rent_short"
        string property_type "apartment|house|villa|commercial|land"
        string title
        text description
        numeric price
        string currency
        numeric gross_area_m2
        numeric net_area_m2
        string rooms "2+1"
        int bedrooms
        int bathrooms
        int province_id FK
        int district_id FK
        int neighbourhood_id FK
        string address_text
        float latitude
        float longitude
        int building_age
        int floor
        int total_floors
        string heating
        bool furnished
        bool balcony
        bool elevator
        bool parking
        bool pool
        string residential_complex
        string deed_status
        string seller_type "owner|agency|developer"
        string agency_name
        int distance_to_sea_m
        numeric price_per_gross_m2 "вычисляется при записи"
        numeric price_per_net_m2
        date publication_date
        datetime first_seen_at
        datetime last_seen_at
        datetime last_checked_at
        datetime source_updated_at
        string status "active|possibly_inactive|inactive"
        int miss_count "подряд не найдено в индексе"
        datetime next_check_at "адаптивный график"
        string fingerprint "hash ключевых полей для detect changes"
        bigint duplicate_group_id FK
        json raw_data "оригинал источника"
    }
    listing_history {
        bigint id PK
        bigint listing_id FK
        datetime observed_at
        numeric price
        string currency
        string status
        numeric gross_area_m2
        numeric net_area_m2
        json changed_fields "diff остальных ключевых полей"
    }
    listing_images {
        bigint id PK
        bigint listing_id FK
        int position
        string storage "local_s3|remote_url|feed"
        string url "или ключ объекта в S3"
        string phash "perceptual hash (后)"
        json meta
    }
    listing_features {
        bigint id PK
        bigint listing_id FK
        string name
        string value
    }
    currencies {
        string code PK "TRY|USD|EUR"
        string symbol
    }
    exchange_rates {
        int id PK
        string currency_code FK
        numeric rate_to_try
        datetime fetched_at
    }
    users {
        bigint id PK
        string device_token UK "анонимный MVP-идентификатор"
        string email
        datetime created_at
    }
    favorites {
        bigint id PK
        bigint user_id FK
        bigint listing_id FK
        datetime created_at
    }
    duplicate_groups {
        bigint id PK
        datetime created_at
        string match_basis "geo+area+rooms+price|image|manual"
    }
```

Поисковые поля — нормализованные колонки с индексами; JSONB — только для
`raw_data`, `changed_fields`, `config`, `meta`.

## Жизненный цикл объявления

```mermaid
stateDiagram-v2
    [*] --> active : впервые найдено в индексе
    active --> active : найдено в индексе (miss_count=0)
    active --> possibly_inactive : отсутствует в индексе (miss_count=1)
    possibly_inactive --> active : снова найдено
    possibly_inactive --> inactive : отсутствует N проверок подряд (default 2)
    inactive --> active : реактивация (объявление вернулось)
```

Исчезновение подтверждается повторной проверкой — одиночный «пропуск» в индексе
никогда не приводит к немедленному `inactive`.

## Инкрементальное обновление (двухступенчатая схема)

```
1. adapter.fetch_index()  → множество {external_id, fingerprint?}
2. diff с БД:
      NEW      = index − db
      MISSING  = db(active|possibly_inactive) − index
      EXISTING = index ∩ db
      CHANGED  = EXISTING, где fingerprint отличается
                 ИЛИ next_check_at <= now (плановая перепроверка)
3. Полная загрузка (fetch_listing → normalize → upsert) — ТОЛЬКО для NEW и CHANGED.
4. MISSING → miss_count += 1 → переходы статусов (см. lifecycle).
5. Для всех найденных в индексе: last_seen_at = now, last_checked_at = now,
   next_check_at = адаптивный график.
```

### Адаптивный график перепроверки (конфигурируемый, `core/config.py`)

| Возраст объявления | Интервал проверки |
|---|---|
| 0–7 дней | 24 ч |
| 8–30 дней | 36 ч |
| 31–90 дней | 60 ч |
| 90+ дней | 96 ч |

Отдельно: аренда ~24 ч, продажа 24–48 ч (множитель на тип сделки в конфиге).
Полный snapshot не требуется — каждый цикл обрабатывает только дельту.

## История изменений

Любое изменение цены/статуса/площади при повторной обработке создаёт запись в
`listing_history` (плюс первичная запись при появлении). API отдаёт производные
метрики: первоначальная цена, текущая, абсолютное и процентное снижение, число
изменений, дата последнего изменения, дней в базе.

## Нормализация

Отдельный слой `app/normalization/`:
- **география**: `"MAHMUTLAR MAH." → Neighbourhood(Mahmutlar, Alanya, Antalya)` —
  словарь алиасов + türkçe-фолдинг (İ/ı/ş/ğ/ç/ö/ü), иерархия locations в БД;
- **комнатность**: `"2+1", "2 + 1", "2·1" → rooms="2+1", bedrooms=2`;
- **тип недвижимости / сделки / отопление / валюта** — mapping-таблицы;
- **price/m²**: gross и net считаются раздельно и не смешиваются;
- AI-extraction из свободного текста (позже) — только **дополняет** пустые поля,
  никогда не перезаписывает исходные данные.

## REST API (MVP)

```
GET    /api/listings                  — поиск с фильтрами, пагинация, сортировка
GET    /api/listings/{id}            — карточка + свежесть + price-аналитика
GET    /api/listings/{id}/history    — история цены/статуса
GET    /api/map                      — точки для карты (bbox-фильтр)
GET    /api/locations                — дерево географии для фильтров
GET    /api/meta                     — справочники (типы, валюты, курсы)
POST   /api/favorites                — добавить в избранное (X-Device-Id)
GET    /api/favorites                — список избранного
DELETE /api/favorites/{listing_id}   — удалить
```

Все ручки работают исключительно с нашей БД.

## Frontend flow (MVP)

```
/            поиск: фильтры (сделка, тип, гео, цена, m², комнаты, этаж,
             возраст, мебель/бассейн/парковка/балкон) + список карточек
/listing/[id]  карточка: цена, price/m² (gross и net), характеристики,
               история цены, «последняя проверка», статус, source-метаданные
/map         карта с точками (leaflet)
/favorites   избранное
```

Карточка показывает: `first_seen_at`, `last_checked_at`, дату последнего
изменения, статус — пользователь всегда видит свежесть данных.

## Стек

Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL (dev/tests — SQLite) ·
Redis + APScheduler/Celery для фоновых задач (MVP — APScheduler в процессе) ·
S3-compatible storage для изображений · Next.js/React frontend.

## Дорожная карта MVP

1. **Этап 1 (готово в этом репозитории)**: модели, нормализация, ingestion с
   инкрементальным diff и lifecycle, история цен, поиск/фильтры, REST API,
   mock- и feed-адаптеры, тесты, минимальный frontend.
2. **Этап 2** (частично готово): PostgreSQL+Alembic в проде и docker-compose
   (db+api+worker) — готово; планировщик отдельным процессом
   (`python -m app.tasks.scheduler`) — готово; курсы валют из официального
   XML TCMB с fallback на сохранённые — готово. Осталось: реальный
   agency-feed (нужен договор с агентством), изображения в S3.
3. **Этап 3**: дедупликация с image phash/embeddings, переводы (ru/en/tr),
   AI-extraction, сохранённые поиски и уведомления, аналитика рынка.
