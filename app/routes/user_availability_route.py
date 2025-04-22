from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from app.schemas.user_availability_schema import UserAvailabilityCreate
from app.crud.user_availability_crud import create_user_availability, delete_user_availability, get_team_availabilities, get_user_availabilities, toggle_approval  
from app.dependencies.auth import require_role
from app.models import User
from app.dependencies.db_config import get_db
from app.services.websocket_manager import manager 
from app.models.team_model import Team
from app.models.user_availability_model import UserAvailability
from app.schemas.user_availability_schema import UserAvailabilityResponse


router = APIRouter()
# creates a list of request availabilities
@router.post("/")
async def create_availability(
    availability_data: UserAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employee", "Employer"]))
):
    
    availability = create_user_availability(db, availability_data, current_user)

    # Ensure that you are correctly retrieving the user's team and employer
    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    
    if team:
        employer_id = team.creator_id  
        if employer_id:
            # Send notification to employer via WebSocket
            await manager.send_to_user(str(employer_id), f"Employee {current_user.first_name} has updated availability.")
            print(f"Sending notification to employer {employer_id} about availability update from {current_user.first_name}")
        else:
            print(f"No employer found for team {team.id}.")
    else:
        print(f"No team found for user {current_user.id}.")

    return availability

    
# deletes a specific availability
@router.delete("/specific/{availability_id}")
async def delete_availability(
    availability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer", "Employee"]))  
):
    return delete_user_availability(db, availability_id, current_user)

# gets the availabilities of the team
@router.get("/team", response_model=List[UserAvailabilityResponse])
async def get_team_availabilities_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))
):
    return get_team_availabilities(db, current_user)

# gets the availabilities of the user
@router.get("/user", response_model=List[UserAvailabilityResponse])
async def get_user_availabilities_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employee", "Employer"])) 
):
    return get_user_availabilities(db, current_user)

# toggles the approval of a specific availability
# toggles the approval of a specific availability
@router.patch("/specific/{availability_id}")
async def toggle_approval_route(
    availability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))
):
    # Toggle the approval status first
    updated_availability = toggle_approval(db, availability_id, current_user)
    userAvailability = db.query(UserAvailability).filter(UserAvailability.id == availability_id).first()
    # Notify the employee that their availability has been approved or rejected
    if updated_availability:
        employee_id = userAvailability.user_id
        message = f"Your availability has been {'approved' if userAvailability.approved else 'rejected'} by {current_user.first_name}."
        await manager.send_to_user(str(employee_id), message)
        print(f"Sent WebSocket notification to employee {employee_id}")

    return updated_availability
