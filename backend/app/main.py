import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import engine, Base
from .routers import ingest, incidents, buses, analytics, scan

# Create SQLite tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SIH26124 Road Anomaly Sensing API",
    version="1.1.0",
    description="Backend for simulated public-transport mobile sensing system with incident intelligence layer."
)

# CORS configuration for React development servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
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


@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "SIH26124 Road Anomaly Platform"}
