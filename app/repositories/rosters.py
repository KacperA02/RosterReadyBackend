from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Assignment, Roster, ShiftInstance, TeamMember, User


def get_roster(db: Session, team_id: int, roster_id: int) -> Roster | None:
    return db.scalar(select(Roster).where(Roster.id == roster_id, Roster.team_id == team_id))


def list_rosters(db: Session, team_id: int) -> list[Roster]:
    return list(
        db.scalars(
            select(Roster)
            .where(Roster.team_id == team_id)
            .order_by(Roster.period_start.desc(), Roster.id.desc())
        ).all()
    )


def list_assignment_rows(db: Session, roster_id: int):
    return list(
        db.execute(
            select(Assignment, ShiftInstance, TeamMember, User)
            .join(ShiftInstance, ShiftInstance.id == Assignment.shift_instance_id)
            .join(TeamMember, TeamMember.id == Assignment.team_member_id)
            .join(User, User.id == TeamMember.user_id)
            .where(Assignment.roster_id == roster_id)
            .order_by(ShiftInstance.starts_at, User.last_name, User.first_name)
        ).all()
    )
