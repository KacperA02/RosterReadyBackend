from sqlalchemy.orm import Session
from app.models.solution_model import Solution
from typing import List
from app.schemas.user_schema import UserResponse
from app.schemas.solution_schema import SolutionI
from sqlalchemy.orm import joinedload
from app.models.solution_model import SolutionStatus
from app.models.assignment_model import Assignment
from fastapi import HTTPException

def get_all_solutions(db: Session, current_user: UserResponse) -> List[SolutionI]:
    solutions = db.query(Solution) \
                  .options(joinedload(Solution.week)) \
                  .filter(Solution.team_id == current_user.team_id) \
                  .all()

    return [SolutionI.model_validate(solution) for solution in solutions]

def accept_solution(db: Session, solution_id: int, current_user: UserResponse):

    solution = db.query(Solution).filter(Solution.id == solution_id, Solution.team_id == current_user.team_id).first()
    
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found or not part of your team.")
    
    # Change the status to ACTIVE
    solution.status = SolutionStatus.ACTIVE
    db.commit()
    db.refresh(solution)
    
    return solution

def decline_solution(db: Session, solution_id: int, current_user: UserResponse):
    # Fetch the solution by ID and check if it belongs to the current user’s team
    solution = db.query(Solution).filter(Solution.id == solution_id, Solution.team_id == current_user.team_id).first()
    
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found or not part of your team.")
    
    # Delete all assignments related to this solution
    db.query(Assignment).filter(Assignment.solution_id == solution.id).delete()
    
    # Delete the solution
    db.delete(solution)
    db.commit()
    
    return {"message": "Solution and its assignments have been deleted."}