from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserCreate, UserResponse
from app.crud.user_crud import *
from app.dependencies.db_config import get_db
from app.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    redirect_slashes=True
)


@router.post("/", response_model=UserResponse)
async def create_user_route(user: UserCreate, db: Session = Depends(get_db)):
    db_user = create_user(db, user)
    if not db_user:
        raise HTTPException(status_code=400, detail="Email already in use")
    return db_user

@router.get("/specific/{user_id}", response_model=UserResponse)
async def get_user_route(user_id: int, db: Session = Depends(get_db)):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
# new route to get the current user using the get_current_user dependency
@router.get("/me", response_model=UserResponse)
async def get_my_info(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@router.delete("/me", response_model=UserResponse)
async def delete_my_account(current_user: UserResponse = Depends(get_current_user), db: Session = Depends(get_db)):
    deleted_user = delete_user(db, current_user.id)  
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted_user

@router.put("/me", response_model=UserEdit)
def update_current_user_route(
    user_update: UserEdit, 
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    return update_user(db, current_user.id, user_update)
