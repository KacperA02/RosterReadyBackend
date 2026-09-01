import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.database import get_db
from app.domain.models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _jwt_secret() -> str:
    secret = os.getenv("MY_SECRET_JWTKEY")
    if not secret:
        raise RuntimeError("MY_SECRET_JWTKEY is required for the V2 API")
    return secret


def _jwt_algorithm() -> str:
    return os.getenv("MY_SECRET_JWTALGORITHM", "HS256")


def create_access_token(user: User) -> str:
    active_memberships = [m for m in user.memberships if m.status.value == "ACTIVE"]
    primary_membership = active_memberships[0] if active_memberships else None
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=60)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "id": user.id,
        "team_id": primary_membership.team_id if primary_membership else None,
        "roles": [m.role.value for m in active_memberships],
        "exp": expires_at,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=_jwt_algorithm())


def _extract_token(authorization: str | None, access_token: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return access_token


def get_current_user(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = _extract_token(authorization, access_token)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[_jwt_algorithm()])
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.scalar(
        select(User).options(selectinload(User.memberships)).where(User.id == user_id)
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
