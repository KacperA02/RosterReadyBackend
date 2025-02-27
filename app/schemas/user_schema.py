from pydantic import BaseModel

class UserCreate(BaseModel):
    first_name: str  
    last_name: str   
    email: str
    mobile_number: str
    password: str  

    class Config:
        from_attributes = True 

class UserResponse(BaseModel):
    id: int
    first_name: str  
    last_name: str   
    email: str
    mobile_number: str
    day_off_count: int 
    team_id: int | None  

    class Config:
        from_attributes = True
