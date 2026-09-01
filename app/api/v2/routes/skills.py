from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v2.schemas import (
    MemberSkillResponse,
    MemberSkillUpdate,
    SkillCreateRequest,
    SkillResponse,
)
from app.core.security import get_current_user
from app.domain.database import get_db
from app.domain.models import MemberSkill, Skill, User
from app.repositories.skills import get_member_skill, get_skill_by_name, list_member_skills, list_skills
from app.services.memberships import MANAGEMENT_ROLES, require_active_membership
from app.services.skills import (
    assign_skill,
    require_member,
    require_skill,
    to_member_skill_response,
)

router = APIRouter(prefix="/teams/{team_id}", tags=["V2 Skills"])


@router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(
    team_id: int,
    payload: SkillCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Skill:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Skill name is required")
    if get_skill_by_name(db, team_id, name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Skill already exists")
    skill = Skill(team_id=team_id, name=name)
    db.add(skill)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Skill already exists")
    db.refresh(skill)
    return skill


@router.get("/skills", response_model=list[SkillResponse])
def get_skills(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Skill]:
    require_active_membership(db, current_user.id, team_id)
    return list_skills(db, team_id)


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    team_id: int,
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    skill = require_skill(db, team_id, skill_id)
    db.delete(skill)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/members/{member_id}/skills/{skill_id}", response_model=MemberSkillResponse)
def put_member_skill(
    team_id: int,
    member_id: int,
    skill_id: int,
    payload: MemberSkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemberSkillResponse:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    member = require_member(db, team_id, member_id)
    skill = require_skill(db, team_id, skill_id)
    assignment = assign_skill(db, member, skill, payload.proficiency)
    return to_member_skill_response(assignment, skill)


@router.get("/members/{member_id}/skills", response_model=list[MemberSkillResponse])
def get_member_qualifications(
    team_id: int,
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MemberSkillResponse]:
    require_active_membership(db, current_user.id, team_id)
    member = require_member(db, team_id, member_id)
    return [to_member_skill_response(assignment, skill) for assignment, skill in list_member_skills(db, member.id)]


@router.delete("/members/{member_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member_skill(
    team_id: int,
    member_id: int,
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    member = require_member(db, team_id, member_id)
    require_skill(db, team_id, skill_id)
    assignment = get_member_skill(db, member.id, skill_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member skill not found")
    db.delete(assignment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
