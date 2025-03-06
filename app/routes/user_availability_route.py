from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.user_availability_schema import UserAvailabilityCreate
from app.crud.user_availability_crud import create_user_availability
from app.dependencies.auth import require_role
from app.models import User
from app.db_config import get_db

router = APIRouter()

@router.post("/")
async def create_availability(
    availability_data: UserAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employee", "Employer"]))  
):
    return create_user_availability(db, availability_data, current_user)
