from sqlalchemy.orm import Session
from sqlalchemy import insert, delete
from fastapi import HTTPException, status
from app.models.expertise_model import Expertise
from app.models.team_model import Team
from app.models.shift_model import Shift
from app.schemas.expertise_schema import ExpertiseCreate, ShiftAttached, UserAttached
from app.models.user_model import User
from app.schemas.user_schema import UserResponse
from app.association import user_expertise, shift_expertise

# creating an expertise for a team
def create_expertise(db: Session, expertise: ExpertiseCreate, current_user: UserResponse):
    # Condition to check if the user is part of a team
    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found."
        )
    
    # Condition to check if the user is the creator of the team
    if team.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team creator can create expertise."
        )
    
    # create the expertise
    db_expertise = Expertise(
        name=expertise.name,
        team_id=current_user.team_id
    )
    
    db.add(db_expertise)
    db.commit()
    db.refresh(db_expertise)
    
    return db_expertise

# Edit function for expertise
def edit_expertise(db: Session, expertise_id: int, expertise_data: ExpertiseCreate, current_user: UserResponse):
    # Check if the expertise exists
    db_expertise = db.query(Expertise).filter(Expertise.id == expertise_id).first()
    if not db_expertise:
        raise HTTPException(status_code=404, detail="Expertise not found.")
    
    # Check if the team exists
    team = db.query(Team).filter(Team.id == db_expertise.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    
    # Ensure the user is the creator of the team
    if team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to edit this expertise.")
    
    # Update the expertise
    db_expertise.name = expertise_data.name
    
    db.commit()
    db.refresh(db_expertise)
    
    return db_expertise

# View a single expertise
def view_expertise(db: Session, expertise_id: int, current_user: UserResponse):
    # Check if the expertise exists
    db_expertise = db.query(Expertise).filter(Expertise.id == expertise_id).first()
    if not db_expertise:
        raise HTTPException(status_code=404, detail="Expertise not found.")
    
    # Ensure the user is part of the team
    if db_expertise.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="You are not part of this team.")
    
    return db_expertise

def delete_expertise(db: Session, expertise_id: int, current_user: UserResponse):
    # Condition to check if the user is part of a team
    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found."
        )
    
    # Condition to check if the user is the creator of the team
    if team.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team creator can delete expertise."
        )
    
    # Check if the expertise exists
    db_expertise = db.query(Expertise).filter(Expertise.id == expertise_id, Expertise.team_id == current_user.team_id).first()
    if not db_expertise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expertise not found or not associated with your team."
        )
    # deleting the expertise from the association tables
    db.execute(
        delete(user_expertise).where(user_expertise.c.expertise_id == expertise_id)
    )
    db.execute(
        delete(shift_expertise).where(shift_expertise.c.expertise_id == expertise_id)
    )
    
    
    db.commit()   
    
    # Delete the expertise
    db.delete(db_expertise)
    db.commit()
    
    return {"detail": "Expertise deleted successfully."}

# get all expertise for a team
def view_all_expertise_of_team(db: Session, current_user: UserResponse):
    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    
    if team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the employer (team creator) can view expertise for the team.")
    
    expertise_list = db.query(Expertise).filter(Expertise.team_id == current_user.team_id).all()
    
    if not expertise_list:
        return []  # Return empty array if no expertise is found
    
    response = []
    for expertise in expertise_list:
        # Joining the many to many of user expertise to match witht the expertise ids
        users = db.query(User).join(user_expertise).filter(user_expertise.c.expertise_id == expertise.id).all()
        
        # Joining the many to many of shift expertise to match witht the expertise ids
        shifts = db.query(Shift).join(Shift.expertises).filter(Expertise.id == expertise.id).all()

        response.append({
            "id": expertise.id,
            "name": expertise.name,
            "team_id": expertise.team_id,
            "users": [{"id": user.id, "first_name": user.first_name, "last_name": user.last_name} for user in users],
            "shifts": [{"id": shift.id, "name": shift.name} for shift in shifts] 
        })

    return response


