from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.dependencies.db_config import get_db
from app.schemas.week_schema import *
from app.crud.week_crud import * 


router = APIRouter()

@router.get("/", response_model=List[WeekSchema])
def fetch_all_weeks(db: Session = Depends(get_db)):
    return get_all_weeks(db)

@router.get("/search/", response_model=Optional[WeekResponse])
def fetch_week_by_start_date(start_date: date, db: Session = Depends(get_db)):
    week = get_week_by_start_date(db, start_date)
    if not week:
        raise HTTPException(status_code=404, detail="No week found for this date")
    return week
