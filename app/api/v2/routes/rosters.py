from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v2.schemas import (
    AssignmentResponse,
    ManualAssignmentCreate,
    RosterCreateRequest,
    RosterDetailResponse,
    RosterResponse,
)
from app.core.security import get_current_user
from app.domain.database import get_db
from app.domain.enums import RosterStatus, SolverStatus
from app.domain.models import Roster, Team, User
from app.repositories.rosters import list_rosters
from app.services.memberships import MANAGEMENT_ROLES, require_active_membership
from app.services.roster_solver import solve_roster
from app.services.rosters import (
    add_manual_assignment,
    assignment_responses,
    publish_roster,
    remove_assignment,
    require_draft,
    require_roster,
)

router = APIRouter(prefix="/teams/{team_id}/rosters", tags=["V2 Rosters"])


def _detail(db: Session, roster: Roster) -> RosterDetailResponse:
    data = RosterResponse.model_validate(roster).model_dump()
    return RosterDetailResponse(**data, assignments=assignment_responses(db, roster.id))


@router.post("", response_model=RosterResponse, status_code=status.HTTP_201_CREATED)
def create_roster(
    team_id: int,
    payload: RosterCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Roster:
    actor = require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    if payload.period_end < payload.period_start:
        raise HTTPException(status_code=422, detail="Roster end date cannot be before start date")
    if (payload.period_end - payload.period_start).days > 62:
        raise HTTPException(status_code=422, detail="A roster can span at most 63 days")
    roster = Roster(
        team_id=team_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        status=RosterStatus.DRAFT,
        solver_status=SolverStatus.PENDING,
        created_by_member_id=actor.id,
    )
    db.add(roster)
    db.commit()
    db.refresh(roster)
    return roster


@router.get("", response_model=list[RosterResponse])
def get_rosters(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Roster]:
    require_active_membership(db, current_user.id, team_id)
    return list_rosters(db, team_id)


@router.get("/{roster_id}", response_model=RosterDetailResponse)
def get_roster_detail(
    team_id: int,
    roster_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RosterDetailResponse:
    require_active_membership(db, current_user.id, team_id)
    return _detail(db, require_roster(db, team_id, roster_id))


@router.post("/{roster_id}/solve", response_model=RosterDetailResponse)
def solve_draft_roster(
    team_id: int,
    roster_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RosterDetailResponse:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    roster = require_roster(db, team_id, roster_id)
    require_draft(roster)
    team = db.scalar(select(Team).where(Team.id == team_id))
    roster.solver_status = SolverStatus.RUNNING
    db.commit()
    solve_roster(db, roster, team)
    db.refresh(roster)
    return _detail(db, roster)


@router.post("/{roster_id}/assignments", response_model=AssignmentResponse, status_code=201)
def create_manual_assignment(
    team_id: int,
    roster_id: int,
    payload: ManualAssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    actor = require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    roster = require_roster(db, team_id, roster_id)
    assignment = add_manual_assignment(
        db, roster, actor, payload.shift_instance_id, payload.team_member_id, payload.reason
    )
    return next(item for item in assignment_responses(db, roster.id) if item.id == assignment.id)


@router.delete("/{roster_id}/assignments/{assignment_id}", status_code=204)
def delete_roster_assignment(
    team_id: int,
    roster_id: int,
    assignment_id: int,
    reason: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    actor = require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    roster = require_roster(db, team_id, roster_id)
    remove_assignment(db, roster, assignment_id, actor, reason)
    return Response(status_code=204)


@router.post("/{roster_id}/publish", response_model=RosterResponse)
def publish_draft_roster(
    team_id: int,
    roster_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Roster:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    return publish_roster(db, require_roster(db, team_id, roster_id))
