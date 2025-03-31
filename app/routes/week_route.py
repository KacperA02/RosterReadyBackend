from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db_config import get_db
from app.schemas.week_schema import WeekSchema
from app.crud.week_crud import get_all_weeks  # Import your function

router = APIRouter()

@router.get("/", response_model=List[WeekSchema])
def fetch_all_weeks(db: Session = Depends(get_db)):
    return get_all_weeks(db)
