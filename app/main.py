from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .middleware.rate_limit import RateLimitMiddleware

from .routers import health, jobs, interviews, admin, auth, portal, candidate
from .routers.public import router as public_router

import os

app = FastAPI()

# ----------------------------
# CORS (production friendly)
# ----------------------------
# Set this in Render env: CORS_ORIGINS="https://your-frontend-domain,https://*.replit.dev,https://*.replit.app"
cors_origins_raw = os.getenv("CORS_ORIGINS", "")
cors_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

allow_origin_regex = os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.(replit\.dev|replit\.app)$")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else [],
    allow_origin_regex=None if cors_origins else allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "120")))

# ----------------------------
# Routers (NO double prefixing)
# ----------------------------
app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(interviews.router)
app.include_router(public_router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(portal.router)
app.include_router(candidate.router)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
