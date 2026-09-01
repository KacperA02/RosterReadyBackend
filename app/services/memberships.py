from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.v2.schemas import MemberResponse
from app.domain.enums import MembershipRole
from app.domain.models import TeamMember
from app.repositories.memberships import get_active_membership


MANAGEMENT_ROLES = {MembershipRole.OWNER, MembershipRole.MANAGER}


def require_active_membership(
    db: Session,
    user_id: int,
    team_id: int,
    allowed_roles: set[MembershipRole] | None = None,
) -> TeamMember:
    membership = get_active_membership(db, user_id, team_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a team member")
    if allowed_roles and membership.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient team permissions")
    return membership


def to_member_response(membership: TeamMember) -> MemberResponse:
    return MemberResponse(
        id=membership.id,
        user_id=membership.user_id,
        first_name=membership.user.first_name,
        last_name=membership.user.last_name,
        email=membership.user.email,
        role=membership.role,
        status=membership.status,
        contracted_minutes_week=membership.contracted_minutes_week,
        maximum_minutes_week=membership.maximum_minutes_week,
        maximum_days_week=membership.maximum_days_week,
        maximum_consecutive_days=membership.maximum_consecutive_days,
        minimum_rest_minutes=membership.minimum_rest_minutes,
        effective_from=membership.effective_from,
        effective_to=membership.effective_to,
    )

