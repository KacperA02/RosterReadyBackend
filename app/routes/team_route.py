from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.team_schema import TeamCreate, TeamResponse
from app.crud.team_crud import create_team, get_team, update_team_members
from app.db_config import get_db

router = APIRouter()

@router.post("/", response_model=TeamResponse)
async def create_team_route(team: TeamCreate, db: Session = Depends(get_db)):
    new_team,error = await create_team(db, team)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return new_team

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team_route(team_id: int, db: Session = Depends(get_db)):
    team = await get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.put("/{team_id}/members", response_model=TeamResponse)
def add_members_to_team(team_id: int, new_member_ids: list[int], db: Session = Depends(get_db)):
    team, error = update_team_members(db, team_id, new_member_ids)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return team