from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.team_schema import *
from app.crud.team_crud import *
from app.dependencies.db_config import get_db
from app.schemas.user_schema import UserResponse
from app.dependencies.auth import get_current_user
from app.dependencies.auth import require_role


router = APIRouter()

@router.post("/", response_model=TeamCreate)
async def create_team_route(
    team: TeamCreate, 
    current_user: UserResponse = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    new_team, error = create_team(db, team, current_user)  
    if error:
        raise HTTPException(status_code=400, detail=error)
    return new_team

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team_route(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    team = get_team(db, team_id, current_user)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    users = [
        UserI(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        for user in team.users
    ]

    return TeamResponse(
        id=team.id,
        name=team.name,
        creator_id=team.creator_id,
        user_ids=users,
        employee_count=len(team.users),
        shift_count=len(team.shifts),
        expertise_count=len(team.expertises),
    )

@router.get("/{team_id}/users", response_model=TeamUsersResponse)
async def get_team_users_route(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_role(["Employer"]))
):
    team = get_team_users(db, team_id, current_user)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    users = [
        UserInTeam(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            mobile_number=user.mobile_number,
        )
        for user in team.users
    ]

    return TeamUsersResponse(team_id=team.id, users=users)

@router.put("/{team_id}/users", response_model=TeamResponse)
def add_users_to_team(team_id: int, new_users_ids: list[int], db: Session = Depends(get_db)):
    team, error = update_team_users(db, team_id, new_users_ids)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return team

@router.put("/{team_id}/edit", response_model=TeamResponse)
def update_team_name_route(
    team_id: int,
    name_update: TeamCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    updated_team, error = update_team_name(db, team_id, name_update.name, current_user)
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    users = [
        UserI(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        for user in updated_team.users
    ]

    return TeamResponse(
        id=updated_team.id,
        name=updated_team.name,
        creator_id=updated_team.creator_id,
        user_ids=users,
        employee_count=len(updated_team.users),
        shift_count=len(updated_team.shifts),
        expertise_count=len(updated_team.expertises),
    )

@router.delete("/{team_id}", status_code=204)
def delete_team_route(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    success, error = delete_team(db, team_id, current_user)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return

@router.delete("/{team_id}/users/{user_id}", status_code=204)
def remove_user_from_team_route(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_role(["Employer"]))
):
    success, error = remove_user_from_team(db, team_id, user_id, current_user)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return
