from enum import Enum

class SolutionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAST = "PAST"
    DRAFT = "DRAFT"

class InvitationStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"