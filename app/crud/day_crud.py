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
# List of the days of the week hardcoded
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
# function to create all days on startup
def create_all_days(db: Session):
    # Checking how many days already exists
    existing_days = db.query(Day).count() 
    # Condition to check if 7 days already exist to stop anymore from being created
    if existing_days >= 7: 
        print("All days already exist. Skipping insertion.")
        return 
    # loop through each day from the days of week list 
    for day_name in DAYS_OF_WEEK:
        # if the day_name already exists it prints it exists to prevent duplicates
        existing_day = db.query(Day).filter(Day.name == day_name).first()
        if existing_day:
            print(f"Day '{day_name}' already exists.")
        # otherwise it creates a new day object with the current day name, then adds it to the database  
        else:
            new_day = Day(name=day_name)
            db.add(new_day)
            print(f"Added day '{day_name}' to the database.")
    db.commit()
