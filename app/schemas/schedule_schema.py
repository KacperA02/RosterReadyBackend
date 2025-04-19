from pydantic import BaseModel
from typing import List, Optional, Any


class ShiftAssignment(BaseModel):
    user_id: int
    shift_id: int
    day_id: int
    slot: int


class ShiftAssignmentResponse(BaseModel):
    total_solutions: int
    assignments: List[List[ShiftAssignment]]


class ShiftAssignmentRegenerationResponse(BaseModel):
    total_solutions: int
    assignments: List[ShiftAssignment] = []
    changed_count: int
    fallback_count: int
    skipped_count: Optional[int] = 0
    skipped_assignments: Optional[List[Any]] = []
    failure_reasons: Optional[List[str]] = []
    message: Optional[str] = None
