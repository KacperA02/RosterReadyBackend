from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.shift_model import Shift
from app.models.team_model import Team
from app.schemas.shift_schema import ShiftCreate
from app.models.user_model import User
from app.schemas.user_schema import UserResponse

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
    # Fetches all shifts related to the team
    db_shifts = db.query(Shift).filter(Shift.team_id == current_user.team_id).all()
    # checks if there are any shifts
    if not db_shifts:
        raise HTTPException(status_code=404, detail="No shifts found for this team.")

    return db_shifts
