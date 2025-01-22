from pydantic import BaseModel
from datetime import time
from typing import List

# Base model for validation
class ShiftBase(BaseModel):
    name: str
    time_start: time
    time_end: time

# The team the shift belongs to
class ShiftCreate(ShiftBase):
    team_id: int
    days: List[int]  

# The response from the data
class ShiftResponse(ShiftBase):
    id: int
    team_id: int 

    class Config:
        from_attributes = True
