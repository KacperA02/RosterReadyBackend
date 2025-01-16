# Schema for team 
from pydantic import BaseModel
from typing import Optional

class TeamBase(BaseModel):
    name: str

class TeamResponse(TeamBase):
    id: int
    employer_id: int

    class config:
        orm_mode = True