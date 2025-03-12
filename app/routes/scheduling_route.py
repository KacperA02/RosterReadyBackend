from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db_config import get_db
from app.crud.scheduling_crud import create_schedule
from fastapi import APIRouter, Depends, HTTPException
from app.models import User
from app.dependencies.auth import require_role
from app.solver_csp import ShiftAssignmentSolver
from app.schemas.schedule_schema import ShiftAssignmentResponse

router = APIRouter()

@router.post("/assign-shifts/{team_id}", response_model=ShiftAssignmentResponse)
async def assign_shifts(
    team_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))
):
    # auth
    if current_user.team_id != team_id:
        raise HTTPException(status_code=403, detail="You are not authorized to assign shifts for this team")

    # Requesting the data
    request_data = create_schedule(db, team_id)

    # Initialize CSP solver with the request data
    solver = ShiftAssignmentSolver(
        users=request_data["users"],
        shifts=request_data["shifts"],
        shift_details=request_data["shift_details"],
        user_availability=request_data["user_availability"],
        user_expertise=request_data["user_expertise"],
        shift_expertise=request_data["shift_expertise"]
    )

    # calling the solve function within the shiftAssignmentSolver
    result = solver.solve() 
    # if no assignments show 400 status code
    if not result["assignments"]:
        raise HTTPException(status_code=400, detail="No valid shift assignments found")
    # return the solutions
    return result
