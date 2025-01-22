from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.crud.shift_crud import create_shift
from app.schemas.shift_schema import ShiftCreate, ShiftResponse
from app.db_config import get_db

router = APIRouter()

@router.post("/", response_model=ShiftResponse)
async def create_shift_route(shift: ShiftCreate, db: Session = Depends(get_db)):
    db_shift, error = create_shift(db, shift)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return db_shift
