from fastapi import FastAPI
from app.db_config import Base, engine
from app.routes.user_route import router as user_router
from app.routes.team_route import router as team_router
from app.routes.shift_route import router as shift_router
from app.routes.day_route import router as day_router
from app.routes.user_constraint_route import router as userCon_router
from fastapi.middleware.cors import CORSMiddleware

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

