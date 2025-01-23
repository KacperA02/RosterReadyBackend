from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.team_schema import TeamCreate, TeamResponse
from app.crud.team_crud import create_team, get_team, update_team_users
from app.db_config import get_db

router = APIRouter()

@router.post("/", response_model=TeamResponse)
async def create_team_route(team: TeamCreate, db: Session = Depends(get_db)):
    new_team,error = create_team(db, team)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return new_team

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team_route(team_id: int, db: Session = Depends(get_db)):
    team = get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Had to manually map the linking table as it was giving back and empty array
    user_ids = [user.id for user in team.users]

    
    return TeamResponse(
        id=team.id,
        name=team.name,
        creator_id=team.creator_id,
        user_ids=user_ids  
    )

@router.put("/{team_id}/users", response_model=TeamResponse)
def add_users_to_team(team_id: int, new_users_ids: list[int], db: Session = Depends(get_db)):
    team, error = update_team_users(db, team_id, new_users_ids)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return team