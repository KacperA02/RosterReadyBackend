from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from sqlalchemy.orm import Session
from app.crud.shift_crud import *
from app.schemas.shift_schema import ShiftCreate, ShiftResponse , ShiftDaysCreate
from app.dependencies.db_config import get_db
from app.models import User

from app.dependencies.auth import get_current_user,require_role

router = APIRouter()
# Route for creating a new shift
@router.post("/", response_model=ShiftResponse)
async def create_new_shift(
    shift: ShiftCreate, 
    db: Session = Depends(get_db), 
    # Ensure the user is an employer
    current_user: User = Depends(require_role(["Employer"]))
):

    # create function returns a tuple, so I unpacked it
    db_shift, error = create_shift(db, shift, current_user)
    # If there is an error, raise an HTTPException
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return db_shift

# Route for updating a shift
@router.put("/specific/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: int, 
    shift: ShiftCreate, 
    db: Session = Depends(get_db),
    # Ensure the user is an employer 
    current_user: User = Depends(require_role(["Employer"]))
):
    # Edit function returns a tuple, so I unpacked it
    db_shift = edit_shift(db, shift_id, shift, current_user)
    return db_shift

# Route for viewing a single shift
@router.get("/specific/{shift_id}", response_model=ShiftResponse)
async def get_shift(
    shift_id: int, 
    db: Session = Depends(get_db),
    # Ensure the user is an employer or employee 
    current_user: User = Depends(require_role(["Employer", "Employee"]))
):
    # view function returns a tuple, so I unpacked it
    db_shift = view_shift(db, shift_id, current_user)
    return db_shift
# Route for viewing all shifts for a team
@router.get("/", response_model=List[ShiftResponse])
async def get_team_shifts(
    db: Session = Depends(get_db),
    # Getting the current user 
    current_user: User = Depends(get_current_user)
):
    # view_shifts_by_team function returns a list of shifts
    db_shifts = view_shifts_by_team(db, current_user)
    return db_shifts

# attach days to a shift
@router.post("/days/{shift_id}")
def attach_days_to_shift_route(
    shift_id: int,
    shift_days: ShiftDaysCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"])) 
):
    return attach_days_to_shift(db, shift_id, shift_days, current_user)

# delete days from a shift
@router.delete("/days/{shift_id}")
def remove_days_from_shift_route(
    shift_id: int,
    shift_days: ShiftDaysCreate,  
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))  
):
    return remove_days_from_shift(db, shift_id, shift_days, current_user)

@router.delete("/specific/{shift_id}")
def delete_shift_route(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))  
):
    return delete_shift(db, shift_id, current_user)




    