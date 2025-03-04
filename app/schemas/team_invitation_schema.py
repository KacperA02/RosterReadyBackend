# app/schemas/team_invitation_schema.py
from pydantic import BaseModel
from enum import Enum

class InvitationStatusEnum(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

class TeamInvitationBase(BaseModel):
    user_id: int
    team_id: int
    status: InvitationStatusEnum = InvitationStatusEnum.PENDING  

class TeamInvitationResponse(TeamInvitationBase):
    id: int

    class Config:
        from_attributes = True
