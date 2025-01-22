from pydantic import BaseModel
from typing import List, Optional

class TeamCreate(BaseModel):
    name: str
    creator_id: int
    user_ids: List[int] = []

class TeamResponse(BaseModel):
    id: int
    name: str
    creator_id: int
    user_ids: List[int] = []

    class Config:
        from_attributes = True
