"""FastAPI app. All data served from our DB only."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.routes import favorites, listings, map as map_routes, meta
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.ingestion.lifecycle import utcnow
from app.services.currency import upsert_rate

# Import all models so they register with Base before create_all
import app.models  # noqa: F401
from app.models import Listing, Source

logger = logging.getLogger(__name__)
settings = get_settings()

_DEMO_SOURCES = [
    {
        "code": "mock",
        "name": "Demo Agency Feed",
        "adapter": "app.sources.mock.adapter:MockSource",
        "enabled": True,
    },
]


async def _seed_if_empty() -> None:
    """Run demo seed idempotently: only executes when the listings table is empty."""
    from app.ingestion.pipeline import sync_all_enabled
    from app.services.tcmb import refresh_rates

    db = SessionLocal()
    try:
        listing_count = db.scalar(select(Listing).limit(1))
        if listing_count is not None:
            return  # already seeded

        # Register demo source if not present
        for spec in _DEMO_SOURCES:
            if not db.scalar(select(Source).where(Source.code == spec["code"])):
                db.add(Source(**spec))
        db.commit()

        # Seed currency rates (falls back to constants if TCMB is offline)
        try:
            await refresh_rates(db)
        except Exception as exc:
            logger.warning("TCMB unavailable (%s); using fallback rates", exc)
            now = utcnow()
            upsert_rate(db, "USD", "$", 41.0, now)
            upsert_rate(db, "EUR", "€", 46.5, now)
            db.commit()

        results = await sync_all_enabled(db)
        for stats in results:
            logger.info(
                "seed %s: index=%s new=%s updated=%s",
                stats.source, stats.total_in_index, stats.new, stats.updated,
            )
    except Exception as exc:
        logger.exception("Demo seed failed: %s", exc)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (works for both SQLite dev and PostgreSQL prod)
    Base.metadata.create_all(bind=engine)
    # Seed demo data in the background so the health probe passes immediately.
    # The app is fully ready to serve requests before seeding finishes.
    asyncio.create_task(_seed_if_empty())
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings.router)
app.include_router(map_routes.router)
app.include_router(favorites.router)
app.include_router(meta.router)


@app.get("/api/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}
