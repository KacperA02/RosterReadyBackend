from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user_model import User
from app.schemas.user_schema import UserCreate
import bcrypt

# function to encrypt the password using bycrypt
def hash_password(password: str) -> str:
    # generated a salt and hashed the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def create_user(db: Session, user: UserCreate):
    db_email = db.query(User).filter(User.email == user.email).first()
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    db_number = db.query(User).filter(User.mobile_number == user.mobile_number).first()
    if db_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile number already registered"
        )
    encrypted_password = hash_password(user.password)
    
    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        mobile_number=user.mobile_number,
        password=encrypted_password,
        )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
