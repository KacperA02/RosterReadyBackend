# schema for users
from pydantic import BaseModel, EmailStr
from typing import List, Optional

class team(BaseModel):
    id:int
    name:str
    # needed to add this to allow pydantic to read the SQL objects. This is as pydantic generally expects json data.
    class Config:
        orm_mode = True
    
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password:str

class UserResponse(UserBase):
    id:int
    teams: List[team] = []

    class Config:
        orm_mode = True
