import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.domain.database import get_db
from app.domain.enums import InvitationStatus, MembershipRole, MembershipStatus
from app.domain.models import TeamInvitation, TeamMember, User
from app.repositories.memberships import get_member, list_members as find_members
from app.services.memberships import MANAGEMENT_ROLES, require_active_membership, to_member_response
from app.api.v2.schemas import (
    InvitationCreateRequest,
    InvitationCreatedResponse,
    InvitationResponse,
    MemberAccessUpdate,
    MemberLimitsUpdate,
    MemberResponse,
)
from app.core.security import get_current_user

router = APIRouter(tags=["V2 Memberships"])


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.post(
    "/teams/{team_id}/invitations",
    response_model=InvitationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(
    team_id: int,
    payload: InvitationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvitationCreatedResponse:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    if payload.role == MembershipRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ownership cannot be granted through an invitation",
        )

    email = payload.email.lower()
    invited_user = db.scalar(select(User).where(User.email == email))
    if invited_user and db.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == invited_user.id,
        )
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a team member")

    existing = db.scalar(
        select(TeamInvitation).where(
            TeamInvitation.team_id == team_id,
            TeamInvitation.invited_email == email,
            TeamInvitation.status == InvitationStatus.PENDING,
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pending invitation already exists")

    token = secrets.token_urlsafe(32)
    invitation = TeamInvitation(
        team_id=team_id,
        invited_email=email,
        proposed_role=payload.role,
        status=InvitationStatus.PENDING,
        token_hash=_token_hash(token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invitation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pending invitation already exists")
    db.refresh(invitation)
    return InvitationCreatedResponse.model_validate(
        {**InvitationResponse.model_validate(invitation).model_dump(), "invitation_token": token}
    )


@router.get("/teams/{team_id}/invitations", response_model=list[InvitationResponse])
def list_invitations(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TeamInvitation]:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    return list(
        db.scalars(
            select(TeamInvitation)
            .where(TeamInvitation.team_id == team_id)
            .order_by(TeamInvitation.created_at.desc())
        ).all()
    )


def _pending_invitation(db: Session, token: str) -> TeamInvitation:
    invitation = db.scalar(
        select(TeamInvitation).where(
            TeamInvitation.token_hash == _token_hash(token),
            TeamInvitation.status == InvitationStatus.PENDING,
        )
    )
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        invitation.status = InvitationStatus.EXPIRED
        db.commit()
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation expired")
    return invitation


@router.post("/invitations/{token}/accept", response_model=MemberResponse)
def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemberResponse:
    invitation = _pending_invitation(db, token)
    if invitation.invited_email != current_user.email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invitation belongs to another user")
    if db.scalar(
        select(TeamMember).where(
            TeamMember.team_id == invitation.team_id,
            TeamMember.user_id == current_user.id,
        )
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a team member")

    membership = TeamMember(
        team_id=invitation.team_id,
        user_id=current_user.id,
        role=invitation.proposed_role,
        status=MembershipStatus.ACTIVE,
        contracted_minutes_week=0,
        maximum_minutes_week=2400,
        maximum_days_week=5,
        maximum_consecutive_days=5,
        minimum_rest_minutes=660,
        effective_from=datetime.now(timezone.utc).date(),
    )
    invitation.status = InvitationStatus.ACCEPTED
    db.add(membership)
    db.commit()
    membership = db.scalar(
        select(TeamMember)
        .options(selectinload(TeamMember.user))
        .where(TeamMember.id == membership.id)
    )
    return to_member_response(membership)


@router.post("/invitations/{token}/decline", response_model=InvitationResponse)
def decline_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamInvitation:
    invitation = _pending_invitation(db, token)
    if invitation.invited_email != current_user.email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invitation belongs to another user")
    invitation.status = InvitationStatus.DECLINED
    db.commit()
    db.refresh(invitation)
    return invitation


@router.get("/teams/{team_id}/members", response_model=list[MemberResponse])
def list_members(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MemberResponse]:
    require_active_membership(db, current_user.id, team_id)
    return [to_member_response(membership) for membership in find_members(db, team_id)]


@router.patch("/teams/{team_id}/members/{member_id}/limits", response_model=MemberResponse)
def update_member_limits(
    team_id: int,
    member_id: int,
    payload: MemberLimitsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemberResponse:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    if payload.maximum_minutes_week < payload.contracted_minutes_week:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Maximum weekly minutes cannot be lower than contracted minutes",
        )
    if payload.effective_to and payload.effective_to < payload.effective_from:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Effective end date cannot be before the start date",
        )

    membership = get_member(db, team_id, member_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")
    for field, value in payload.model_dump().items():
        setattr(membership, field, value)
    db.commit()
    db.refresh(membership)
    return to_member_response(membership)

@router.patch("/teams/{team_id}/members/{member_id}/access", response_model=MemberResponse)
def update_member_access(
    team_id: int,
    member_id: int,
    payload: MemberAccessUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemberResponse:
    actor = require_active_membership(db, current_user.id, team_id, {MembershipRole.OWNER})
    membership = get_member(db, team_id, member_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")
    if membership.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Owners cannot change their own access",
        )
    if payload.role == MembershipRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Use an ownership transfer workflow to assign an owner",
        )
    membership.role = payload.role
    membership.status = payload.status
    db.commit()
    db.refresh(membership)
    return to_member_response(membership)
