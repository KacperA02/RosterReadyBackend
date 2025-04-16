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
        from_attributes = True
        
class TeamResponse(BaseModel):
    id: int
    name: str
    creator_id: int
    user_ids: List[UserI]
    
    employee_count: int
    shift_count: int
    expertise_count: int

    class Config:
        from_attributes = True

class UserInTeam(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    mobile_number: str

    class Config:
        from_attributes = True

class TeamUsersResponse(BaseModel):
    team_id: int
    users: List[UserInTeam]
    
