from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v2.schemas import (
    ShiftGenerationRequest,
    ShiftGenerationResponse,
    ShiftInstanceResponse,
    ShiftRuleCreate,
    ShiftRuleResponse,
    ShiftTemplateCreate,
    ShiftTemplateResponse,
    ShiftTemplateSkillResponse,
    ShiftTemplateSkillUpdate,
    ShiftTemplateUpdate,
)
from app.core.security import get_current_user
from app.domain.database import get_db
from app.domain.models import ShiftTemplate, ShiftTemplateRule, ShiftTemplateSkill, Team, User
from app.repositories.shifts import (
    get_rule,
    get_instance,
    list_instance_skills,
    list_instances,
    list_rules,
    list_template_skills,
    list_templates,
)
from app.services.memberships import MANAGEMENT_ROLES, require_active_membership
from app.services.shifts import (
    generate_instances,
    require_template,
    validate_rule_period,
    validate_template_times,
)
from app.services.skills import require_skill

router = APIRouter(prefix="/teams/{team_id}", tags=["V2 Shifts"])


@router.post("/shift-templates", response_model=ShiftTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_shift_template(
    team_id: int,
    payload: ShiftTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShiftTemplate:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    validate_template_times(payload.start_time, payload.end_time)
    template = ShiftTemplate(
        team_id=team_id,
        name=payload.name.strip(),
        start_time=payload.start_time,
        end_time=payload.end_time,
        active=True,
    )
    db.add(template)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Shift template already exists")
    db.refresh(template)
    return template


@router.get("/shift-templates", response_model=list[ShiftTemplateResponse])
def get_shift_templates(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ShiftTemplate]:
    require_active_membership(db, current_user.id, team_id)
    return list_templates(db, team_id)


@router.patch("/shift-templates/{template_id}", response_model=ShiftTemplateResponse)
def update_shift_template(
    team_id: int,
    template_id: int,
    payload: ShiftTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShiftTemplate:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    template = require_template(db, team_id, template_id)
    values = payload.model_dump(exclude_unset=True)
    new_start = values.get("start_time", template.start_time)
    new_end = values.get("end_time", template.end_time)
    validate_template_times(new_start, new_end)
    if "name" in values:
        values["name"] = values["name"].strip()
    for field, value in values.items():
        setattr(template, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Shift template already exists")
    db.refresh(template)
    return template


@router.post(
    "/shift-templates/{template_id}/rules",
    response_model=ShiftRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_shift_rule(
    team_id: int,
    template_id: int,
    payload: ShiftRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShiftTemplateRule:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    template = require_template(db, team_id, template_id)
    validate_rule_period(payload.effective_from, payload.effective_to)
    required_skill_counts = [item.required_count for item, _ in list_template_skills(db, template.id)]
    if required_skill_counts and max(required_skill_counts) > payload.required_staff:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Required skill count cannot exceed required staff",
        )
    rule = ShiftTemplateRule(shift_template_id=template.id, **payload.model_dump())
    db.add(rule)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Shift rule already exists")
    db.refresh(rule)
    return rule


@router.get("/shift-templates/{template_id}/rules", response_model=list[ShiftRuleResponse])
def get_shift_rules(
    team_id: int,
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ShiftTemplateRule]:
    require_active_membership(db, current_user.id, team_id)
    template = require_template(db, team_id, template_id)
    return list_rules(db, template.id)


@router.delete("/shift-templates/{template_id}/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shift_rule(
    team_id: int,
    template_id: int,
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    template = require_template(db, team_id, template_id)
    rule = get_rule(db, template.id, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift rule not found")
    db.delete(rule)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/shift-templates/{template_id}/skills/{skill_id}",
    response_model=ShiftTemplateSkillResponse,
)
def put_shift_template_skill(
    team_id: int,
    template_id: int,
    skill_id: int,
    payload: ShiftTemplateSkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShiftTemplateSkillResponse:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    template = require_template(db, team_id, template_id)
    skill = require_skill(db, team_id, skill_id)
    rules = list_rules(db, template.id)
    if rules and payload.required_count > min(rule.required_staff for rule in rules):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Required skill count cannot exceed required staff",
        )
    requirement = db.get(ShiftTemplateSkill, (template.id, skill.id))
    if requirement:
        requirement.required_count = payload.required_count
    else:
        requirement = ShiftTemplateSkill(
            shift_template_id=template.id,
            skill_id=skill.id,
            required_count=payload.required_count,
        )
        db.add(requirement)
    db.commit()
    return ShiftTemplateSkillResponse(
        skill_id=skill.id,
        name=skill.name,
        required_count=requirement.required_count,
    )


@router.get(
    "/shift-templates/{template_id}/skills",
    response_model=list[ShiftTemplateSkillResponse],
)
def get_shift_template_skills(
    team_id: int,
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ShiftTemplateSkillResponse]:
    require_active_membership(db, current_user.id, team_id)
    template = require_template(db, team_id, template_id)
    return [
        ShiftTemplateSkillResponse(
            skill_id=skill.id,
            name=skill.name,
            required_count=requirement.required_count,
        )
        for requirement, skill in list_template_skills(db, template.id)
    ]


@router.delete(
    "/shift-templates/{template_id}/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_shift_template_skill(
    team_id: int,
    template_id: int,
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    template = require_template(db, team_id, template_id)
    require_skill(db, team_id, skill_id)
    requirement = db.get(ShiftTemplateSkill, (template.id, skill_id))
    if not requirement:
        raise HTTPException(status_code=404, detail="Shift skill requirement not found")
    db.delete(requirement)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/shift-instances/generate", response_model=ShiftGenerationResponse)
def generate_shift_instances(
    team_id: int,
    payload: ShiftGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShiftGenerationResponse:
    require_active_membership(db, current_user.id, team_id, MANAGEMENT_ROLES)
    team = db.scalar(select(Team).where(Team.id == team_id))
    created, skipped = generate_instances(
        db, team_id, team.timezone, payload.period_start, payload.period_end
    )
    return ShiftGenerationResponse(
        created_count=len(created),
        skipped_count=skipped,
        instances=[ShiftInstanceResponse.model_validate(instance) for instance in created],
    )


@router.get("/shift-instances", response_model=list[ShiftInstanceResponse])
def get_shift_instances(
    team_id: int,
    starts_at: datetime,
    ends_at: datetime,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    require_active_membership(db, current_user.id, team_id)
    if starts_at.tzinfo is None or ends_at.tzinfo is None or ends_at <= starts_at:
        raise HTTPException(status_code=422, detail="A valid timezone-aware period is required")
    return list_instances(
        db,
        team_id,
        starts_at.astimezone(timezone.utc),
        ends_at.astimezone(timezone.utc),
    )


@router.get(
    "/shift-instances/{instance_id}/skills",
    response_model=list[ShiftTemplateSkillResponse],
)
def get_shift_instance_skills(
    team_id: int,
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ShiftTemplateSkillResponse]:
    require_active_membership(db, current_user.id, team_id)
    instance = get_instance(db, team_id, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Shift instance not found")
    return [
        ShiftTemplateSkillResponse(
            skill_id=skill.id,
            name=skill.name,
            required_count=requirement.required_count,
        )
        for requirement, skill in list_instance_skills(db, instance.id)
    ]
