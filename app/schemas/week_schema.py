from pydantic import BaseModel
from datetime import date

class WeekSchema(BaseModel):
    id: int
    week_number: int
    start_date: date
    end_date: date

    class Config:
        from_attributes = True  
        
class WeekBase(BaseModel):
    week_number: int
    start_date: date
    end_date: date
    
class WeekCreate(WeekBase):
    pass
class WeekResponse(WeekBase):
    id: int
    
    class Config:
        from_attributes = True  
