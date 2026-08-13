"""FastAPI-приложение. Обслуживает пользователей ТОЛЬКО из нашей БД:
во время пользовательского запроса внешние сайты не используются."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import favorites, listings, map as map_routes, meta
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend dev-сервер
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings.router)
app.include_router(map_routes.router)
app.include_router(favorites.router)
app.include_router(meta.router)


@app.get("/health")
def health():
    return {"status": "ok"}
