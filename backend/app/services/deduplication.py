import math
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
try:
    import geoalchemy2
except ImportError:
    geoalchemy2 = None
from .. import models


def calculate_haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two coordinates on Earth."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def find_matching_incident(
    db: Session,
    anomaly_type: str,
    lat: float,
    lon: float,
    radius_meters: float = 15.0
) -> Optional[models.Incident]:
    """
    Find existing open (non-RESOLVED) incident within radius_meters with the same anomaly_type.
    Uses PostGIS ST_DWithin if PostgreSQL dialect is detected and geom is available,
    otherwise uses pure Haversine distance.
    Returns the nearest matching Incident or None.
    """
    bind = db.get_bind()
    if bind and bind.dialect.name == "postgresql":
        try:
            from geoalchemy2.functions import ST_DWithin, ST_SetSRID, ST_MakePoint, ST_Distance
            point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
            # PostGIS ST_DWithin on geography/geometry (cast to geography for meter accuracy)
            match = (
                db.query(models.Incident)
                .filter(
                    models.Incident.anomaly_type == anomaly_type,
                    models.Incident.status != "RESOLVED",
                    ST_DWithin(models.Incident.geom.cast(geoalchemy2.Geography), point.cast(geoalchemy2.Geography), radius_meters)
                )
                .order_by(ST_Distance(models.Incident.geom.cast(geoalchemy2.Geography), point.cast(geoalchemy2.Geography)))
                .first()
            )
            if match:
                return match
        except Exception as e:
            # Fall back to Haversine if PostGIS functions fail or geom is null
            pass

    open_incidents = (
        db.query(models.Incident)
        .filter(
            models.Incident.anomaly_type == anomaly_type,
            models.Incident.status != "RESOLVED"
        )
        .all()
    )

    closest_incident: Optional[models.Incident] = None
    min_dist = float("inf")

    for incident in open_incidents:
        dist = calculate_haversine_meters(incident.latitude, incident.longitude, lat, lon)
        if dist <= radius_meters and dist < min_dist:
            min_dist = dist
            closest_incident = incident

    return closest_incident


def is_rapid_duplicate_observation(
    db: Session,
    incident_id: int,
    bus_id: str,
    current_time: datetime,
    cooldown_seconds: float = 2.0
) -> bool:
    """
    Check if the same bus already submitted an observation for this incident
    within `cooldown_seconds`. Used to suppress rapid frame-by-frame spam from the same bus.
    """
    latest_obs = (
        db.query(models.Observation)
        .filter(
            models.Observation.incident_id == incident_id,
            models.Observation.bus_id == bus_id
        )
        .order_by(models.Observation.timestamp.desc())
        .first()
    )

    if not latest_obs:
        return False

    obs_time = latest_obs.timestamp
    if obs_time.tzinfo is None:
        obs_time = obs_time.replace(tzinfo=timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    delta = abs((current_time - obs_time).total_seconds())
    return delta < cooldown_seconds
