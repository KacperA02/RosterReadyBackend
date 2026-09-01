from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.enums import RequestStatus
from app.domain.models import TeamMember, TimeRequest
from app.repositories.time_requests import find_active_overlap


def normalize_period(starts_at: datetime, ends_at: datetime) -> tuple[datetime, datetime]:
    if starts_at.tzinfo is None or ends_at.tzinfo is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Start and end times must include a timezone",
        )
    starts_at = starts_at.astimezone(timezone.utc)
    ends_at = ends_at.astimezone(timezone.utc)
    if ends_at <= starts_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="End time must be after start time",
        )
    return starts_at, ends_at


def create_time_request(
    db: Session,
    member: TeamMember,
    request_type,
    starts_at: datetime,
    ends_at: datetime,
    reason: str | None,
) -> TimeRequest:
    starts_at, ends_at = normalize_period(starts_at, ends_at)
    if find_active_overlap(db, member.id, starts_at, ends_at):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active time request already overlaps this period",
        )
    request = TimeRequest(
        team_member_id=member.id,
        request_type=request_type,
        starts_at=starts_at,
        ends_at=ends_at,
        status=RequestStatus.PENDING,
        reason=reason.strip() if reason else None,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def require_request(request: TimeRequest | None) -> TimeRequest:
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time request not found")
    return request


def update_time_request(
    db: Session,
    request: TimeRequest,
    request_type,
    starts_at: datetime,
    ends_at: datetime,
    reason: str | None,
) -> TimeRequest:
    starts_at, ends_at = normalize_period(starts_at, ends_at)
    if find_active_overlap(db, request.team_member_id, starts_at, ends_at, request.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active time request already overlaps this period",
        )
    request.request_type = request_type
    request.starts_at = starts_at
    request.ends_at = ends_at
    request.reason = reason.strip() if reason else None
    db.commit()
    db.refresh(request)
    return request
