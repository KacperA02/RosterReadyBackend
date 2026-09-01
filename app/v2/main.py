from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.v2.auth_routes import router as auth_router
from app.v2.team_routes import router as team_router

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "2"}

