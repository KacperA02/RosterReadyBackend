# app/schemas/team_invitation_schema.py
from pydantic import BaseModel
from app.enums import InvitationStatus
from app.schemas.team_schema import UserI 
from app.schemas.team_schema import TeamCreate  

class TeamInvitationBase(BaseModel):
    user_id: int
    team_id: int
    status: InvitationStatus = InvitationStatus.PENDING 

class TeamInvitationResponse(TeamInvitationBase):
    id: int

    class Config:
        from_attributes = True
        
class UserPendingInvitationResponse(TeamInvitationResponse):
    team: TeamCreate

    class Config:
        from_attributes = True


class TeamPendingInvitationResponse(TeamInvitationResponse):
    user: UserI

    class Config:
        from_attributes = True