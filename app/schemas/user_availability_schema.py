from typing import List, Optional
from pydantic import BaseModel

class UserAvailabilityCreate(BaseModel):
    day_ids: List[int]  # Only days now
    reason: Optional[str] = None
    approved: bool = False

    class Config:
        from_attributes = True
        
