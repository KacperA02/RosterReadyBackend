from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import RequestStatus
from app.domain.models import TeamMember, TimeRequest


def get_time_request(db: Session, team_id: int, request_id: int) -> TimeRequest | None:
    return db.scalar(
        select(TimeRequest)
        .join(TeamMember, TeamMember.id == TimeRequest.team_member_id)
        .where(TimeRequest.id == request_id, TeamMember.team_id == team_id)
    )


def list_time_requests(
    db: Session,
    team_id: int,
    member_id: int | None = None,
    request_status: RequestStatus | None = None,
) -> list[TimeRequest]:
    statement = (
        select(TimeRequest)
        .join(TeamMember, TeamMember.id == TimeRequest.team_member_id)
        .where(TeamMember.team_id == team_id)
    )
    if member_id is not None:
        statement = statement.where(TimeRequest.team_member_id == member_id)
    if request_status is not None:
        statement = statement.where(TimeRequest.status == request_status)
    return list(db.scalars(statement.order_by(TimeRequest.starts_at, TimeRequest.id)).all())


def find_active_overlap(
    db: Session,
    member_id: int,
    starts_at,
    ends_at,
    exclude_request_id: int | None = None,
) -> TimeRequest | None:
    statement = select(TimeRequest).where(
            TimeRequest.team_member_id == member_id,
            TimeRequest.status.in_([RequestStatus.PENDING, RequestStatus.APPROVED]),
            TimeRequest.starts_at < ends_at,
            TimeRequest.ends_at > starts_at,
        )
    if exclude_request_id is not None:
        statement = statement.where(TimeRequest.id != exclude_request_id)
    return db.scalar(statement)
