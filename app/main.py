from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers import health, jobs, interviews
from .routers.public import router as public_router
from .routers import admin
from app.middleware.rate_limit import RateLimitMiddleware
from .routers import auth
from .routers import portal

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.(replit\.dev|replit\.app)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60  
)
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
app.include_router(public_router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(portal.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)