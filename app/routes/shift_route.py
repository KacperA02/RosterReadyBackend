from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.crud.shift_crud import create_shift
from app.csp_solver import ShiftAssignmentSolver
from app.schemas.shift_schema import ShiftCreate, ShiftResponse
from app.db_config import get_db
from app.models import Team, User, Shift, Day
from app.association import team_user, day_shift_team

router = APIRouter()

@router.post("/", response_model=ShiftResponse)
async def create_shift_route(shift: ShiftCreate, db: Session = Depends(get_db)):
    db_shift, error = create_shift(db, shift)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return db_shift

# Route for creating a schedule by assigning shifts to users
@router.get("/{team_id}/assign_shifts")
# takes team_id para
async def assign_shifts(team_id: int, db: Session = Depends(get_db)):
    # Finds the team and checks if it exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Fetches all the users and joins with the m:n table and filters to the correct team id
    users = db.query(User).join(team_user).filter(team_user.c.team_id == team_id).all()
    # defining a variable to store each user within the team into this array
    user_ids = [user.id for user in users]

    # gets all rows within the linking table which matches the team_id as the one given
    day_shift_team_data = db.query(day_shift_team.c.day_id, day_shift_team.c.shift_id).filter(day_shift_team.c.team_id == team_id).all()

    # validating that users exist and if shifts exist
    if not user_ids or not day_shift_team_data:
        raise HTTPException(status_code=404, detail="Missing users or day-shift data")

    # defining a variable called solver then passing the two variables created above which the solver needs
    solver = ShiftAssignmentSolver(user_ids, day_shift_team_data)
    #running the solve method on the solver variable to get the solutions 
    solutions = solver.solve()
    # Checks if there is a solution available, this may come up if there are too many constraints to fill each varaible
    if not solutions:
        raise HTTPException(status_code=400, detail="No valid solutions found")

    # The less constraints and more variables and domains then there are more solutions for the purpose of testing i am just getting the first solution
    first_solution = solutions[0]
    formatted_solution = [
        {"day_id": day_id, "shift_id": shift_id, "user_id": user_id}
        for (day_id, shift_id), user_id in first_solution.items()
    ]

    return {
        "team_id": team_id,
        # Getting the amount of solutions found
        "total_solutions": len(solutions),
        "first_solution": formatted_solution
    }



    