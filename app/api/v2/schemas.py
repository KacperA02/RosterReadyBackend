from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.enums import (
    InvitationStatus,
    MembershipRole,
    MembershipStatus,
    RequestStatus,
    SkillProficiency,
    TimeRequestType,
    ShiftStatus,
)


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    mobile_number: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MembershipSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    role: MembershipRole
    status: MembershipStatus


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    mobile_number: str | None
    memberships: list[MembershipSummary] = Field(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    timezone: str = Field(default="Europe/Dublin", min_length=1, max_length=64)
    contracted_minutes_week: int = Field(default=0, ge=0, le=10080)
    maximum_minutes_week: int = Field(default=2400, ge=0, le=10080)
    maximum_days_week: int = Field(default=5, ge=1, le=7)
    maximum_consecutive_days: int = Field(default=5, ge=1, le=7)
    minimum_rest_minutes: int = Field(default=660, ge=0, le=1440)
    effective_from: date = Field(default_factory=date.today)


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    timezone: str


class TeamWithMembershipResponse(TeamResponse):
    membership: MembershipSummary


class InvitationCreateRequest(BaseModel):
    email: EmailStr
    role: MembershipRole = MembershipRole.EMPLOYEE


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    invited_email: EmailStr
    proposed_role: MembershipRole
    status: InvitationStatus
    expires_at: datetime


class InvitationCreatedResponse(InvitationResponse):
    invitation_token: str


class MemberResponse(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: MembershipRole
    status: MembershipStatus
    contracted_minutes_week: int
    maximum_minutes_week: int
    maximum_days_week: int
    maximum_consecutive_days: int
    minimum_rest_minutes: int
    effective_from: date
    effective_to: date | None


class MemberLimitsUpdate(BaseModel):
    contracted_minutes_week: int = Field(ge=0, le=10080)
    maximum_minutes_week: int = Field(ge=0, le=10080)
    maximum_days_week: int = Field(ge=1, le=7)
    maximum_consecutive_days: int = Field(ge=1, le=7)
    minimum_rest_minutes: int = Field(ge=0, le=1440)
    effective_from: date
    effective_to: date | None = None


class MemberAccessUpdate(BaseModel):
    role: MembershipRole
    status: MembershipStatus


class SkillCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    name: str


class MemberSkillUpdate(BaseModel):
    proficiency: SkillProficiency = SkillProficiency.QUALIFIED


class MemberSkillResponse(BaseModel):
    skill_id: int
    name: str
    proficiency: SkillProficiency


class TimeRequestCreate(BaseModel):
    request_type: TimeRequestType
    starts_at: datetime
    ends_at: datetime
    reason: str | None = Field(default=None, max_length=2000)


class TimeRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_member_id: int
    request_type: TimeRequestType
    starts_at: datetime
    ends_at: datetime
    status: RequestStatus
    reason: str | None
    reviewed_by_member_id: int | None
    reviewed_at: datetime | None
    review_note: str | None


class TimeRequestReview(BaseModel):
    status: RequestStatus
    review_note: str | None = Field(default=None, max_length=2000)


class ShiftTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    start_time: time
    end_time: time


class ShiftTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    start_time: time | None = None
    end_time: time | None = None
    active: bool | None = None


class ShiftTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    name: str
    start_time: time
    end_time: time
    active: bool


class ShiftRuleCreate(BaseModel):
    weekday: int = Field(ge=0, le=6)
    required_staff: int = Field(ge=1, le=1000)
    effective_from: date
    effective_to: date | None = None


class ShiftRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shift_template_id: int
    weekday: int
    required_staff: int
    effective_from: date
    effective_to: date | None


class ShiftTemplateSkillUpdate(BaseModel):
    required_count: int = Field(default=1, ge=1, le=1000)


class ShiftTemplateSkillResponse(BaseModel):
    skill_id: int
    name: str
    required_count: int


class ShiftGenerationRequest(BaseModel):
    period_start: date
    period_end: date


class ShiftInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    template_id: int | None
    starts_at: datetime
    ends_at: datetime
    required_staff: int
    status: ShiftStatus


class ShiftGenerationResponse(BaseModel):
    created_count: int
    skipped_count: int
    instances: list[ShiftInstanceResponse]
