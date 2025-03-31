from pydantic import BaseModel
from typing import Optional, List

class UserSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    
class ShiftSchema(BaseModel):
    id: int
    name: str

class ExpertiseCreate(BaseModel):
    name: str


class ExpertiseResponse(ExpertiseCreate):
    id: int
    team_id: int
    users: List[UserSchema]
    shifts: List[ShiftSchema]

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