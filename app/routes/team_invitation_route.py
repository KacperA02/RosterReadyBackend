# app/routes/team_invitations_routes.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.crud.team_invitation_crud import invite_user_to_team, accept_invitation, reject_invitation, get_pending_invitations
from app.schemas.team_invitation_schema import TeamInvitationResponse
from app.dependencies.db_config import get_db
from app.dependencies.auth import get_current_user
from app.schemas.user_schema import UserResponse
from app.services.websocket_manager import manager
from app.models.team_model import Team

router = APIRouter()
# inviting a specifc user to a team
@router.post("/invite/{user_id}", response_model=TeamInvitationResponse)
async def invite_user(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
):
    invitation = invite_user_to_team(db, user_id, current_user)

    # WebSocket Notification to the invited user
    await manager.send_to_user(
        str(user_id), 
        f"{current_user.first_name} has invited you to join their team."
    )
    print(f"[WS] Invitation sent to user {user_id}")

    return invitation


# accepting an invitation
@router.post("/accept/{invitation_id}", response_model=TeamInvitationResponse)
async def accept_invitation_route(
    invitation_id: int, 
    current_user: UserResponse = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    invitation, error = accept_invitation(db, current_user.id, invitation_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    team = db.query(Team).filter(Team.id == invitation.team_id).first()
    if team and team.creator_id:
        message = f"{current_user.first_name} has accepted your team invitation."
        await manager.send_to_user(str(team.creator_id), message)
        print(f"[WS] Notified employer {current_user.id} they approved the invitation")

    return invitation


# rejecting an invitation
@router.post("/reject/{invitation_id}", response_model=TeamInvitationResponse)
async def reject_invitation_route(
    invitation_id: int, 
    current_user: UserResponse = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    invitation, error = reject_invitation(db, current_user.id, invitation_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    team = db.query(Team).filter(Team.id == invitation.team_id).first()
    if team and team.creator_id:
        message = f"{current_user.first_name} has rejected your team invitation."
        await manager.send_to_user(str(team.creator_id), message)
        print(f"[WS] Notified employer {current_user.id} they Rejected the invitation")
    return invitation


# view all pending invitations for the current user
@router.get("/", response_model=list[TeamInvitationResponse])
async def get_my_pending_invitations(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invitations = get_pending_invitations(db, current_user.id)
    return invitations
