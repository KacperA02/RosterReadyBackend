from pydantic import BaseModel
from datetime import date

class WeekSchema(BaseModel):
    id: int
    week_number: int
    start_date: date
    end_date: date

    class Config:
        from_attributes = True  
