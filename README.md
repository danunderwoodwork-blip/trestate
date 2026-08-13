# TREstate — независимый агрегатор недвижимости Турции

Платформа данных о недвижимости для зарубежных пользователей: собственная база,
периодически обновляемая из **разрешённых** источников (официальные API,
XML/CSV/JSON-фиды агентств, сайты застройщиков, лицензированный доступ).

Пользовательский путь: `USER → OUR FRONTEND → OUR API → OUR DATABASE`.
Во время пользовательских запросов исходные порталы не используются вообще.
Система не содержит механизмов обхода технических ограничений сайтов
(CAPTCHA / антибот / rate limit и т.п.) — если источник блокирует автоматический
доступ, для него подключается альтернативный разрешённый канал.

Подробности: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Структура

```
backend/
  app/
    api/            REST API (FastAPI): listings, map, favorites, locations, meta
    core/           конфигурация (интервалы обновления, лимиты — всё настраивается)
    db/             engine / session / Base
    models/         SQLAlchemy: listings, listing_history, images, features,
                    sources, locations, currencies, users, favorites, duplicate_groups
    schemas/        Pydantic: NormalizedListing, фильтры, ответы API
    sources/        адаптеры источников (единый интерфейс ListingSource)
      base.py         контракт: fetch_index / fetch_listing / normalize
      agency_feed/    рабочий импортёр XML/CSV/JSON-фидов
      mock/           демо-фид (5 объектов Аланьи) для dev-среды
      sahibinden/     placeholder — активируется только с разрешённым каналом данных
    normalization/  гео (алиасы районов), комнатность, валюты, price/m², türkçe-фолдинг
    ingestion/      инкрементальный pipeline + lifecycle + адаптивный график
    services/       поиск, аналитика цены, курсы валют, дедупликация
    tasks/          APScheduler-планировщик фоновой синхронизации
  alembic/          миграции (initial schema сгенерирована)
  scripts/          seed_demo.py — сидинг dev-среды
  tests/            15 тестов: нормализация, pipeline, lifecycle, API
frontend/           Next.js: поиск+фильтры, карточка, история цены, карта, избранное
docs/ARCHITECTURE.md  архитектура, ER-схема, алгоритмы, roadmap
```

## Запуск (dev)

Backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m scripts.seed_demo        # создаёт БД и импортирует демо-фид
.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

Frontend (проксирует /api на backend):

```powershell
cd frontend
npm install
npm run dev          # http://localhost:3000
```

Фоновая синхронизация (отдельный процесс):

```powershell
cd backend
.venv\Scripts\python -m app.tasks.scheduler
```

Тесты:

```powershell
cd backend
.venv\Scripts\python -m pytest tests
```

Прод-БД: задать `TRE_DATABASE_URL=postgresql+psycopg2://...` и применить
миграции `alembic upgrade head` (dev/тесты работают на SQLite без миграций).

## Подключение нового источника

1. Создать пакет в `app/sources/<name>/` с классом, реализующим `ListingSource`
   (`fetch_index`, `fetch_listing`, `normalize` → `NormalizedListing`).
   Для XML/CSV/JSON-фида достаточно конфигурации `AgencyFeedSource` (`feed_url`,
   `format`, `field_map`) — без нового кода.
2. Добавить строку в таблицу `sources` (code, name, adapter, config, enabled).
3. Всё. Pipeline, БД, API и frontend не меняются.
