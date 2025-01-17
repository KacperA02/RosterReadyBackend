from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserCreate, UserResponse
from app.crud.user_crud import create_user, get_user
from app.db_config import get_db

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user_route(user: UserCreate, db: Session = Depends(get_db)):
    db_user = create_user(db, user)
    if not db_user:
        raise HTTPException(status_code=400, detail="Email already in use")
    return db_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_route(user_id: int, db: Session = Depends(get_db)):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

