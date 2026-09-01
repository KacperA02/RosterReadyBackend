from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.database import get_db
from app.domain.enums import MembershipRole, MembershipStatus
from app.domain.models import Team, TeamMember, TeamPolicy, User
from app.api.v2.schemas import TeamCreateRequest, TeamWithMembershipResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/teams", tags=["V2 Teams"])


@router.post("", response_model=TeamWithMembershipResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamWithMembershipResponse:
    if payload.maximum_minutes_week < payload.contracted_minutes_week:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Maximum weekly minutes cannot be lower than contracted minutes",
        )

    team = Team(
        name=payload.name.strip(),
        timezone=payload.timezone,
        created_by_user_id=current_user.id,
    )
    db.add(team)
    db.flush()
    membership = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role=MembershipRole.OWNER,
        status=MembershipStatus.ACTIVE,
        contracted_minutes_week=payload.contracted_minutes_week,
        maximum_minutes_week=payload.maximum_minutes_week,
        maximum_days_week=payload.maximum_days_week,
        maximum_consecutive_days=payload.maximum_consecutive_days,
        minimum_rest_minutes=payload.minimum_rest_minutes,
        effective_from=payload.effective_from,
    )
    db.add(membership)
    db.add(TeamPolicy(team_id=team.id))
    db.commit()
    db.refresh(team)
    db.refresh(membership)
    return TeamWithMembershipResponse(
        id=team.id,
        name=team.name,
        timezone=team.timezone,
        membership=membership,
    )


@router.get("", response_model=list[TeamWithMembershipResponse])
def list_my_teams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TeamWithMembershipResponse]:
    memberships = db.scalars(
        select(TeamMember)
        .options(selectinload(TeamMember.team))
        .where(
            TeamMember.user_id == current_user.id,
            TeamMember.status == MembershipStatus.ACTIVE,
        )
        .order_by(TeamMember.id)
    ).all()
    return [
        TeamWithMembershipResponse(
            id=membership.team.id,
            name=membership.team.name,
            timezone=membership.team.timezone,
            membership=membership,
        )
        for membership in memberships
    ]
