from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from time import perf_counter
from zoneinfo import ZoneInfo

from ortools.sat.python import cp_model
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.enums import (
    AssignmentSource,
    MembershipStatus,
    RequestStatus,
    ShiftStatus,
    SolverStatus,
    TimeRequestType,
)
from app.domain.models import (
    Assignment,
    MemberSkill,
    ShiftInstance,
    ShiftInstanceSkill,
    Team,
    TeamMember,
    TeamPolicy,
    TimeRequest,
)

HARD_UNAVAILABLE_TYPES = {
    TimeRequestType.UNAVAILABLE,
    TimeRequestType.HOLIDAY,
    TimeRequestType.SICK_LEAVE,
    TimeRequestType.PERSONAL_LEAVE,
}


def _overlaps(start_a, end_a, start_b, end_b) -> bool:
    return start_a < end_b and end_a > start_b


def solve_roster(db: Session, roster, team: Team) -> None:
    started = perf_counter()
    zone = ZoneInfo(team.timezone)
    period_start_utc = datetime.combine(roster.period_start, time.min, tzinfo=zone).astimezone(timezone.utc)
    period_end_utc = datetime.combine(roster.period_end + timedelta(days=1), time.min, tzinfo=zone).astimezone(timezone.utc)
    shifts = list(
        db.scalars(
            select(ShiftInstance).where(
                ShiftInstance.team_id == team.id,
                ShiftInstance.starts_at >= period_start_utc,
                ShiftInstance.starts_at < period_end_utc,
                ShiftInstance.status == ShiftStatus.OPEN,
            ).order_by(ShiftInstance.starts_at)
        ).all()
    )
    members = list(
        db.scalars(
            select(TeamMember).where(
                TeamMember.team_id == team.id,
                TeamMember.status == MembershipStatus.ACTIVE,
                TeamMember.effective_from <= roster.period_end,
                (TeamMember.effective_to.is_(None) | (TeamMember.effective_to >= roster.period_start)),
            ).order_by(TeamMember.id)
        ).all()
    )
    policy = db.get(TeamPolicy, team.id) or TeamPolicy(team_id=team.id)
    if not shifts or not members:
        roster.solver_status = SolverStatus.INFEASIBLE
        roster.solver_duration_ms = int((perf_counter() - started) * 1000)
        roster.solver_metadata = {"reason": "No open shifts or active members", "shift_count": len(shifts)}
        db.commit()
        return

    member_skills = defaultdict(set)
    for member_id, skill_id in db.execute(
        select(MemberSkill.team_member_id, MemberSkill.skill_id).where(
            MemberSkill.team_member_id.in_([member.id for member in members])
        )
    ):
        member_skills[member_id].add(skill_id)
    shift_skills = defaultdict(list)
    for shift_id, skill_id, count in db.execute(
        select(
            ShiftInstanceSkill.shift_instance_id,
            ShiftInstanceSkill.skill_id,
            ShiftInstanceSkill.required_count,
        ).where(ShiftInstanceSkill.shift_instance_id.in_([shift.id for shift in shifts]))
    ):
        shift_skills[shift_id].append((skill_id, count))
    requests = list(
        db.scalars(
            select(TimeRequest).where(
                TimeRequest.team_member_id.in_([member.id for member in members]),
                TimeRequest.status == RequestStatus.APPROVED,
                TimeRequest.starts_at < period_end_utc,
                TimeRequest.ends_at > period_start_utc,
            )
        ).all()
    )
    requests_by_member = defaultdict(list)
    for request in requests:
        requests_by_member[request.team_member_id].append(request)

    model = cp_model.CpModel()
    assigned = {
        (shift.id, member.id): model.new_bool_var(f"s{shift.id}_m{member.id}")
        for shift in shifts
        for member in members
    }
    locked_assignments = list(
        db.scalars(
            select(Assignment).where(Assignment.roster_id == roster.id, Assignment.locked.is_(True))
        ).all()
    )
    locked_pairs = {
        (assignment.shift_instance_id, assignment.team_member_id)
        for assignment in locked_assignments
    }
    variables = assigned.keys()
    for locked in locked_assignments:
        if (locked.shift_instance_id, locked.team_member_id) not in variables:
            roster.solver_status = SolverStatus.INFEASIBLE
            roster.solver_duration_ms = int((perf_counter() - started) * 1000)
            roster.solver_metadata = {"reason": "A locked assignment is outside the eligible solve set"}
            db.commit()
            return
        model.add(assigned[locked.shift_instance_id, locked.team_member_id] == 1)
    for shift in shifts:
        model.add(sum(assigned[shift.id, member.id] for member in members) == shift.required_staff)
        for skill_id, required_count in shift_skills[shift.id]:
            model.add(
                sum(
                    assigned[shift.id, member.id]
                    for member in members
                    if skill_id in member_skills[member.id]
                )
                >= required_count
            )

    preference_terms = []
    for member in members:
        for shift in shifts:
            variable = assigned[shift.id, member.id]
            local_date = shift.starts_at.astimezone(zone).date()
            if local_date < member.effective_from or (member.effective_to and local_date > member.effective_to):
                model.add(variable == 0)
            for request in requests_by_member[member.id]:
                if not _overlaps(shift.starts_at, shift.ends_at, request.starts_at, request.ends_at):
                    continue
                if request.request_type in HARD_UNAVAILABLE_TYPES:
                    model.add(variable == 0)
                elif request.request_type == TimeRequestType.AVOID_SHIFT:
                    preference_terms.append(-policy.preference_weight * variable)
                elif request.request_type == TimeRequestType.PREFERRED_SHIFT:
                    preference_terms.append(policy.preference_weight * variable)

        for index, first in enumerate(shifts):
            for second in shifts[index + 1 :]:
                rest_minutes = int((second.starts_at - first.ends_at).total_seconds() // 60)
                if _overlaps(first.starts_at, first.ends_at, second.starts_at, second.ends_at) or rest_minutes < member.minimum_rest_minutes:
                    model.add(assigned[first.id, member.id] + assigned[second.id, member.id] <= 1)

    shifts_by_week = defaultdict(list)
    shifts_by_date = defaultdict(list)
    for shift in shifts:
        local_date = shift.starts_at.astimezone(zone).date()
        shifts_by_week[local_date.isocalendar()[:2]].append(shift)
        shifts_by_date[local_date].append(shift)

    fairness_terms = []
    for member in members:
        for weekly_shifts in shifts_by_week.values():
            minutes = {
                shift.id: max(1, int((shift.ends_at - shift.starts_at).total_seconds() // 60))
                for shift in weekly_shifts
            }
            worked = sum(minutes[shift.id] * assigned[shift.id, member.id] for shift in weekly_shifts)
            model.add(worked <= member.maximum_minutes_week)
            deviation = model.new_int_var(0, 10080, f"deviation_{member.id}_{weekly_shifts[0].id}")
            model.add(deviation >= worked - member.contracted_minutes_week)
            model.add(deviation >= member.contracted_minutes_week - worked)
            fairness_terms.append(-policy.fairness_weight * deviation)

            dates = sorted({shift.starts_at.astimezone(zone).date() for shift in weekly_shifts})
            day_vars = []
            for work_date in dates:
                day_var = model.new_bool_var(f"day_{member.id}_{work_date}")
                day_assignments = [assigned[shift.id, member.id] for shift in shifts_by_date[work_date]]
                model.add(sum(day_assignments) >= day_var)
                model.add(sum(day_assignments) <= len(day_assignments) * day_var)
                day_vars.append(day_var)
            model.add(sum(day_vars) <= member.maximum_days_week)

        all_dates = [roster.period_start + timedelta(days=offset) for offset in range((roster.period_end - roster.period_start).days + 1)]
        working_by_date = {}
        for work_date in all_dates:
            day_var = model.new_bool_var(f"consecutive_{member.id}_{work_date}")
            date_assignments = [assigned[shift.id, member.id] for shift in shifts_by_date.get(work_date, [])]
            if date_assignments:
                model.add(sum(date_assignments) >= day_var)
                model.add(sum(date_assignments) <= len(date_assignments) * day_var)
            else:
                model.add(day_var == 0)
            working_by_date[work_date] = day_var
        window = member.maximum_consecutive_days + 1
        for offset in range(max(0, len(all_dates) - window + 1)):
            model.add(sum(working_by_date[day] for day in all_dates[offset : offset + window]) <= member.maximum_consecutive_days)

    model.maximize(sum(fairness_terms + preference_terms))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = policy.solver_limit_seconds
    solver.parameters.num_search_workers = 8
    result = solver.solve(model)
    roster.solver_duration_ms = int((perf_counter() - started) * 1000)
    roster.solver_metadata = {
        "shift_count": len(shifts),
        "member_count": len(members),
        "conflicts": solver.num_conflicts,
        "branches": solver.num_branches,
        "solver_response": solver.response_stats(),
    }
    if result not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
        roster.solver_status = SolverStatus.INFEASIBLE if result == cp_model.INFEASIBLE else SolverStatus.FAILED
        db.execute(
            delete(Assignment).where(
                Assignment.roster_id == roster.id,
                Assignment.locked.is_(False),
            )
        )
        db.commit()
        return
    db.execute(delete(Assignment).where(Assignment.roster_id == roster.id, Assignment.locked.is_(False)))
    for shift in shifts:
        for member in members:
            if solver.value(assigned[shift.id, member.id]):
                if (shift.id, member.id) in locked_pairs:
                    continue
                db.add(
                    Assignment(
                        roster_id=roster.id,
                        shift_instance_id=shift.id,
                        team_member_id=member.id,
                        source=AssignmentSource.SOLVER,
                        locked=False,
                    )
                )
    roster.solver_status = SolverStatus.OPTIMAL if result == cp_model.OPTIMAL else SolverStatus.FEASIBLE
    roster.objective_score = solver.objective_value
    db.commit()
