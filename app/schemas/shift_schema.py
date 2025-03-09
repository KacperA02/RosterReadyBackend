from pydantic import BaseModel, Field
from typing import Optional, Annotated
from datetime import time
from typing import List

# Schema for creating a shift
class ShiftCreate(BaseModel):
    name: str
    time_start: time
    time_end: time
    task: Optional[str] = None  
    # no_of_users is optional but defaults to 1 and must be greater than or equal to 1
    no_of_users: Annotated[int, Field(ge=1, default=1)]  

# Schema for viewing a shift
class ShiftResponse(BaseModel):
    id: int
    name: str
    time_start: time
    time_end: time
    task: Optional[str] = None
    no_of_users: int
    team_id: int 

    class Config:
        from_attributes = True
        


class ShiftDaysCreate(BaseModel):
    day_ids: List[int] 

    class Config:
        from_attributes = True
