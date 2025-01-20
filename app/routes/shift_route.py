from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.db_config import get_db

router = APIRouter()

# creating a new shift
@router.post("/shifts/", response_model=schemas.Shift)
async def create_new_shift(shift: schemas.ShiftCreate, db: Session = Depends(get_db)):
    new_shift, error = crud.create_shift(db=db, shift=shift)
    if error:
        raise HTTPException(status_code=400, detail=error)  
    return new_shift 

# getting all shifts from a singular team
@router.get("/shifts/{team_id}", response_model=List[schemas.Shift])
async def get_shifts(team_id: int, db: Session = Depends(get_db)):
    shifts, error = crud.get_shifts_by_team(db=db, team_id=team_id)
    if error:
        raise HTTPException(status_code=404, detail=error)  
    return shifts  