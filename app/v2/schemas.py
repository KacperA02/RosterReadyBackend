from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.enums import MembershipRole, MembershipStatus


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
