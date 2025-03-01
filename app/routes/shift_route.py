from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.crud.shift_crud import create_shift
from app.csp_solver import ShiftAssignmentSolver
from app.schemas.shift_schema import ShiftCreate, ShiftResponse
from app.db_config import get_db
from app.models import Team, User, UserConstraint
from app.association import day_shift_team

router = APIRouter()

@router.post("/", response_model=ShiftResponse)
async def create_shift_route(shift: ShiftCreate, db: Session = Depends(get_db)):
    db_shift, error = create_shift(db, shift)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return db_shift

# Route for creating a schedule by assigning shifts to users
@router.get("/{team_id}/assign_shifts")
async def assign_shifts(team_id: int, db: Session = Depends(get_db)):
    # Find the team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get users in the team
    # users = db.query(User).join(team_user).filter(team_user.c.team_id == team_id).all()
    # user_ids = [user.id for user in users]

    # Get day_shift_team_data
    day_shift_team_data = db.query(day_shift_team.c.day_id, day_shift_team.c.shift_id).filter(day_shift_team.c.team_id == team_id).all()

    # if not user_ids or not day_shift_team_data:
    #     raise HTTPException(status_code=404, detail="Missing users or day-shift data")

    # Fetch user availability from UserConstraint 
    user_availability = {
        (constraint.day_id, constraint.shift_id, constraint.user_id,constraint.is_available)
        for constraint in db.query(UserConstraint)
        .filter(UserConstraint.team_id == team_id)
        .all()
    }
    print(user_availability)
    print(day_shift_team_data)
    # Create the solver
    # solver = ShiftAssignmentSolver(user_ids, day_shift_team_data,user_availability)

    # Run the solver to get possible solutions
    solutions = solver.solve()

    if not solutions:
        raise HTTPException(status_code=400, detail="No valid solutions found")

    # Get the first solution for the purpose of testing
    first_solution = solutions[0]
    formatted_solution = [
        {"day_id": day_id, "shift_id": shift_id, "user_id": user_id}
        for (day_id, shift_id), user_id in first_solution.items()
    ]

    return {
        "team_id": team_id,
        "total_solutions": len(solutions),
        "first_solution": formatted_solution
    }




    