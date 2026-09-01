from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.v2.schemas import MemberSkillResponse
from app.domain.enums import SkillProficiency
from app.domain.models import MemberSkill, Skill, TeamMember
from app.repositories.memberships import get_member
from app.repositories.skills import get_skill


def require_member(db: Session, team_id: int, member_id: int) -> TeamMember:
    member = get_member(db, team_id, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")
    return member


def require_skill(db: Session, team_id: int, skill_id: int) -> Skill:
    skill = get_skill(db, team_id, skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill


def assign_skill(
    db: Session,
    member: TeamMember,
    skill: Skill,
    proficiency: SkillProficiency,
) -> MemberSkill:
    assignment = db.get(MemberSkill, (member.id, skill.id))
    if assignment:
        assignment.proficiency = proficiency
    else:
        assignment = MemberSkill(
            team_member_id=member.id,
            skill_id=skill.id,
            proficiency=proficiency,
        )
        db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def to_member_skill_response(assignment: MemberSkill, skill: Skill) -> MemberSkillResponse:
    return MemberSkillResponse(
        skill_id=skill.id,
        name=skill.name,
        proficiency=assignment.proficiency,
    )
