from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v2.routes.auth import router as auth_router
from app.api.v2.routes.memberships import router as membership_router
from app.api.v2.routes.skills import router as skill_router
from app.api.v2.routes.shifts import router as shift_router
from app.api.v2.routes.time_requests import router as time_request_router
from app.api.v2.routes.teams import router as team_router

app = FastAPI(title="RosterReady API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://rosterready1.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v2")
app.include_router(team_router, prefix="/api/v2")
app.include_router(membership_router, prefix="/api/v2")
app.include_router(skill_router, prefix="/api/v2")
app.include_router(shift_router, prefix="/api/v2")
app.include_router(time_request_router, prefix="/api/v2")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "2"}
