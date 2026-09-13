import math
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .. import models, schemas


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two coordinates."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def update_bus_telemetry(db: Session, bus_id: str, route_id: str, lat: float, lon: float):
    """Upsert bus telemetry on every event reported."""
    bus = db.query(models.Bus).filter(models.Bus.bus_id == bus_id).first()
    now = datetime.now(timezone.utc)
    if bus:
        bus.route_id = route_id
        bus.latitude = lat
        bus.longitude = lon
        bus.last_seen = now
        bus.status = "Active"
    else:
        bus = models.Bus(
            bus_id=bus_id,
            route_id=route_id,
            status="Active",
            latitude=lat,
            longitude=lon,
            last_seen=now
        )
        db.add(bus)
    db.commit()
    db.refresh(bus)
    return bus
