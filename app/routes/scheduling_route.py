from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies.db_config import get_db
from app.crud.scheduling_crud import *
from fastapi import APIRouter, Depends, HTTPException
from app.models import User, Solution, Assignment
import datetime
from app.dependencies.auth import require_role
from app.CSPs.solver_csp import ShiftAssignmentSolver
from app.CSPs.regen_csp import RegenerateCSP
from app.schemas.schedule_schema import *

router = APIRouter()

@router.post("/assign-shifts/{team_id}/{week_id}", response_model=ShiftAssignmentResponse)
async def assign_shifts(
    team_id: int,
    week_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))
):
    # auth
    if current_user.team_id != team_id:
        raise HTTPException(status_code=403, detail="You are not authorized to assign shifts for this team")

    # Requesting the data
    request_data = create_schedule(db, team_id, week_id)

    # Initialize CSP solver with the request data
    solver = ShiftAssignmentSolver(
        users=request_data["users"],
        shifts=request_data["shifts"],
        shift_details=request_data["shift_details"],
        user_availability=request_data["user_availability"],
        user_expertise=request_data["user_expertise"],
        shift_expertise=request_data["shift_expertise"]
    )
    print(request_data)

    # calling the solve function within the shiftAssignmentSolver
    result = solver.solve() 
    # if there are no assignments show 400 stats code
    if not result["assignments"]:
        raise HTTPException(status_code=400, detail="No valid shift assignments found")
    
    # creating solution entry for each solution available
    for formatted_assignment in result["assignments"]:
        solution = Solution(
            team_id=team_id,
            week_id=week_id,
            status="DRAFT", 
            created_at=datetime.datetime.now()
        )
        db.add(solution)
        db.commit()  

        # Creating assignments for each solution
        for assignment in formatted_assignment:
            user_id = assignment["user_id"]
            shift_id = assignment["shift_id"]
            day_id = assignment["day_id"]
            
            assignment_obj = Assignment(
                user_id=user_id,
                shift_id=shift_id,
                day_id=day_id,
                team_id=team_id,
                solution_id=solution.id,
                locked=False
            )
            db.add(assignment_obj)

        db.commit()  

#    returning the solutions with the assignemnts
    return result

@router.post("/regenerate/{solution_id}", response_model=ShiftAssignmentRegenerationResponse)
async def reassign_shifts(
    solution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Employer"]))
):
    # Requesting the data
    request_data = regenerate_solution(db, solution_id)
    
    if current_user.team_id != request_data["team_id"]:
        raise HTTPException(status_code=403, detail="You are not authorized to assign shifts for this team")

    # Initialising CSP solver with the request data from thhe regenerate solution function in the crud file
    solver = RegenerateCSP(
        users=request_data["users"],
        shifts=request_data["shifts"],
        user_availability=request_data["user_availability"],
        user_expertise=request_data["user_expertise"],
        shift_expertise=request_data["shift_expertise"],
        shift_details=request_data["shift_times"],
        original_assignments=request_data["original_assignments"],
        locked_assignments=request_data["locked_assignments"],
    )

    result = solver.solve()

    if not result["assignments"]:
        return {
        "assignments": [],
        "total_solutions": 0,
        "changed_count": 0,
        "fallback_count": 0,
        "skipped_count": result.get("skipped_count", 0),
        "skipped_assignments": result.get("skipped_assignments", []),
        "failure_reasons": result.get("failure_reasons", ["No valid shift assignments found"]),
        "message": "No assignments could be generated due to constraints."
        }


    # Creating assignment objects from the solved data
    solution = db.query(Solution).filter(Solution.id == solution_id).first()
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    # updating the solution status to draft if its not 
    solution.status = "DRAFT"
    solution.created_at = datetime.datetime.now()
    db.commit()

    # Delete existing assignments for that solution
    db.query(Assignment).filter(Assignment.solution_id == solution_id).delete()
    db.commit()

    # Inserting the updated assignments (including locked ones)
    for assignment in result["assignments"]:
        user_id = assignment["user_id"]
        shift_id = assignment["shift_id"]
        day_id = assignment["day_id"]
        locked = assignment["locked"]

        assignment_obj = Assignment(
            user_id=user_id,
            shift_id=shift_id,
            day_id=day_id,
            team_id=request_data["team_id"],
            solution_id=solution.id,
            locked=locked
        )
        db.add(assignment_obj)

    db.commit()

    return result
