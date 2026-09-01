from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.domain.database import Base
from app.domain.enums import (
    AssignmentEventType,
    AssignmentSource,
    InvitationStatus,
    MembershipRole,
    MembershipStatus,
    RequestStatus,
    RosterStatus,
    ShiftStatus,
    SkillProficiency,
    SolverStatus,
    TimeRequestType,
)

JSON_DOCUMENT = JSON().with_variant(JSONB(), "postgresql")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    mobile_number: Mapped[str | None] = mapped_column(String(32), unique=True)

    memberships: Mapped[list[TeamMember]] = relationship(back_populates="user")


class Team(TimestampMixin, Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", server_default="UTC")
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    members: Mapped[list[TeamMember]] = relationship(back_populates="team")
    policy: Mapped[TeamPolicy | None] = relationship(back_populates="team", uselist=False)


class TeamMember(TimestampMixin, Base):
    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_members_team_user"),
        CheckConstraint("contracted_minutes_week >= 0", name="ck_member_contract_minutes"),
        CheckConstraint("maximum_minutes_week >= contracted_minutes_week", name="ck_member_max_minutes"),
        CheckConstraint("maximum_days_week BETWEEN 1 AND 7", name="ck_member_max_days"),
        CheckConstraint("maximum_consecutive_days BETWEEN 1 AND 7", name="ck_member_consecutive_days"),
        CheckConstraint("minimum_rest_minutes >= 0", name="ck_member_rest_minutes"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_member_effective_period",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[MembershipRole] = mapped_column(Enum(MembershipRole, name="membership_role"))
    status: Mapped[MembershipStatus] = mapped_column(
        Enum(MembershipStatus, name="membership_status"),
        default=MembershipStatus.ACTIVE,
    )
    contracted_minutes_week: Mapped[int] = mapped_column(Integer, default=0)
    maximum_minutes_week: Mapped[int] = mapped_column(Integer, default=2400)
    maximum_days_week: Mapped[int] = mapped_column(SmallInteger, default=5)
    maximum_consecutive_days: Mapped[int] = mapped_column(SmallInteger, default=5)
    minimum_rest_minutes: Mapped[int] = mapped_column(Integer, default=660)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)

    team: Mapped[Team] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships")


class TeamPolicy(Base):
    __tablename__ = "team_policies"
    __table_args__ = (
        CheckConstraint("solver_limit_seconds BETWEEN 1 AND 300", name="ck_policy_solver_limit"),
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    )
    solver_limit_seconds: Mapped[int] = mapped_column(Integer, default=5)
    fairness_weight: Mapped[int] = mapped_column(Integer, default=100)
    preference_weight: Mapped[int] = mapped_column(Integer, default=50)
    overtime_weight: Mapped[int] = mapped_column(Integer, default=200)
    change_weight: Mapped[int] = mapped_column(Integer, default=25)
    max_hours_hard: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )

    team: Mapped[Team] = relationship(back_populates="policy")


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("team_id", "name", name="uq_skills_team_name"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))


