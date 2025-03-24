from sqlalchemy.orm import Session, joinedload
from app.models.assignment_model import Assignment
from app.models.solution_model import Solution
from app.models.user_model import User
from app.models.role_model import Role
from fastapi import HTTPException
from app.schemas.user_schema import UserResponse

def view_all_assignments(db: Session, solution_id: int, current_user: UserResponse):
    # Get the solution
    solution = db.query(Solution).filter(Solution.id == solution_id).first()
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found.")

    # Get the team_id of the current user
    team_id = current_user.team_id
    
    # Filtering the assignments to check for that logged in user
    assignments = db.query(Assignment).filter(
        Assignment.solution_id == solution_id,
        Assignment.team_id == team_id 
    ).all()

    if not assignments:
        raise HTTPException(status_code=404, detail="No assignments found for this solution or team.")

    return assignments

def toggle_locked(db: Session, assignment_id: int, current_user: UserResponse):
    # Filtering assignments
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    if assignment.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="You do not have permission to modify this assignment.")

    # Toggle the locked status
    assignment.locked = not assignment.locked
    db.commit()
    db.refresh(assignment)

    return {"message": "Toggle Activated", "assignment": assignment}

# getting all the assignments for the current user for a specific week to see how they are rostered
def get_assignments_for_user_week(db: Session, user_id: int, week_id: int):
    assignments = (
        db.query(Assignment)
        .join(Solution, Assignment.solution_id == Solution.id)
        .filter(
            Assignment.user_id == user_id, 
            Solution.week_id == week_id,  
            Solution.status == "ACTIVE"  
        )
        .options(joinedload(Assignment.solution)) 
        .all()
    )

    if not assignments:
        raise HTTPException(status_code=404, detail="No active assignments found for this user in the given week.")

    # Prepare response
    result = [
        {
            "id": a.id,
            "week_id": a.solution.week_id,  
            "day_id": a.day_id,
            "team_id": a.team_id,
            "user_id": a.user_id,
            "shift_id": a.shift_id,
        }
        for a in assignments
    ]

    return result