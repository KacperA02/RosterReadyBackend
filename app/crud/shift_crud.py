from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.shift_model import Shift
from app.models.team_model import Team
from app.schemas.shift_schema import ShiftCreate, ShiftDaysCreate, ShiftResponse,DayResponse
from app.models.day_model import Day
from sqlalchemy.exc import IntegrityError
from app.association import day_shift_team
from app.models.user_model import User
from app.schemas.user_schema import UserResponse
from sqlalchemy import delete
# create a shift
def create_shift(db: Session, shift: ShiftCreate, current_user: UserResponse):
    # checks if the user is part of a team
    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found."
        )

    # Ensures the user is the creator of the team
    if team.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team creator can create shifts."
        )
    
    # Create the shift
    db_shift = Shift(
        name=shift.name,
        time_start=shift.time_start,
        time_end=shift.time_end,
        # task is optional
        task=shift.task if shift.task else None,
        # no_of_users is optional but defaults to 1
        no_of_users=shift.no_of_users if shift.no_of_users else 1,
        # team_id is the team the shift is associated with
        team_id=current_user.team_id  
    )

    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    # I added none because the function is supposed to return a tuple
    return db_shift, None

# edit a shift
def edit_shift(db: Session, shift_id: int, shift_data: ShiftCreate, current_user: UserResponse):
    # Fetchs the shift
    db_shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not db_shift:
        raise HTTPException(status_code=404, detail="Shift not found.")

    # Checks if the team exists
    team = db.query(Team).filter(Team.id == db_shift.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")

    # ensures the user is the creator of the team
    if team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to edit this shift.")

    # Update the shift
    db_shift.name = shift_data.name
    db_shift.time_start = shift_data.time_start
    db_shift.time_end = shift_data.time_end
    db_shift.task = shift_data.task
    db_shift.no_of_users = shift_data.no_of_users

    db.commit()
    db.refresh(db_shift)

    return db_shift
# view a single shift
def view_shift(db: Session, shift_id: int, current_user: UserResponse):
    # checks if the shift exists
    db_shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not db_shift:
        raise HTTPException(status_code=404, detail="Shift not found.")

    # Ensure the user is part of the team
    if db_shift.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="You are not part of this team.")

    return db_shift

# view all shifts related to the team
def view_shifts_by_team(db: Session, current_user: UserResponse):
    # Fetch all shifts related to the user's team
    db_shifts = db.query(Shift).filter(Shift.team_id == current_user.team_id).all()

    if not db_shifts:
        raise HTTPException(status_code=404, detail="No shifts found for this team.")
    
    shifts_with_days = []

    # Loop through each shift and get associated days
    for shift in db_shifts:
        # Fetch associated days using the day_shift_team association table
        associated_days = db.query(Day).join(
            day_shift_team, day_shift_team.c.day_id == Day.id
        ).filter(day_shift_team.c.shift_id == shift.id).all()

        # Convert days to DayResponse model
        days_response = [DayResponse.model_validate(day) for day in associated_days]


        # Convert shift to ShiftResponse model, including the associated days
        shift_response = ShiftResponse(
            id=shift.id,
            name=shift.name,
            time_start=shift.time_start,
            time_end=shift.time_end,
            no_of_users=shift.no_of_users,
            team_id=shift.team_id,
            task=shift.task,
            days=days_response
        )

        # Append the shift with its days to the result list
        shifts_with_days.append(shift_response)
    
    return shifts_with_days

# attach days to a shift
def attach_days_to_shift(db: Session, shift_id: int, shift_days: ShiftDaysCreate, current_user: UserResponse):
    # gets the shift
    db_shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not db_shift:
        raise HTTPException(status_code=404, detail="Shift not found.")

    # condition to check if the shift belongs to the user's team
    if db_shift.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="This shift does not belong to your team.")

    # Ensures the user is the creator of the team can attach days to shifts
    team = db.query(Team).filter(Team.id == db_shift.team_id).first()
    if team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the team creator (Employer) can attach days to shifts.")

    # Fetch the days from the database using the provided day_ids
    days = db.query(Day).filter(Day.id.in_(shift_days.day_ids)).all()

    # Check if all provided day_ids exist
    if len(days) != len(shift_days.day_ids):
        raise HTTPException(status_code=404, detail="One or more days not found.")

    # Create associations between the shift and the days
    # try block to catch any errors
    try:
        # loop through the days and add them to the day_shift_team table
        for day in days:
            # insert the day_shift_team data
            db.execute(day_shift_team.insert().values(
                day_id=day.id,
                shift_id=db_shift.id,
                team_id=db_shift.team_id 
            ))
        # commits each transaction
        db.commit()  

    # catch any integrity errors
    except IntegrityError:
        db.rollback() 
        raise HTTPException(status_code=400, detail="Failed to attach days to the shift. Integrity error.")

    return {"detail": "Days successfully attached to the shift."}

# remove days from a shift
def remove_days_from_shift(db: Session, shift_id: int, shift_days: ShiftDaysCreate, current_user: UserResponse):
    # fetch the shift
    db_shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not db_shift:
        raise HTTPException(status_code=404, detail="Shift not found.")
    
    # Condition to check if the shift belongs to the user's team
    if db_shift.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="This shift does not belong to your team.")
    
    # condition to check if the user is the creator of the team
    team = db.query(Team).filter(Team.id == db_shift.team_id).first()
    if team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the team creator (Employer) can remove days from shifts.")

    # Fetch the days from the database using the provided day_ids
    days = db.query(Day).filter(Day.id.in_(shift_days.day_ids)).all()

    # condition to check if all provided day_ids exist
    if len(days) != len(shift_days.day_ids):
        raise HTTPException(status_code=404, detail="One or more days not found.")
    
    # Remove the days from the shift
    # try block to catch any errors
    try:
        # loop through the days and delete them from the day_shift_team table
        for day in days:
            # delete the day_shift_team data
            db.execute(
                day_shift_team.delete().where(
                    day_shift_team.c.day_id == day.id,
                    day_shift_team.c.shift_id == db_shift.id,
                    day_shift_team.c.team_id == db_shift.team_id  
                )
            )
        
        db.commit()  
    # catch any integrity errors
    except IntegrityError:
        db.rollback()  
        raise HTTPException(status_code=400, detail="Failed to remove days from the shift. Integrity error.")
    
    return {"detail": "Days successfully removed from the shift."}

def delete_shift(db: Session, shift_id: int, current_user: UserResponse):
    # Fetch the shift
    db_shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not db_shift:
        raise HTTPException(status_code=404, detail="Shift not found.")

    # Confirm the shift belongs to the user's team
    if db_shift.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="This shift does not belong to your team.")

    # Ensure the user is the team creator
    team = db.query(Team).filter(Team.id == db_shift.team_id).first()
    if team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the team creator (Employer) can delete shifts.")

    try:
        # Explicitly delete from day_shift_team where this shift is referenced
        db.execute(
            day_shift_team.delete().where(day_shift_team.c.shift_id == db_shift.id)
        )

        # Assignments are automatically handled by `cascade="all, delete-orphan"`

        # Delete the shift
        db.delete(db_shift)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while deleting the shift.")

    return {"detail": "Shift and related data successfully deleted."}