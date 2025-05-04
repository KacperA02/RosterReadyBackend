from fastapi import FastAPI
# Using to get the current year dynamically
from datetime import datetime, timezone
# Manages the start up and shutdown event, APIs version of onStartUp
from contextlib import asynccontextmanager
from app.dependencies.db_config import Base, engine, SessionLocal
from app.routes.user_route import router as user_router
from app.routes.team_route import router as team_router
from app.routes.shift_route import router as shift_router
from app.routes.auth_route import router as auth_router
from app.routes.day_route import router as day_router
from app.routes.expertise_route import router as expertise_router
from app.routes.user_availability_route import router as user_availability_router
from app.routes.assignment_route import router as assignment_router
from fastapi.middleware.cors import CORSMiddleware
from app.crud.day_crud import create_all_days 
from app.crud.week_crud import create_all_weeks
from app.crud.role_crud import seed_roles
from app.routes.scheduling_route import router as scheduling_router
from app.routes.team_invitation_route import router as team_invitation_router
from app.routes.week_route import router as week_router
from app.routes.solution_route import router as solution_router
from app.routes.websocket_route import router as websocket_router
# lifespan runs on start up and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    # creating all days and weeks on startup.
    try:
        current_year = datetime.now(timezone.utc).year
        create_all_days(db) 
        create_all_weeks(db, current_year)
        seed_roles(db)
        yield  
    finally:
        db.close()

app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rosterready1.vercel.app/", "http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)
# Include routers
app.include_router(user_router, prefix="/users", tags=["Users"], strict_slashes=False)
app.include_router(team_router, prefix="/teams", tags=["Teams"], strict_slashes=False)
app.include_router(shift_router, prefix="/shifts", tags=["Shifts"], strict_slashes=False) 
app.include_router(day_router, prefix="/days", tags=["Days"], strict_slashes=False)
app.include_router(scheduling_router, prefix="/schedule", tags=["Schedules"], strict_slashes=False)
app.include_router(assignment_router, prefix="/assignments", tags=["Assignments"], strict_slashes=False)
app.include_router(solution_router, prefix="/solutions", tags=["Solutions"], strict_slashes=False)
app.include_router(week_router, prefix="/weeks", tags=["Weeks"], strict_slashes=False)
app.include_router(user_availability_router, prefix="/available", tags=["User-available"], strict_slashes=False)
app.include_router(auth_router, prefix="/auth", tags=["Auth"], strict_slashes=False)
app.include_router(team_invitation_router, prefix="/invitation", tags=["invitations"], strict_slashes=False)
app.include_router(expertise_router, prefix="/expertise", tags=["expertises"], strict_slashes=False)
# Create all database tables at once
app.include_router(websocket_router, tags=["WebSocket"], strict_slashes=False)
Base.metadata.create_all(bind=engine)

