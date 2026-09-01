from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import (
    ShiftInstance,
    ShiftInstanceSkill,
    ShiftTemplate,
    ShiftTemplateRule,
    ShiftTemplateSkill,
    Skill,
)


def get_template(db: Session, team_id: int, template_id: int) -> ShiftTemplate | None:
    return db.scalar(
        select(ShiftTemplate).where(ShiftTemplate.id == template_id, ShiftTemplate.team_id == team_id)
    )


def list_templates(db: Session, team_id: int) -> list[ShiftTemplate]:
    return list(
        db.scalars(
            select(ShiftTemplate).where(ShiftTemplate.team_id == team_id).order_by(ShiftTemplate.name)
        ).all()
    )


def list_rules(db: Session, template_id: int) -> list[ShiftTemplateRule]:
    return list(
        db.scalars(
            select(ShiftTemplateRule)
            .where(ShiftTemplateRule.shift_template_id == template_id)
            .order_by(ShiftTemplateRule.weekday, ShiftTemplateRule.effective_from)
        ).all()
    )


def get_rule(db: Session, template_id: int, rule_id: int) -> ShiftTemplateRule | None:
    return db.scalar(
        select(ShiftTemplateRule).where(
            ShiftTemplateRule.id == rule_id,
            ShiftTemplateRule.shift_template_id == template_id,
        )
    )


def list_template_skills(db: Session, template_id: int) -> list[tuple[ShiftTemplateSkill, Skill]]:
    return list(
        db.execute(
            select(ShiftTemplateSkill, Skill)
            .join(Skill, Skill.id == ShiftTemplateSkill.skill_id)
            .where(ShiftTemplateSkill.shift_template_id == template_id)
            .order_by(Skill.name)
        ).all()
    )


def list_instances(
    db: Session,
    team_id: int,
    starts_at: datetime,
    ends_at: datetime,
) -> list[ShiftInstance]:
    return list(
        db.scalars(
            select(ShiftInstance)
            .where(
                ShiftInstance.team_id == team_id,
                ShiftInstance.starts_at < ends_at,
                ShiftInstance.ends_at > starts_at,
            )
            .order_by(ShiftInstance.starts_at, ShiftInstance.id)
        ).all()
    )


def get_instance(db: Session, team_id: int, instance_id: int) -> ShiftInstance | None:
    return db.scalar(
        select(ShiftInstance).where(ShiftInstance.id == instance_id, ShiftInstance.team_id == team_id)
    )


def list_instance_skills(db: Session, instance_id: int) -> list[tuple[ShiftInstanceSkill, Skill]]:
    return list(
        db.execute(
            select(ShiftInstanceSkill, Skill)
            .join(Skill, Skill.id == ShiftInstanceSkill.skill_id)
            .where(ShiftInstanceSkill.shift_instance_id == instance_id)
            .order_by(Skill.name)
        ).all()
    )
