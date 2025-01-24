from sqlalchemy.orm import Session
from app.models.user_constraint_model import UserConstraint
from app.models.user_model import User
from typing import Optional
from app.models.day_model import Day
from app.association import team_user  

# creating a constraint for each user and shift within the team
def create_user_constraints(db: Session, shift_id: int, team_id: int, days_for_shift: list):
    # Gets all the users which match the team id 
    team_users = db.query(User).join(team_user).filter(team_user.c.team_id == team_id).all()

    # Fetches every day the shift repeats
    days_for_shift = db.query(Day).filter(Day.id.in_(days_for_shift)).all()

    # Creating a possible constraint for each user shift and day
    for user in team_users:
        for day in days_for_shift:
            user_constraint = UserConstraint(
                user_id=user.id,
                team_id=team_id,
                shift_id=shift_id,
                day_id=day.id,
                # presetting the boolean fields
                is_available=True, 
                is_preferred=False  
            )
            db.add(user_constraint)

    # commiting the userconstraint to the db
    db.commit()
    
# getting a users availabilty or choosing a specific one depdning if the shift or day is filled
def get_user_constraints(db: Session, user_id: int, shift_id: Optional[int] = None, day_id: Optional[int] = None):
    query = db.query(UserConstraint).filter(UserConstraint.user_id == user_id)

    # condition to check if shift or day is null or not
    if shift_id is not None:
        query = query.filter(UserConstraint.shift_id == shift_id)

    if day_id is not None:
        query = query.filter(UserConstraint.day_id == day_id)
    # getting all filtered
    return query.all()

# Update a single users constraint
def update_user_constraint(db: Session, user_id: int, shift_id: int, day_id: int, new_availability: bool, new_preference: bool):
    # filters the matched query with the parameters and gets the first result
    user_constraint = db.query(UserConstraint).filter(
        UserConstraint.user_id == user_id,
        UserConstraint.shift_id == shift_id,
        UserConstraint.day_id == day_id
    ).first()
    # if one exists then commit any new changes
    if user_constraint:
        user_constraint.is_available = new_availability
        user_constraint.is_preferred = new_preference
        db.commit()
        return user_constraint
    # otherwise return none
    return None



