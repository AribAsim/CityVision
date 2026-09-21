"""
backend/app/routers/telemetry.py
--------------------------------
Endpoints for vehicle density, traffic bottlenecks, route delays,
and origin-destination flow summaries.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db
from .. import models, schemas
from ..services.analytics_engine import (
    compute_congestion_index,
    compute_route_delay,
    compute_od_summary,
)

router = APIRouter(
    prefix="/api/telemetry",
    tags=["telemetry"],
)


@router.post("/density", response_model=schemas.VehicleDensityResponse, status_code=status.HTTP_201_CREATED)
def record_vehicle_density(
    payload: schemas.VehicleDensityCreate,
    db: Session = Depends(get_db),
):
    """
    Ingests batched vehicle density observations from the edge pipeline.
    Calculates congestion index relative to route baseline capacity.
    """
    c_index = compute_congestion_index(payload.route_id, payload.total_count)
    ts = payload.timestamp or datetime.now(timezone.utc)
    lat_val = payload.latitude if payload.latitude is not None else (payload.lat if payload.lat is not None else 0.0)
    lon_val = payload.longitude if payload.longitude is not None else (payload.lon if payload.lon is not None else 0.0)

    density_record = models.TrafficDensity(
        segment_key=payload.segment_key,
        route_id=payload.route_id,
        bus_id=payload.bus_id,
        timestamp=ts,
        latitude=lat_val,
        longitude=lon_val,
        count_person=payload.count_person,
        count_bicycle=payload.count_bicycle,
        count_car=payload.count_car,
        count_motorcycle=payload.count_motorcycle,
        count_bus=payload.count_bus,
        count_truck=payload.count_truck,
        total_count=payload.total_count,
        congestion_index=c_index,
    )
    db.add(density_record)
    db.commit()
    db.refresh(density_record)
    return density_record


@router.get("/density", response_model=List[schemas.VehicleDensityResponse])
def get_vehicle_density(
    route_id: Optional[str] = Query(None, description="Filter by route ID (e.g. ROUTE-RED)"),
    hours: Optional[int] = Query(24, description="Lookback window in hours"),
    limit: int = Query(200, le=1000),
    db: Session = Depends(get_db),
):
    """
    Retrieves recent traffic density records for mapping and heatmap layers.
    """
    query = db.query(models.TrafficDensity)
    if route_id:
        query = query.filter(models.TrafficDensity.route_id == route_id)
    if hours:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = query.filter(models.TrafficDensity.timestamp >= since)

    return query.order_by(desc(models.TrafficDensity.timestamp)).limit(limit).all()


@router.get("/density/bottlenecks")
def get_traffic_bottlenecks(
    route_id: Optional[str] = Query(None),
    top_n: int = Query(5, le=20),
    db: Session = Depends(get_db),
):
    """
    Returns top N congested segments ranked by congestion index and vehicle volume.
    """
    query = db.query(models.TrafficDensity)
    if route_id:
        query = query.filter(models.TrafficDensity.route_id == route_id)

    records = query.order_by(desc(models.TrafficDensity.congestion_index)).limit(top_n).all()

    bottlenecks = []
    for r in records:
        status_label = "Critical" if r.congestion_index >= 1.2 else "Heavy" if r.congestion_index >= 0.8 else "Moderate"
        bottlenecks.append({
            "segment_key": r.segment_key,
            "route_id": r.route_id,
            "bus_id": r.bus_id,
            "peak_count": r.total_count,
            "congestion_index": r.congestion_index,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "timestamp": r.timestamp.isoformat(),
            "status": status_label,
        })
    return bottlenecks


@router.get("/density/delay")
def get_route_delay(
    route_id: str = Query("ROUTE-RED", description="Route ID to analyze"),
    db: Session = Depends(get_db),
):
    """
    Compares observed transit times against baseline corridor free-flow transit times.
    """
    return compute_route_delay(db, route_id)


@router.get("/density/od")
def get_od_flow_summary(
    route_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Returns estimated origin-destination flows between consecutive corridor segments.
    """
    return compute_od_summary(db, route_id)
