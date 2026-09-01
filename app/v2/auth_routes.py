import os

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.domain.database import get_db
from app.domain.models import User
from app.v2.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.v2.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["V2 Authentication"])


def _set_auth_cookie(response: Response, token: str) -> None:
    production = os.getenv("APP_ENV", "development").lower() == "production"
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=production,
        samesite="none" if production else "lax",
        max_age=3600,
        path="/",
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    normalized_email = payload.email.lower()
    duplicate = db.scalar(
        select(User).where(
            or_(
                User.email == normalized_email,
                User.mobile_number == payload.mobile_number
                if payload.mobile_number
                else False,
            )
        )
    )
    if duplicate:
        detail = "Email already registered" if duplicate.email == normalized_email else "Mobile number already registered"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    user = User(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=normalized_email,
        mobile_number=payload.mobile_number,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already registered")
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(
        select(User)
        .options(selectinload(User.memberships))
        .where(User.email == payload.email.lower())
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    token = create_access_token(user)
    _set_auth_cookie(response, token)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie("access_token", path="/")

