from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.enums import MembershipStatus
from app.domain.models import TeamMember


def get_active_membership(db: Session, user_id: int, team_id: int) -> TeamMember | None:
    return db.scalar(
        select(TeamMember).where(
            TeamMember.user_id == user_id,
            TeamMember.team_id == team_id,
            TeamMember.status == MembershipStatus.ACTIVE,
        )
    )


def get_member(db: Session, team_id: int, member_id: int) -> TeamMember | None:
    return db.scalar(
        select(TeamMember)
        .options(selectinload(TeamMember.user))
        .where(TeamMember.id == member_id, TeamMember.team_id == team_id)
    )


def list_members(db: Session, team_id: int) -> list[TeamMember]:
    return list(
        db.scalars(
            select(TeamMember)
            .options(selectinload(TeamMember.user))
            .where(TeamMember.team_id == team_id)
            .order_by(TeamMember.id)
        ).all()
    )

