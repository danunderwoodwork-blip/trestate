import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase


# JSONB на PostgreSQL, обычный JSON на SQLite (dev/tests).
JSONVariant = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass
