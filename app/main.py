from fastapi import FastAPI
from .database import Base, engine
from .routers import jobs, interviews, health

# Create tables on startup (simple for MVP)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Interviewer MVP")

app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(interviews.router)
