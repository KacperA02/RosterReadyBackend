from enum import Enum


class MembershipRole(str, Enum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"


class MembershipStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    INVITED = "INVITED"


class SkillProficiency(str, Enum):
    QUALIFIED = "QUALIFIED"
    ADVANCED = "ADVANCED"


class ShiftStatus(str, Enum):
    OPEN = "OPEN"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class TimeRequestType(str, Enum):
    UNAVAILABLE = "UNAVAILABLE"
    HOLIDAY = "HOLIDAY"
    SICK_LEAVE = "SICK_LEAVE"
    PERSONAL_LEAVE = "PERSONAL_LEAVE"
    PREFERRED_SHIFT = "PREFERRED_SHIFT"
    AVOID_SHIFT = "AVOID_SHIFT"


class RequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class RosterStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class SolverStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FEASIBLE = "FEASIBLE"
    OPTIMAL = "OPTIMAL"
    INFEASIBLE = "INFEASIBLE"
    FAILED = "FAILED"


class AssignmentSource(str, Enum):
    SOLVER = "SOLVER"
    MANUAL = "MANUAL"
    OVERRIDE = "OVERRIDE"


class AssignmentEventType(str, Enum):
    CREATED = "CREATED"
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    REASSIGNED = "REASSIGNED"
    REMOVED = "REMOVED"


class InvitationStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"

