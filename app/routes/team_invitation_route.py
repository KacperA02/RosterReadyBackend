# app/routes/team_invitations_routes.py
from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from app.crud.team_invitation_crud import *
from app.schemas.team_invitation_schema import *
from app.dependencies.db_config import get_db
from app.dependencies.auth import get_current_user
from app.schemas.user_schema import UserResponse
from app.services.websocket_manager import manager
from app.models.team_model import Team
from sqlalchemy import or_
from app.models.user_model import User
from app.dependencies.auth import require_role


router = APIRouter()
# inviting a specifc user to a team
@router.post("/invite", response_model=TeamInvitationResponse)
async def invite_user(
    identifier: str = Body(..., embed=True),  # email or mobile_number
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_role(["Employer"]))
):
    # Look up user by email or mobile number
    invited_user = db.query(User).filter(
        or_(User.email == identifier, User.mobile_number == identifier)
    ).first()

    if not invited_user:
        raise HTTPException(
            status_code=404, 
            detail="User not found with that email or mobile number."
        )

    invitation = invite_user_to_team(db, invited_user.id, current_user)

    # Optional: send WebSocket notification
    await manager.send_to_user(
        str(invited_user.id), 
        f"{current_user.first_name} has invited you to join their team."
    )
    print(f"[WS] Invitation sent to user {invited_user.id}")

    return invitation

@router.delete("/cancel/{invitation_id}", status_code=200)
async def cancel_request_route(
    invitation_id: int, 
    current_user: UserResponse = Depends(require_role(["Employer"])), 
    db: Session = Depends(get_db)
):
    return cancel_invitation(db, invitation_id, current_user)
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
@router.get("/", response_model=list[UserPendingInvitationResponse])
async def get_my_pending_invitations(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_pending_invitations(db, current_user.id)

@router.get("/team", response_model=list[TeamPendingInvitationResponse])
async def get_pending_invitations_for_team_route(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.team_id:
        raise HTTPException(status_code=404, detail="User is not part of any team.")
    
    invitations = get_pending_invitations_for_team(db, current_user.team_id)

    if not invitations:
        raise HTTPException(status_code=404, detail="No pending invitations for this team.")

    return invitations