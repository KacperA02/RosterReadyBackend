from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v2.schemas import TimeRequestCreate, TimeRequestResponse, TimeRequestReview
from app.core.security import get_current_user
from app.domain.database import get_db
from app.domain.enums import RequestStatus
from app.domain.models import TimeRequest, User
from app.repositories.time_requests import get_time_request, list_time_requests
from app.services.memberships import MANAGEMENT_ROLES, require_active_membership
from app.services.skills import require_member
from app.services.time_requests import create_time_request, require_request, update_time_request

router = APIRouter(prefix="/teams/{team_id}", tags=["V2 Time Requests"])


@router.post("/time-requests", response_model=TimeRequestResponse, status_code=status.HTTP_201_CREATED)
def submit_time_request(
    team_id: int,
    payload: TimeRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TimeRequest:
    member = require_active_membership(db, current_user.id, team_id)
    return create_time_request(db, member, **payload.model_dump())


@router.post(
    "/members/{member_id}/time-requests",
    response_model=TimeRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_time_request_for_member(
    team_id: int,
    member_id: int,
    payload: TimeRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TimeRequest:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    member = require_member(db, team_id, member_id)
    return create_time_request(db, member, **payload.model_dump())


@router.get("/time-requests/mine", response_model=list[TimeRequestResponse])
def list_my_time_requests(
    team_id: int,
    request_status: RequestStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TimeRequest]:
    member = require_active_membership(db, current_user.id, team_id)
    return list_time_requests(db, team_id, member.id, request_status)


@router.get("/time-requests", response_model=list[TimeRequestResponse])
def list_team_time_requests(
    team_id: int,
    member_id: int | None = None,
    request_status: RequestStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TimeRequest]:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    if member_id is not None:
        require_member(db, team_id, member_id)
    return list_time_requests(db, team_id, member_id, request_status)


@router.patch("/time-requests/{request_id}/cancel", response_model=TimeRequestResponse)
def cancel_time_request(
    team_id: int,
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TimeRequest:
    member = require_active_membership(db, current_user.id, team_id)
    request = require_request(get_time_request(db, team_id, request_id))
    if request.team_member_id != member.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot cancel another member's request")
    if request.status in {RequestStatus.REJECTED, RequestStatus.CANCELLED}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request cannot be cancelled")
    request.status = RequestStatus.CANCELLED
    db.commit()
    db.refresh(request)
    return request


@router.patch("/time-requests/{request_id}", response_model=TimeRequestResponse)
def edit_time_request(
    team_id: int,
    request_id: int,
    payload: TimeRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TimeRequest:
    member = require_active_membership(db, current_user.id, team_id)
    request = require_request(get_time_request(db, team_id, request_id))
    is_manager = member.role in MANAGEMENT_ROLES
    if not is_manager and request.team_member_id != member.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit another member's request")
    if not is_manager and request.status != RequestStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending requests can be edited")
    if request.status in {RequestStatus.REJECTED, RequestStatus.CANCELLED}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request cannot be edited")
    return update_time_request(db, request, **payload.model_dump())


@router.patch("/time-requests/{request_id}/review", response_model=TimeRequestResponse)
def review_time_request(
    team_id: int,
    request_id: int,
    payload: TimeRequestReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TimeRequest:
    reviewer = require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    request = require_request(get_time_request(db, team_id, request_id))
    if payload.status not in {RequestStatus.APPROVED, RequestStatus.REJECTED}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Review status must be APPROVED or REJECTED",
        )
    if request.status != RequestStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending requests can be reviewed")
    request.status = payload.status
    request.reviewed_by_member_id = reviewer.id
    request.reviewed_at = datetime.now(timezone.utc)
    request.review_note = payload.review_note.strip() if payload.review_note else None
    db.commit()
    db.refresh(request)
    return request
