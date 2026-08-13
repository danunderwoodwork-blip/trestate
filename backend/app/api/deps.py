from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.ingestion.lifecycle import utcnow
from app.models import User

DbDep = Annotated[Session, Depends(get_db)]


def get_or_create_user(
    db: DbDep,
    x_device_id: Annotated[str | None, Header()] = None,
) -> User:
    """MVP-идентификация: анонимный пользователь по заголовку X-Device-Id."""
    if not x_device_id or len(x_device_id) > 64:
        raise HTTPException(status_code=401, detail="X-Device-Id header required")
    user = db.scalar(select(User).where(User.device_token == x_device_id))
    if user is None:
        user = User(device_token=x_device_id, created_at=utcnow())
        db.add(user)
        db.commit()
    return user


UserDep = Annotated[User, Depends(get_or_create_user)]
