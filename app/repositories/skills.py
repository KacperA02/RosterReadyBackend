from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import MemberSkill, Skill


def get_skill(db: Session, team_id: int, skill_id: int) -> Skill | None:
    return db.scalar(select(Skill).where(Skill.id == skill_id, Skill.team_id == team_id))


def get_skill_by_name(db: Session, team_id: int, name: str) -> Skill | None:
    return db.scalar(select(Skill).where(Skill.team_id == team_id, Skill.name == name))


def list_skills(db: Session, team_id: int) -> list[Skill]:
    return list(db.scalars(select(Skill).where(Skill.team_id == team_id).order_by(Skill.name)).all())


def get_member_skill(db: Session, member_id: int, skill_id: int) -> MemberSkill | None:
    return db.get(MemberSkill, (member_id, skill_id))


def list_member_skills(db: Session, member_id: int) -> list[tuple[MemberSkill, Skill]]:
    return list(
        db.execute(
            select(MemberSkill, Skill)
            .join(Skill, Skill.id == MemberSkill.skill_id)
            .where(MemberSkill.team_member_id == member_id)
            .order_by(Skill.name)
        ).all()
    )
