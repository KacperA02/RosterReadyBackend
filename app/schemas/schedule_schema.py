from pydantic import BaseModel
from typing import List


class ShiftAssignment(BaseModel):
    user_id: int
    shift_id: int
    day_id: int
    slot: int  

class ShiftAssignmentResponse(BaseModel):
    total_solutions: int
    assignments: List[List[ShiftAssignment]]  
    