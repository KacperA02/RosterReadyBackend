from sqlalchemy.orm import Session
from app.models.shift_model import Shift
from app.schemas.shift_schema import ShiftCreate
from app.models.team_model import Team
from app.models.day_model import Day
from app.crud.user_constraints_crud import create_user_constraints
from app.association import day_shift_team

def create_shift(db: Session, shift: ShiftCreate):
    # Fetch the team based on the provided team_id
    team = db.query(Team).filter(Team.id == shift.team_id).first()
    if not team:
        return None, "Team with the given ID does not exist"

    # Create the shift object
    db_shift = Shift(
        name=shift.name, 
        time_start=shift.time_start, 
        time_end=shift.time_end, 
        team_id=shift.team_id
    )

   
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)

    # checking all day ids
    days = db.query(Day).filter(Day.id.in_(shift.days)).all()
    if len(days) != len(shift.days):
        return None, "One or more of the day IDs are invalid"

    # inserting the information to many to many table
    for day in days:
        db.execute(day_shift_team.insert().values(
            day_id=day.id,
            shift_id=db_shift.id,
            team_id=shift.team_id
        ))
    db.commit()
    # creates all rows with the for each shift and user
    create_user_constraints(db, db_shift.id, shift.team_id, shift.days)
    return db_shift, None
