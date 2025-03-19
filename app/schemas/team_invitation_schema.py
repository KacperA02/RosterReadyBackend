# app/schemas/team_invitation_schema.py
from pydantic import BaseModel
from app.enums import InvitationStatus


class TeamInvitationBase(BaseModel):
    user_id: int
    team_id: int
    status: InvitationStatus = InvitationStatus.PENDING 

class TeamInvitationResponse(TeamInvitationBase):
    id: int

    class Config:
        from_attributes = True
