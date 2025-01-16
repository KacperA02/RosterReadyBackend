from sqlalchemy.orm import Session
from models.user_model import User
from schemas.user_schema import UserCreate

def create_user(db: Session, user: UserCreate):
    new_user = User(email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


