from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import UserAvailability
from app.schemas.user_availability_schema import UserAvailabilityCreate
from app.models import User  

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
