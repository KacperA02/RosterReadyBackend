from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.day_schema import DayCreate, DayResponse
from app.crud.day_crud import get_day,create_day
from app.dependencies.db_config import get_db

router = APIRouter()

# creating a new shift
@router.post("/", response_model=DayResponse)
async def create_new_day(day: DayCreate, db: Session = Depends(get_db)):
    new_day, error = create_day(db=db, day=day)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return new_day

# getti
@router.get("/{day_id}", response_model=DayResponse)
async def get_day_route(day_id: int, db: Session = Depends(get_db)):
    day = await get_day(db, day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")
    return day 