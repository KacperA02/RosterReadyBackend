from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.user_availability_schema import UserAvailabilityCreate
from app.crud.user_availability_crud import create_user_availability, delete_user_availability, get_team_availabilities, get_user_availabilities, toggle_approval  
from app.dependencies.auth import require_role
from app.models import User
from app.db_config import get_db

router = APIRouter()
# creates a list of request availabilities
@router.post("/")
async def create_availability(
    availability_data: UserAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employee", "Employer"]))  
):
    return create_user_availability(db, availability_data, current_user)

# deletes a specific availability
@router.delete("/specific/{availability_id}")
async def delete_availability(
    availability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer", "Employee"]))  
):
    return delete_user_availability(db, availability_id, current_user)

# gets the availabilities of the team
@router.get("/team")
async def get_team_availabilities_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))
):
    return get_team_availabilities(db, current_user)

# gets the availabilities of the user
@router.get("/user")
async def get_user_availabilities_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employee", "Employer"])) 
):
    return get_user_availabilities(db, current_user)

# toggles the approval of a specific availability
@router.patch("/specific/{availability_id}")
async def toggle_approval_route(
    availability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))
):
    return toggle_approval(db, availability_id, current_user)