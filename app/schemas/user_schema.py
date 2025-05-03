from pydantic import BaseModel
from typing import List, Optional
from app.schemas.role_schema import RoleResponse

class UserCreate(BaseModel):
    first_name: str  
    last_name: str   
    email: str
    mobile_number: str
    password: str  

    class Config:
        from_attributes = True 
        
class UserEdit(BaseModel):
    first_name: str  
    last_name: str   
    email: str
    mobile_number: str

    class Config:
        from_attributes = True         

class UserResponse(BaseModel):
    id: int
    first_name: str  
    last_name: str   
    email: str
    mobile_number: str
    day_off_count: int 
    team_id: Optional[int] | None
    roles: List[RoleResponse] = []   

    class Config:
        from_attributes = True
