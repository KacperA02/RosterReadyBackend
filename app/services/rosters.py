from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from app.api.v2.schemas import AssignmentResponse
from app.domain.enums import AssignmentEventType, AssignmentSource, RosterStatus, SolverStatus
from app.domain.models import (
    Assignment,
    AssignmentEvent,
    Roster,
    ShiftInstance,
    Team,
    TeamMember,
)
from app.repositories.rosters import get_roster, list_assignment_rows


def require_roster(db: Session, team_id: int, roster_id: int) -> Roster:
    roster = get_roster(db, team_id, roster_id)
    if not roster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roster not found")
    return roster


def require_draft(roster: Roster) -> None:
    if roster.status != RosterStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only draft rosters can be changed")


def assignment_responses(db: Session, roster_id: int) -> list[AssignmentResponse]:
    return [
        AssignmentResponse(
            id=assignment.id,
            roster_id=assignment.roster_id,
            shift_instance_id=assignment.shift_instance_id,
            team_member_id=assignment.team_member_id,
            source=assignment.source,
            locked=assignment.locked,
            starts_at=shift.starts_at,
            ends_at=shift.ends_at,
            member_name=f"{user.first_name} {user.last_name}",
        )
        for assignment, shift, _, user in list_assignment_rows(db, roster_id)
    ]


def add_manual_assignment(
    db: Session,
    roster: Roster,
    actor: TeamMember,
    shift_instance_id: int,
    team_member_id: int,
    reason: str | None,
) -> Assignment:
    require_draft(roster)
    shift = db.scalar(
        select(ShiftInstance).where(
            ShiftInstance.id == shift_instance_id,
            ShiftInstance.team_id == roster.team_id,
        )
    )
    member = db.scalar(
        select(TeamMember).where(
            TeamMember.id == team_member_id,
            TeamMember.team_id == roster.team_id,
        )
    )
    if not shift or not member:
        raise HTTPException(status_code=404, detail="Shift or team member not found")
    team = db.get(Team, roster.team_id)
    local_shift_date = shift.starts_at.astimezone(ZoneInfo(team.timezone)).date()
    if not (roster.period_start <= local_shift_date <= roster.period_end):
        raise HTTPException(status_code=422, detail="Shift is outside the roster period")
    duplicate = db.scalar(
        select(Assignment).where(
            Assignment.roster_id == roster.id,
            Assignment.shift_instance_id == shift.id,
            Assignment.team_member_id == member.id,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Member is already assigned to this shift")
    assignment = Assignment(
        roster_id=roster.id,
        shift_instance_id=shift.id,
        team_member_id=member.id,
        source=AssignmentSource.OVERRIDE,
        locked=True,
    )
    db.add(assignment)
    db.flush()
    db.add(
        AssignmentEvent(
            assignment_id=assignment.id,
            actor_member_id=actor.id,
            event_type=AssignmentEventType.CREATED,
            reason=reason,
            new_values={"shift_instance_id": shift.id, "team_member_id": member.id},
        )
    )
    roster.solver_status = SolverStatus.PENDING
    db.commit()
    db.refresh(assignment)
    return assignment


def remove_assignment(
    db: Session,
    roster: Roster,
    assignment_id: int,
    actor: TeamMember,
    reason: str | None,
) -> None:
    require_draft(roster)
    assignment = db.scalar(
        select(Assignment).where(Assignment.id == assignment_id, Assignment.roster_id == roster.id)
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    db.add(
        AssignmentEvent(
            assignment_id=assignment.id,
            actor_member_id=actor.id,
            event_type=AssignmentEventType.REMOVED,
            reason=reason,
            previous_values={
                "shift_instance_id": assignment.shift_instance_id,
                "team_member_id": assignment.team_member_id,
            },
        )
    )
    db.flush()
    db.delete(assignment)
    roster.solver_status = SolverStatus.PENDING
    db.commit()


def publish_roster(db: Session, roster: Roster) -> Roster:
    require_draft(roster)
    if roster.solver_status not in {SolverStatus.FEASIBLE, SolverStatus.OPTIMAL}:
        raise HTTPException(status_code=409, detail="Roster must have a feasible solution before publishing")
    roster.status = RosterStatus.PUBLISHED
    roster.published_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if "uq_rosters_published_period" in str(error):
            raise HTTPException(
                status_code=409,
                detail="A roster is already published for this period",
            )
        raise
    db.refresh(roster)
    return roster