class MemberSkill(Base):
    __tablename__ = "member_skills"

    team_member_id: Mapped[int] = mapped_column(
        ForeignKey("team_members.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    proficiency: Mapped[SkillProficiency] = mapped_column(
        Enum(SkillProficiency, name="skill_proficiency"),
        default=SkillProficiency.QUALIFIED,
    )


class ShiftTemplate(TimestampMixin, Base):
    __tablename__ = "shift_templates"
    __table_args__ = (CheckConstraint("end_time <> start_time", name="ck_template_nonzero_duration"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ShiftTemplateRule(Base):
    __tablename__ = "shift_template_rules"
    __table_args__ = (
        UniqueConstraint("shift_template_id", "weekday", "effective_from", name="uq_template_rule_period"),
        CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_template_rule_weekday"),
        CheckConstraint("required_staff > 0", name="ck_template_rule_staff"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_template_rule_effective_period",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    shift_template_id: Mapped[int] = mapped_column(
        ForeignKey("shift_templates.id", ondelete="CASCADE"), index=True
    )
    weekday: Mapped[int] = mapped_column(SmallInteger)
    required_staff: Mapped[int] = mapped_column(Integer, default=1)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class ShiftTemplateSkill(Base):
    __tablename__ = "shift_template_skills"
    __table_args__ = (CheckConstraint("required_count > 0", name="ck_template_skill_count"),)

    shift_template_id: Mapped[int] = mapped_column(
        ForeignKey("shift_templates.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    required_count: Mapped[int] = mapped_column(Integer, default=1)


class ShiftInstance(TimestampMixin, Base):
    __tablename__ = "shift_instances"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_shift_instance_duration"),
        CheckConstraint("required_staff > 0", name="ck_shift_instance_staff"),
        Index("ix_shift_instances_team_starts", "team_id", "starts_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    template_id: Mapped[int | None] = mapped_column(ForeignKey("shift_templates.id", ondelete="SET NULL"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    required_staff: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[ShiftStatus] = mapped_column(
        Enum(ShiftStatus, name="shift_status"), default=ShiftStatus.OPEN
    )


class ShiftInstanceSkill(Base):
    __tablename__ = "shift_instance_skills"
    __table_args__ = (CheckConstraint("required_count > 0", name="ck_instance_skill_count"),)

    shift_instance_id: Mapped[int] = mapped_column(
        ForeignKey("shift_instances.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    required_count: Mapped[int] = mapped_column(Integer, default=1)


class TimeRequest(TimestampMixin, Base):
    __tablename__ = "time_requests"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_time_request_duration"),
        Index("ix_time_requests_member_period", "team_member_id", "starts_at", "ends_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    team_member_id: Mapped[int] = mapped_column(
        ForeignKey("team_members.id", ondelete="CASCADE"), index=True
    )
    shift_instance_id: Mapped[int | None] = mapped_column(
        ForeignKey("shift_instances.id", ondelete="SET NULL")
    )
    request_type: Mapped[TimeRequestType] = mapped_column(
        Enum(TimeRequestType, name="time_request_type")
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status"), default=RequestStatus.PENDING
    )
    reason: Mapped[str | None] = mapped_column(Text)
    reviewed_by_member_id: Mapped[int | None] = mapped_column(ForeignKey("team_members.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(Text)


class Roster(TimestampMixin, Base):
    __tablename__ = "rosters"
    __table_args__ = (
        CheckConstraint("period_end >= period_start", name="ck_roster_period"),
        Index("ix_rosters_team_period", "team_id", "period_start", "period_end"),
        Index(
            "uq_rosters_published_period",
            "team_id",
            "period_start",
            "period_end",
            unique=True,
            postgresql_where=text("status = 'PUBLISHED'"),
            sqlite_where=text("status = 'PUBLISHED'"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    status: Mapped[RosterStatus] = mapped_column(
        Enum(RosterStatus, name="roster_status"), default=RosterStatus.DRAFT
    )
    solver_status: Mapped[SolverStatus] = mapped_column(
        Enum(SolverStatus, name="solver_status"), default=SolverStatus.PENDING
    )
    solver_duration_ms: Mapped[int | None] = mapped_column(Integer)
    objective_score: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    solver_metadata: Mapped[dict | None] = mapped_column(JSON_DOCUMENT)
    created_by_member_id: Mapped[int] = mapped_column(ForeignKey("team_members.id"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Assignment(TimestampMixin, Base):
    __tablename__ = "assignments"
    __table_args__ = (
        UniqueConstraint(
            "roster_id", "shift_instance_id", "team_member_id", name="uq_assignment_member_shift"
        ),
        Index("ix_assignments_roster_shift", "roster_id", "shift_instance_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    roster_id: Mapped[int] = mapped_column(ForeignKey("rosters.id", ondelete="CASCADE"))
    shift_instance_id: Mapped[int] = mapped_column(ForeignKey("shift_instances.id", ondelete="CASCADE"))
    team_member_id: Mapped[int] = mapped_column(ForeignKey("team_members.id", ondelete="CASCADE"))
    source: Mapped[AssignmentSource] = mapped_column(
        Enum(AssignmentSource, name="assignment_source"), default=AssignmentSource.SOLVER
    )
    locked: Mapped[bool] = mapped_column(Boolean, default=False)


class AssignmentEvent(TimestampMixin, Base):
    __tablename__ = "assignment_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    actor_member_id: Mapped[int] = mapped_column(ForeignKey("team_members.id"))
    event_type: Mapped[AssignmentEventType] = mapped_column(
        Enum(AssignmentEventType, name="assignment_event_type")
    )
    reason: Mapped[str | None] = mapped_column(Text)
    previous_values: Mapped[dict | None] = mapped_column(JSON_DOCUMENT)
    new_values: Mapped[dict | None] = mapped_column(JSON_DOCUMENT)


class TeamInvitation(TimestampMixin, Base):
    __tablename__ = "team_invitations"
    __table_args__ = (Index("ix_invitations_team_status", "team_id", "status"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    invited_email: Mapped[str] = mapped_column(String(320))
    proposed_role: Mapped[MembershipRole] = mapped_column(Enum(MembershipRole, name="invitation_role"))
    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus, name="invitation_status"), default=InvitationStatus.PENDING
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
