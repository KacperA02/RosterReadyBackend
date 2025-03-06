from pydantic import BaseModel
from typing import Optional


class ExpertiseCreate(BaseModel):
    name: str


class ExpertiseResponse(ExpertiseCreate):
    id: int
    team_id: int

    class Config:
        from_attributes = True
        
class UserAttached(BaseModel):
    user_id: int
    expertise_id: int

    class Config:
        from_attributes = True
        
class ShiftAttached(BaseModel):
    shift_id: int
    expertise_id: int

    class Config:
        from_attributes = True