import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import engine, Base
from .routers import ingest, incidents, buses, analytics, scan, telemetry, reports

# Create SQLite tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SIH26124 Road Anomaly Sensing API",
    version="1.1.0",
    description="Backend for simulated public-transport mobile sensing system with incident intelligence layer."
)

# CORS configuration for development and Render deployment
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env and cors_origins_env != "*":
    allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"https://.*\.onrender\.com",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Default permissive CORS for hackathon / cross-origin deployments
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount static files directory for evidence snapshots
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(os.path.join(STATIC_DIR, "snapshots"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include Routers
app.include_router(ingest.router)
app.include_router(incidents.router)
app.include_router(buses.router)
app.include_router(analytics.router)
app.include_router(scan.router)
app.include_router(telemetry.router)
app.include_router(reports.router)



@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "SIH26124 Road Anomaly Platform"}


# Optional SPA mounting if frontend build exists (supports single-service Render deployments)
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
