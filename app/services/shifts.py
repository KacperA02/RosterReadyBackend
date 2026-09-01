from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import (
    ShiftInstance,
    ShiftInstanceSkill,
    ShiftTemplate,
    ShiftTemplateRule,
    ShiftTemplateSkill,
)
from app.repositories.shifts import get_template, list_rules


def require_template(db: Session, team_id: int, template_id: int) -> ShiftTemplate:
    template = get_template(db, team_id, template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift template not found")
    return template


def validate_template_times(start_time: time, end_time: time) -> None:
    if start_time == end_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Shift start and end times must differ",
        )


def validate_rule_period(effective_from: date, effective_to: date | None) -> None:
    if effective_to and effective_to < effective_from:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Effective end date cannot be before start date",
        )


def generate_instances(
    db: Session,
    team_id: int,
    timezone_name: str,
    period_start: date,
    period_end: date,
) -> tuple[list[ShiftInstance], int]:
    if period_end < period_start:
        raise HTTPException(status_code=422, detail="Generation end date cannot be before start date")
    if (period_end - period_start).days > 366:
        raise HTTPException(status_code=422, detail="Generate at most 367 days at a time")
    try:
        zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        raise HTTPException(status_code=422, detail="Team timezone is invalid")

    templates = list(
        db.scalars(
            select(ShiftTemplate).where(ShiftTemplate.team_id == team_id, ShiftTemplate.active.is_(True))
        ).all()
    )
    created: list[ShiftInstance] = []
    skipped = 0
    day = period_start
    while day <= period_end:
        for template in templates:
            applicable = [
                rule
                for rule in list_rules(db, template.id)
                if rule.weekday == day.weekday()
                and rule.effective_from <= day
                and (rule.effective_to is None or rule.effective_to >= day)
            ]
            if not applicable:
                continue
            rule = max(applicable, key=lambda value: value.effective_from)
            local_start = datetime.combine(day, template.start_time, tzinfo=zone)
            end_day = day + timedelta(days=1) if template.end_time <= template.start_time else day
            local_end = datetime.combine(end_day, template.end_time, tzinfo=zone)
            starts_at = local_start.astimezone(timezone.utc)
            ends_at = local_end.astimezone(timezone.utc)
            existing = db.scalar(
                select(ShiftInstance).where(
                    ShiftInstance.template_id == template.id,
                    ShiftInstance.starts_at == starts_at,
                )
            )
            if existing:
                skipped += 1
                continue
            instance = ShiftInstance(
                team_id=team_id,
                template_id=template.id,
                starts_at=starts_at,
                ends_at=ends_at,
                required_staff=rule.required_staff,
            )
            db.add(instance)
            db.flush()
            requirements = db.scalars(
                select(ShiftTemplateSkill).where(ShiftTemplateSkill.shift_template_id == template.id)
            ).all()
            for requirement in requirements:
                db.add(
                    ShiftInstanceSkill(
                        shift_instance_id=instance.id,
                        skill_id=requirement.skill_id,
                        required_count=requirement.required_count,
                    )
                )
            created.append(instance)
        day += timedelta(days=1)
    db.commit()
    for instance in created:
        db.refresh(instance)
    return created, skipped