# Assign expertise to a user
def add_expertise_to_user(db: Session, expertise_id: int, user_id: int, current_user: UserResponse):
    # Check if the team exists
    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    
    # Ensure the user is the creator of the team
    if team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to attach this expertise.")
    db_expertise = db.query(Expertise).filter(Expertise.id == expertise_id).first()
    db_user = db.query(User).filter(User.id == user_id, User.team_id == current_user.team_id).first()
    # Check if the expertise and user exist
    if not db_expertise:
        raise HTTPException(status_code=404, detail="Expertise not found.")
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found or not in your team.")
    # inserting the expertise and user into the association table
    db.execute(insert(user_expertise).values(user_id=user_id, expertise_id=expertise_id))
    db.commit()
    
    return UserAttached(
        user_id=db_user.id,       
        expertise_id=db_expertise.id  
    )

# Assign expertise to a shift
def add_expertise_to_shift(db: Session, expertise_id: int, shift_id: int, current_user: UserResponse):
    # Check if the team exists
    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    
    # Ensure the user is the creator of the team
    if team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to attach this expertise.")
    db_expertise = db.query(Expertise).filter(Expertise.id == expertise_id).first()
    db_shift = db.query(Shift).filter(Shift.id == shift_id, Shift.team_id == current_user.team_id).first()
    # Check if the expertise and shift exist
    if not db_expertise:
        raise HTTPException(status_code=404, detail="Expertise not found.")
    if not db_shift:
        raise HTTPException(status_code=404, detail="Shift not found or not in your team.")
    # inserting the expertise and shift into the association table
    db.execute(insert(shift_expertise).values(shift_id=shift_id, expertise_id=expertise_id))
    db.commit()
    
    return ShiftAttached(
        shift_id=db_shift.id,       
        expertise_id=db_expertise.id  
    )
    
def remove_expertise_from_user(db: Session, expertise_id: int, user_id: int, current_user: UserResponse):
    # Check if the team exists
    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    
    # Ensure the user is the creator of the team
    if team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to remove this expertise.")
    
    db_expertise = db.query(Expertise).filter(Expertise.id == expertise_id).first()
    db_user = db.query(User).filter(User.id == user_id, User.team_id == current_user.team_id).first()
    
    # Check if the expertise and user exist
    if not db_expertise:
        raise HTTPException(status_code=404, detail="Expertise not found.")
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found or not in your team.")
    
    existing_association = db.query(user_expertise).filter(
        user_expertise.c.user_id == user_id,
        user_expertise.c.expertise_id == expertise_id
    ).first()
    
    # If no association exists, raise an error
    if not existing_association:
        raise HTTPException(status_code=404, detail="This expertise is not assigned to the user.")
    
    # Deleting the expertise and user from the association table
    result = db.execute(
        delete(user_expertise)
        .where(user_expertise.c.user_id == user_id)
        .where(user_expertise.c.expertise_id == expertise_id)
    )
    db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="No expertise found to remove for the given user.")
    
def remove_expertise_from_shift(db: Session, expertise_id: int, shift_id: int, current_user: UserResponse):
    # Check if the team exists
    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    
    # Ensure the user is the creator of the team
    if team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to remove this expertise.")
    
    db_expertise = db.query(Expertise).filter(Expertise.id == expertise_id).first()
    db_shift = db.query(Shift).filter(Shift.id == shift_id, Shift.team_id == current_user.team_id).first()
    
    # Check if the expertise and shift exist
    if not db_expertise:
        raise HTTPException(status_code=404, detail="Expertise not found.")
    if not db_shift:
        raise HTTPException(status_code=404, detail="Shift not found or not in your team.")
    
    existing_association = db.query(shift_expertise).filter(
        shift_expertise.c.shift_id == shift_id,
        shift_expertise.c.expertise_id == expertise_id
    ).first()
    
    # If no association exists, raise an error
    if not existing_association:
        raise HTTPException(status_code=404, detail="This expertise is not assigned to the shift.")
        
    # Deleting the expertise and shift from the association table
    result = db.execute(
        delete(shift_expertise)
        .where(shift_expertise.c.shift_id == shift_id)
        .where(shift_expertise.c.expertise_id == expertise_id)
    )
    db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="No expertise found to remove for the given shift.")