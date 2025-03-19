from pydantic import BaseModel
from app.enums import SolutionStatus  
import datetime

class SolutionSchema(BaseModel):
    id: int
    team_id: int
    week_id: int
    status: SolutionStatus.DRAFT
    created_at: datetime

    class Config:
        from_attributes = True
