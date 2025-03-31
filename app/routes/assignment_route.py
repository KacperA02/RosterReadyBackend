from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.crud.assignment_crud import *
from app.schemas.user_schema import UserResponse
from app.models.assignment_model import Assignment
from app.models.solution_model import Solution
from app.db_config import get_db
from app.dependencies.auth import require_role, get_current_user


router = APIRouter()

# View all assignments for a specific solution
@router.get("/solution/{week_id}")
async def get_assignments_for_solution(
    week_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_role(["Employer"]))
):
    return view_all_assignments(db, week_id, current_user)


@router.put("/specific/{assignment_id}/lock")
async def toggle_locked_status(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_role(["Employer"]))
):
    return toggle_locked(db, assignment_id, current_user)

@router.get("/week/{week_id}")
async def get_user_assignments(
    week_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    return get_assignments_for_user_week(db, current_user.id, week_id)