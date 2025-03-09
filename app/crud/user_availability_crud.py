from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import UserAvailability
from app.schemas.user_availability_schema import UserAvailabilityCreate
from app.models import User, Team  

# creates a list of request availabilities
def create_user_availability(db: Session, availability_data: UserAvailabilityCreate, current_user: User):
    created_availabilities = []
    user_id = current_user.id  
    team_id = current_user.team_id  
    # loop to create availability for each day
    for day_id in availability_data.day_ids:
        existing_availability = (
            db.query(UserAvailability)
            .filter(
                UserAvailability.user_id == user_id,
                UserAvailability.team_id == team_id,
                UserAvailability.day_id == day_id,
            )
            # .first() returns the first result of the query
            .first()
        )
        # If the availability already exists, skip it
        if existing_availability:
            continue  

        # availability is created
        db_availability = UserAvailability(
            user_id=user_id,
            team_id=team_id,
            day_id=day_id,
            reason=availability_data.reason,
            approved=availability_data.approved,
        )
        db.add(db_availability)
        # append the availability to the list
        created_availabilities.append(db_availability)

    db.commit()
    # return a list of dictionaries
    return [{"user_id": i.user_id, "team_id": i.team_id, "day_id": i.day_id, "reason": i.reason, "approved": i.approved} for i in created_availabilities]

# deletes a specific availability
def delete_user_availability(db: Session, availability_id: int, current_user: User):
    # Query for the availability entry
    availability_entry = db.query(UserAvailability).filter(UserAvailability.id == availability_id).first()
    
    # If not found, raise an exception
    if not availability_entry:
        raise HTTPException(status_code=404, detail="Availability not found")
    # gets the team of the availability
    team = db.query(Team).filter(Team.id == availability_entry.team_id).first()
    # Check if the user is the creator of the team or the user who created the availability
    if availability_entry.user_id != current_user.id and team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this availability")
    
    # Delete the availability
    db.delete(availability_entry)
    db.commit()
    
    return {"message": "Availability deleted successfully"}

# gets the availabilities of the team
def get_team_availabilities(db: Session, current_user: User):
    # gets the team of the current user
    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    
    # if the team does not exist or the user is not the creator of the team, raise an exception
    if team is None or team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view team availabilities")
    
    # Return all availabilities for the team
    return db.query(UserAvailability).filter(UserAvailability.team_id == current_user.team_id).all()

# gets the availabilities of the user
def get_user_availabilities(db: Session, current_user: User):
    # Ensure the user_id matches the current user id
    return db.query(UserAvailability).filter(UserAvailability.user_id == current_user.id).all()

# toggles the approval status of the availability
def toggle_approval(db: Session, availability_id: int, current_user: User):
    # Query for the availability entry
    availability_entry = db.query(UserAvailability).filter(UserAvailability.id == availability_id).first()
    
    # If not found, raise an exception
    if not availability_entry:
        raise HTTPException(status_code=404, detail="Availability not found")
    
    # Query for the team of the availability
    team = db.query(Team).filter(Team.id == availability_entry.team_id).first()

    # check if the user is the creator of the team
    if team is None or team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to toggle approval for this team's availability")

    # toggles the approval status
    availability_entry.approved = not availability_entry.approved
    db.commit()
    db.refresh(availability_entry)
    
    return {"message": "Approval status updated", "approved": availability_entry.approved}