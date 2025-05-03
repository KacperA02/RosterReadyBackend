from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.dependencies.db_config import get_db
from app.schemas.solution_schema import *
from app.crud.solution_crud import *
from app.dependencies.auth import require_role
from app.schemas.user_schema import UserResponse
from app.models.user_model import User  
from app.services.websocket_manager import manager 
router = APIRouter()

@router.get("/", response_model=List[SolutionI])
async def fetch_all_solutions(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_role(["Employer", "Employee"]))
):
    solutions = get_all_solutions(db, current_user)
    if not solutions:
        raise HTTPException(status_code=404, detail="No solutions found")
    return solutions 

@router.post("/accept/{solution_id}", response_model=SolutionI)
async def accept_changes(
    solution_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_role(["Employer"]))
):
    try:
        # Accept the solution (sync logic)
        solution = accept_solution(db, solution_id, current_user)

        # Fetch all users in the same team
        team_members = db.query(User).filter(User.team_id == current_user.team_id).all()

        # Notify each member via WebSocket
        for member in team_members:
            message = f"A new schedule has been created by {current_user.first_name}. Check it out!"
            await manager.send_to_user(str(member.id), message)

        return solution

    except HTTPException as e:
        raise e

@router.delete("/decline/{solution_id}")
async def decline_changes(
    solution_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_role(["Employer"]))
):
    try:
        message = decline_solution(db, solution_id, current_user)
        return message
    except HTTPException as e:
        raise e