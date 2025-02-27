from fastapi import FastAPI
# Using to get the current year dynamically
from datetime import datetime, timezone
# Manages the start up and shutdown event, APIs version of onStartUp
from contextlib import asynccontextmanager
from app.db_config import Base, engine, SessionLocal
from app.routes.user_route import router as user_router
from app.routes.team_route import router as team_router
from app.routes.shift_route import router as shift_router
from app.routes.day_route import router as day_router
from app.routes.user_constraint_route import router as userCon_router
from fastapi.middleware.cors import CORSMiddleware
from app.crud.day_crud import create_all_days 
from app.crud.week_crud import create_all_weeks

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)
# Include routers
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(team_router, prefix="/teams", tags=["Teams"])
app.include_router(shift_router, prefix="/shifts", tags=["Shifts"]) 
app.include_router(day_router, prefix="/days", tags=["Days"]) 
app.include_router(userCon_router, prefix="/user-constraints", tags=["User Constraints"])

# Create all database tables at once
Base.metadata.create_all(bind=engine)

# lifespan runs on start up and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    # creating all days and weeks on startup.
    try:
        current_year = datetime.now(timezone.utc).year
        create_all_days(db) 
        create_all_weeks(db, current_year) 
        yield  
    finally:
        db.close()

app = FastAPI(lifespan=lifespan)