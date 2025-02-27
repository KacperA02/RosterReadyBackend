from sqlalchemy.orm import Session
from app.models.week_model import Week
# working with dates and times and timedelta is for date arithmetic
from datetime import datetime, timedelta
# This function calculates the exact dates of the chosen week for the current year
def get_week_start_end(year: int, week: int):
    # getting the first day of the year by inputing the year, month and date 
    first_day = datetime(year, 1, 1)  
    # need to calculate the first monday
    #(7 - first_day.weekday()) will calculate the number of days to add to get to the first Monday of the year 
    first_monday = first_day + timedelta(days=(7 - first_day.weekday())) 
    # need to calculate the first first date based on the first monday
    # Add the number of weeks (week - 1) to the first Monday to get the start date of the chosen date
    start_date = first_monday + timedelta(weeks=week - 1)
    # Calculating the end date by adding 6 to the start_date
    end_date = start_date + timedelta(days=6)
    # return both prepared dates in date formats
    return start_date.date(), end_date.date()

# This populates the weeks table ranging from 1 - 52
def create_all_weeks(db: Session, year: int):
    # checking how many weeks already exists
    existing_weeks = db.query(Week).count()
    # condition to check if all weeks are created already, to prevent duplicates
    if existing_weeks >= 52:
        print("All weeks already exist. Skipping insertion.")
        return  
    #loop through the range of weeks
    for week_num in range(1, 53):  
        # calculating the start and end date for the current week number
        start_date, end_date = get_week_start_end(year, week_num)
        # if the week already exists skip
        if not db.query(Week).filter(Week.week_number == week_num).first():
            # If the week doesnt exist, it creates a new week object storing week number, start and end dates
            new_week = Week(week_number=week_num, start_date=start_date, end_date=end_date)
            # adding to the db
            db.add(new_week)
            # printing for results
            print(f"Added Week {week_num}: {start_date} - {end_date} to the database.")
   
    db.commit()
