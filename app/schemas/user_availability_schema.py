from typing import List, Optional
from pydantic import BaseModel

class UserAvailabilityCreate(BaseModel):
    day_ids: List[int]  # Only days now
    reason: Optional[str] = None
    approved: bool = False

    class Config:
        from_attributes = True
        
class User(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True

class Day(BaseModel):
    id: int
    name: str

    class Config:
       from_attributes = True

class Team(BaseModel):
    id: int
    name: str

    class Config:
       from_attributes = True

class UserAvailabilityResponse(BaseModel):
    id: int
    approved: bool
    reason: Optional[str]
    user: User
    day: Day
    team: Team

    class Config:
       from_attributes = True
        
