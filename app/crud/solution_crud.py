from sqlalchemy.orm import Session
from app.models.solution_model import Solution
from typing import List
from app.schemas.user_schema import UserResponse
from app.schemas.solution_schema import SolutionI
from sqlalchemy.orm import joinedload

def get_all_solutions(db: Session, current_user: UserResponse) -> List[SolutionI]:
    solutions = db.query(Solution) \
                  .options(joinedload(Solution.week)) \
                  .filter(Solution.team_id == current_user.team_id) \
                  .all()

    return [SolutionI.model_validate(solution) for solution in solutions]