from fastapi import FastAPI
from app.db_config import Base, engine
from app.routes.user_route import router as user_router
from app.routes.team_route import router as team_router

app = FastAPI()

# Include routers
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(team_router, prefix="/teams", tags=["Teams"])

# Create all database tables at once
Base.metadata.create_all(bind=engine)
