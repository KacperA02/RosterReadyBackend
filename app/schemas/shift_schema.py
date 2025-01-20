from pydantic import BaseModel
from datetime import time

# base model for valdidation
class ShiftBase(BaseModel):
    name: str
    time_start: time
    time_end: time
# the team the shift belongs to 
class ShiftCreate(ShiftBase):
    team_id: int  

# the response from the data
class Shift(ShiftBase):
    id: int
    team_id: int
    # Tells pydantic to accept creations or updates made from the sqlAlchemy model
    class Config:
        from_attributes = True 