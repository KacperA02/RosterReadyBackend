from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.dependencies.db_config import get_db
from app.schemas.solution_schema import *
from app.crud.solution_crud import get_all_solutions
from app.dependencies.auth import require_role
from app.schemas.user_schema import UserResponse

router = APIRouter()

@router.get("/", response_model=List[SolutionI])
async def fetch_all_solutions(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_role(["Employer"]))
):
    solutions = get_all_solutions(db, current_user)
    if not solutions:
        raise HTTPException(status_code=404, detail="No solutions found")
    return solutions 