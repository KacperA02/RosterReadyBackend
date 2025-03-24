from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import jwt
from typing import List
from fastapi import Depends, HTTPException, status, Cookie
# A utility for handling OAuth2-based authentication (used to pass the token).
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db_config import get_db
from app.models.user_model import User
from app.schemas.user_schema import UserResponse
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from app.schemas.role_schema import RoleResponse
load_dotenv()

# Get the database URL from environment variables
JWTSECRETKEY = os.getenv("MY_SECRET_JWTKEY")
JWTSECRETALGORITHM = os.getenv("MY_SECRET_JWTALGORITHM")

# Check if JWTSECRETKEY is loaded correctly
if not JWTSECRETKEY:
    raise ValueError("JWT secret key not found")
if not JWTSECRETALGORITHM:
    raise ValueError("JWT secret algorithm not found")
# Secret key for JWT (Use a secure key in production)
SECRET_KEY = JWTSECRETKEY
ALGORITHM = JWTSECRETALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for handling token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# created a function to hash the password using the hash method from passlib
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# created a function to verify the password using the verify method from passlib
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# created a function to create an access token using the encode method from jwt
# Takes three parameters, data to encode, expires_delta to set the expiration time, and the secret key
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    # to_encode is to create a copy of the data passed for encoding
    to_encode = data.copy()
    # expire is the expiration time for the token and a fallback of 15 if it fails
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=60))
    # encoding the data with the expiration time
    to_encode.update({"exp": expire})
    # returning the encoded token
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# created a function to get the user by email, easier to call globally
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()





# created a function to get the current user using the token passed
# this function gets the current user by decoding the token and checking if the user exists
# if the user exists, it returns the user, otherwise, it raises an exception
async def get_current_user(access_token: str = Cookie(None), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not access_token:
        raise credentials_exception

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception

    roles = [RoleResponse(id=role.id, name=role.name) for role in user.roles]

    return UserResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        mobile_number=user.mobile_number,
        day_off_count=user.day_off_count,
        team_id=user.team_id,
        roles=roles
    )

# function takes a list of required roles and checks if the user has any of the roles
# if the user has any of the roles, it returns the current user, otherwise, it raises an exception
def require_role(required_roles: List[str]):
    def role_checker(current_user: UserResponse = Depends(get_current_user)):
        user_roles = set(role.name for role in current_user.roles)
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user

    return role_checker


