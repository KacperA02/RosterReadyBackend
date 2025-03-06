from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from sqlalchemy.orm import Session
from app.crud.shift_crud import create_shift, edit_shift, view_shift, view_shifts_by_team
# from app.models import Team, day_shift_team, UserConstraint
from app.schemas.shift_schema import ShiftCreate, ShiftResponse
from app.db_config import get_db
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
@router.put("/{shift_id}", response_model=ShiftResponse)
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
@router.get("/{shift_id}", response_model=ShiftResponse)
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

# Route for creating a schedule by assigning shifts to users
# @router.get("/assign-shifts/{team_id}")
# async def assign_shifts(team_id: int, db: Session = Depends(get_db)):
#     # Find the team
#     team = db.query(Team).filter(Team.id == team_id).first()
#     if not team:
#         raise HTTPException(status_code=404, detail="Team not found")

#     # Get users in the team
#     # users = db.query(User).join(team_user).filter(team_user.c.team_id == team_id).all()
#     # user_ids = [user.id for user in users]

#     # Get day_shift_team_data
#     day_shift_team_data = db.query(day_shift_team.c.day_id, day_shift_team.c.shift_id).filter(day_shift_team.c.team_id == team_id).all()

#     # if not user_ids or not day_shift_team_data:
#     #     raise HTTPException(status_code=404, detail="Missing users or day-shift data")

#     # Fetch user availability from UserConstraint 
#     user_availability = {
#         (constraint.day_id, constraint.shift_id, constraint.user_id,constraint.is_available)
#         for constraint in db.query(UserConstraint)
#         .filter(UserConstraint.team_id == team_id)
#         .all()
#     }
#     print(user_availability)
#     print(day_shift_team_data)
#     # Create the solver
#     # solver = ShiftAssignmentSolver(user_ids, day_shift_team_data,user_availability)

#     # Run the solver to get possible solutions
#     solutions = solver.solve()

#     if not solutions:
#         raise HTTPException(status_code=400, detail="No valid solutions found")

#     # Get the first solution for the purpose of testing
#     first_solution = solutions[0]
#     formatted_solution = [
#         {"day_id": day_id, "shift_id": shift_id, "user_id": user_id}
#         for (day_id, shift_id), user_id in first_solution.items()
#     ]

#     return {
#         "team_id": team_id,
#         "total_solutions": len(solutions),
#         "first_solution": formatted_solution
#     }




    