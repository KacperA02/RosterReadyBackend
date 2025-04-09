from sqlalchemy.orm import Session, joinedload
from app.models.assignment_model import Assignment
from app.models.solution_model import Solution
from app.models.user_model import User
from app.models.role_model import Role
from fastapi import HTTPException
from app.schemas.user_schema import UserResponse

from sqlalchemy.orm import joinedload

def view_all_assignments(db: Session, week_id: int, current_user: UserResponse):
    # Get the team_id of the current user
    team_id = current_user.team_id

    # Find all solutions that belong to the given week and team
    solutions = db.query(Solution).filter(
        Solution.week_id == week_id,
        Solution.team_id == team_id
    ).all()

    if not solutions:
        raise HTTPException(status_code=404, detail="No solutions found for this week and team.")

    # Extract solution IDs
    solution_ids = [sol.id for sol in solutions]

    # Retrieve all assignments, eagerly loading user, shift, and day details
    assignments_by_solution = {}
    for sol in solutions:
        assignments = db.query(Assignment).filter(
            Assignment.solution_id == sol.id,
            Assignment.team_id == team_id
        ).options(
            joinedload(Assignment.user),  
            joinedload(Assignment.shift),  
            joinedload(Assignment.day)  
        ).all()

        # Format assignments with user, shift, day, and locked status
        formatted_assignments = [
            {
                "assignment_id": assignment.id,
                "locked": assignment.locked,  
                "user": {
                    "id": assignment.user.id,
                    "first_name": assignment.user.first_name,
                    "last_name": assignment.user.last_name
                } if assignment.user else None,
                "shift": {
                    "id": assignment.shift.id,
                    "name": assignment.shift.name,
                    "time_start": assignment.shift.time_start,
                    "time_end": assignment.shift.time_end,
                    "task": assignment.shift.task,  
                } if assignment.shift else None,
                "day": {
                    "id": assignment.day.id,
                    "name": assignment.day.name,    
                } if assignment.day else None
            }
            for assignment in assignments
        ]

        assignments_by_solution[f"solution_{sol.id}"] = formatted_assignments

    if not assignments_by_solution:
        raise HTTPException(status_code=404, detail="No assignments found for this week and team.")

    return assignments_by_solution


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

def get_assignments_by_solution(db: Session, solution_id: int, current_user: UserResponse):
    team_id = current_user.team_id

    # Verify the solution exists and belongs to the user's team
    solution = db.query(Solution).filter(
        Solution.id == solution_id,
        Solution.team_id == team_id
    ).first()

    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found for your team.")

    # Fetch all assignments for the solution
    assignments = db.query(Assignment).filter(
        Assignment.solution_id == solution_id,
        Assignment.team_id == team_id
    ).options(
        joinedload(Assignment.user),
        joinedload(Assignment.shift),
        joinedload(Assignment.day)
    ).all()

    if not assignments:
        raise HTTPException(status_code=404, detail="No assignments found for this solution.")

    # Format and return the assignments
    return [
        {
            "assignment_id": a.id,
            "locked": a.locked,
            "user": {
                "id": a.user.id,
                "first_name": a.user.first_name,
                "last_name": a.user.last_name
            } if a.user else None,
            "shift": {
                "id": a.shift.id,
                "name": a.shift.name,
                "time_start": a.shift.time_start,
                "time_end": a.shift.time_end,
                "task": a.shift.task
            } if a.shift else None,
            "day": {
                "id": a.day.id,
                "name": a.day.name
            } if a.day else None
        }
        for a in assignments
    ]
