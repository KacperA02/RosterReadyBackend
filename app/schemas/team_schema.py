from pydantic import BaseModel
from typing import List, Optional

class TeamCreate(BaseModel):
    name: str
    
class UserI(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str

    class Config:
        orm_mode = True
        
class TeamResponse(BaseModel):
    id: int
    name: str
    creator_id: int
    user_ids: List[UserI]

    class Config:
        from_attributes = True
