from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from sqlalchemy.orm import Session
from app.crud.expertise_crud import *
from app.schemas.expertise_schema import *
from app.dependencies.db_config import get_db
from app.models import User
from app.dependencies.auth import require_role

router = APIRouter()

# Route for creating a new expertise
@router.post("/", response_model=ExpertiseResponse)
async def create_new_expertise(
    expertise: ExpertiseCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(["Employer"]))
):
    # create function returns a tuple, so I unpacked it
    db_expertise = create_expertise(db, expertise, current_user)
    return db_expertise

# Route for updating an expertise
@router.put("/specific/{expertise_id}", response_model=ExpertiseResponse)
async def update_expertise(
    expertise_id: int, 
    expertise: ExpertiseCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))
):
    db_expertise = edit_expertise(db, expertise_id, expertise, current_user)
    return db_expertise

# Route for viewing a specific expertise
@router.get("/specific/{expertise_id}", response_model=ExpertiseResponse)
async def get_expertise(
    expertise_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer", "Employee"]))
):
    db_expertise = view_expertise(db, expertise_id, current_user)
    return db_expertise
# Route for viewing a specific expertise
@router.delete("/specific/{expertise_id}")
async def delete_expertise_route(
    expertise_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))
):
    delete_expertise(db, expertise_id, current_user)
    return "Deleted expertise successfully"

@router.get("/", response_model=list[ExpertiseResponse])
async def get_all_expertise_of_team(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))  
):
    expertise_list = view_all_expertise_of_team(db, current_user)
    return expertise_list

# route to assign expertise to a user
@router.post("/assign/{expertise_id}/user/{user_id}", response_model=UserAttached)
async def assign_expertise_to_user(
    expertise_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))
):
    # add_expertise_to_user function returns a tuple, so I unpacked it
    usersExpertised = add_expertise_to_user(db, expertise_id, user_id, current_user)
    
    return usersExpertised

# route to assign expertise to a shift
@router.post("/assign/{expertise_id}/shift/{shift_id}", response_model=ShiftAttached)
async def assign_expertise_to_shift(
    expertise_id: int,
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))
):
    # add_expertise_to_shift function returns a tuple, so I unpacked it
    shiftsExpertise = add_expertise_to_shift(db, expertise_id, shift_id, current_user)
    
    return shiftsExpertise

# route to remove expertise from a user
@router.delete("/remove/{expertise_id}/user/{user_id}")
async def remove_expertise_from_user_route(
    expertise_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))  
):
    # calling function to remove expertise from user
    remove_expertise_from_user(db, expertise_id, user_id, current_user)
    
    return "Removed expertise from user successfully"

# route to remove expertise from a shift
@router.delete("/remove/{expertise_id}/shift/{shift_id}")
async def remove_expertise_from_shift_route(
    expertise_id: int,
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"])) 
):
    #calling function to remove expertise from shift
    remove_expertise_from_shift(db, expertise_id, shift_id, current_user)
    
    return "Removed expertise from shift successfully"
