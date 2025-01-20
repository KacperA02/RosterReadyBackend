from sqlalchemy.orm import Session
from app.models.shift_model import Shift
from app.schemas.shift_schema import ShiftCreate
from app.models.team_model import Team  

def create_shift(db: Session, shift: ShiftCreate):
    team = db.query(Team).filter(Team.id == shift.team_id).first()
    if not team:
        return None, "Team with the given ID does not exist"

    db_shift = Shift(name=shift.name, time_start=shift.time_start, time_end=shift.time_end, team_id=shift.team_id)
    db.add(db_shift)  
    db.commit() 
    db.refresh(db_shift)  
    
    return db_shift, None 


def get_shifts_by_team(db: Session, team_id: int):
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        return None, "Team with the given ID does not exist"  
    
    shifts = db.query(Shift).filter(Shift.team_id == team_id).all()
    return shifts, None  
