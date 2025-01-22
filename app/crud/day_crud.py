from sqlalchemy.orm import Session
from app.models.day_model import Day
from app.schemas.day_schema import DayCreate

def create_day(db: Session, day: DayCreate):
    # Check if a day with the same name exists
    db_day = db.query(Day).filter(Day.name == day.name).first()
    if db_day:
        return None, "A day with this name already exists"

    # Create the new day
    new_day = Day(name=day.name)
    db.add(new_day)
    db.commit()
    db.refresh(new_day)
    return new_day, None

def get_day(db: Session, day_id: int):
    return db.query(Day).filter(Day.id == day_id).first()
