from sqlalchemy.orm import Session, joinedload
from fastapi import Depends, HTTPException, status
from app.models.team_invitation_model import TeamInvitation
from app.models.user_model import User
from app.models.team_model import Team
from app.enums import InvitationStatus
from app.dependencies.auth import get_current_user
from app.schemas.user_schema import UserResponse
from app.models.role_model import Role

def invite_user_to_team(
    db: Session, 
    user_id: int, 
    current_user: UserResponse = Depends(get_current_user)
):
    # Ensure the inviter has the "Employer" role
    if "Employer" not in [role.name for role in current_user.roles]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only employers can invite users."
        )
    
    # Ensure the inviter is part of a team
    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You must be part of a team to invite users."
        )

    # Check if the invited user already exists
    invited_user = db.query(User).filter(User.id == user_id).first()
    if not invited_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found."
        )

    # Check if the user is already in a team
    if invited_user.team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User is already part of a team."
        )

    # Check if an invite already exists
    existing_invite = db.query(TeamInvitation).filter(
        TeamInvitation.user_id == user_id, TeamInvitation.team_id == team.id
    ).first()
    if existing_invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User is already invited or part of the team."
        )

    # Create and store the invitation
    invitation = TeamInvitation(user_id=user_id, team_id=team.id)
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    
    return invitation


def accept_invitation(db: Session, user_id: int, invitation_id: int):
    invitation = db.query(TeamInvitation).filter(TeamInvitation.id == invitation_id, TeamInvitation.user_id == user_id).first()
    if not invitation:
        return None, "Invitation not found or user not authorized."
    
    # Update the invitation status to accepted
    invitation.status = InvitationStatus.ACCEPTED
    db.commit()

    # Add the user to the team now that they’ve accepted the invitation
    team = db.query(Team).filter(Team.id == invitation.team_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    
    if team and user:
        # Adding the user to the team
        team.users.append(user)
        
        # Get the Employee role (if it exists)
        employee_role = db.query(Role).filter(Role.name == "Employee").first()
        if employee_role and employee_role not in user.roles:
            user.roles.append(employee_role)  

        db.commit()
    
    return invitation, None

def reject_invitation(db: Session, user_id: int, invitation_id: int):
    invitation = db.query(TeamInvitation).filter(TeamInvitation.id == invitation_id, TeamInvitation.user_id == user_id).first()
    if not invitation:
        return None, "Invitation not found or user not authorized."
    
    # Update the invitation status to rejected
    invitation.status = InvitationStatus.DECLINED
    db.commit()

    return invitation, None

def get_pending_invitations(db: Session, user_id: int):
    return db.query(TeamInvitation).options(
        joinedload(TeamInvitation.team)
    ).filter(
        TeamInvitation.user_id == user_id,
        TeamInvitation.status == InvitationStatus.PENDING
    ).all()


def get_pending_invitations_for_team(db: Session, team_id: int):
    return db.query(TeamInvitation).options(
        joinedload(TeamInvitation.user)
    ).filter(
        TeamInvitation.team_id == team_id,
        TeamInvitation.status == InvitationStatus.PENDING
    ).all()
