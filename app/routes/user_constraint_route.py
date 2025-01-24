from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.crud.user_constraints_crud import update_user_constraint, get_user_constraints
from app.schemas.user_constraint_schema import UserConstraintUpdate, UserConstraintBase
from app.db_config import get_db

router = APIRouter()

# Didn't need a create as it is done automatically upon shift creation

# route to view a users constraints with optional query parameters
@router.get("/user/{user_id}/constraints", response_model=List[UserConstraintBase])
# function parameters
async def get_user_constraints_route(
    # identifys the the users whose constraints were retrieved
    user_id: int,
    # optional parameter to filter the constraints by shift
    shift_id: Optional[int] = None,  
    # optional parameter to filter the constraints by day
    day_id: Optional[int] = None,
    # dependency of the database   
    db: Session = Depends(get_db)
):
    # defined a variable to retieve the constraints from the database
    constraints = get_user_constraints(db, user_id, shift_id, day_id)
    # condition to check if a constraint was found
    if not constraints:
        raise HTTPException(status_code=404, detail="User constraints not found")
    # return the constraints
    return constraints

# Route for a put request on the user constraints to change preferences or availability
# will extend this later on
@router.put("/user/{user_id}/shift/{shift_id}/day/{day_id}", response_model=UserConstraintBase)
async def update_user_constraint_route(
    # path parameters
    user_id: int,
    shift_id: int,
    day_id: int,
    # represents the body request which is specified in the schema
    update_data: UserConstraintUpdate,
    db: Session = Depends(get_db)
):
    # calls the function with all the necessary arguments
    updated_constraint = update_user_constraint(
        db, user_id, shift_id, day_id, update_data.is_available, update_data.is_preferred
    )
    # conditon to check if it exists
    if not updated_constraint:
        raise HTTPException(status_code=404, detail="User constraint not found")
    # otherwise return the updated constraint
    return updated_constraint
