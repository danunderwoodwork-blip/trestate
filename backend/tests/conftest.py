import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
# Тестовая БД задаётся ДО импорта app.* (get_settings кешируется).
os.environ["TRE_DATABASE_URL"] = f"sqlite:///{BACKEND / 'test_trestate.db'}"

import pytest  # noqa: E402

from app.db import session  # noqa: E402
from app.db.base import Base  # noqa: E402
import app.models  # noqa: E402,F401


@pytest.fixture
def db():
    Base.metadata.drop_all(session.engine)
    Base.metadata.create_all(session.engine)
    s = session.SessionLocal()
    yield s
    s.close()
