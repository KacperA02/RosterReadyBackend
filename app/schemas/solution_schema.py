from pydantic import BaseModel
from app.enums import SolutionStatus  
from datetime import datetime
from app.schemas.week_schema import WeekSchema
class SolutionSchema(BaseModel):
    id: int
    team_id: int
    week_id: int
    status: SolutionStatus
    created_at: datetime

    class Config:
        from_attributes = True
        
class SolutionI(BaseModel):
    id: int
    team_id: int
    week: WeekSchema
    status: SolutionStatus
    created_at: datetime

    class Config:
        from_attributes = True
