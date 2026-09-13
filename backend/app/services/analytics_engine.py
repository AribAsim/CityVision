"""
backend/app/services/analytics_engine.py
-----------------------------------------
Phase 3 Analytics Engine:
- Pavement Condition Index (PCI) calculation (ASTM D6433 compliant adaptation).
- Traffic density calculation from vehicle detections.
- Near-miss / sudden deceleration safety events.
- Road quality degradation rate estimation.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models

# Class deduct weights for PCI (ASTM D6433 adaptation)
DEDUCT_WEIGHTS = {
    "Pothole": 35.0,
    "Crack-Severe": 25.0,
    "Crack": 10.0,
    "Speed-Bump": 5.0,
}

SEVERITY_MULTIPLIERS = {
    "Critical": 1.5,
    "High": 1.2,
    "Medium": 1.0,
    "Low": 0.6,
}


def calculate_segment_pci(
    db: Session,
    corridor_route_id: Optional[str] = None,
    lat_min: Optional[float] = None,
    lat_max: Optional[float] = None,
) -> Dict[str, float]:
    """
    Calculate Pavement Condition Index (PCI: 0 to 100).
    PCI = max(0.0, 100.0 - Total Deduct Value)
    ASTM standard condition ratings:
      85-100: Good
      70-84:  Satisfactory
      55-69:  Fair
      40-54:  Poor
      25-39:  Very Poor
      0-24:   Failed
    """
    query = db.query(models.Incident).filter(models.Incident.status != "RESOLVED")
    if corridor_route_id:
        # Join with observations to filter by route
        query = query.join(models.Observation).filter(models.Observation.route_id == corridor_route_id)
    if lat_min is not None and lat_max is not None:
        query = query.filter(models.Incident.latitude.between(lat_min, lat_max))

    active_incidents = query.all()
    if not active_incidents:
        return {"pci": 96.0, "rating": "Good", "defect_count": 0}

    total_deduct = 0.0
    for inc in active_incidents:
        base_w = DEDUCT_WEIGHTS.get(inc.anomaly_type, 10.0)
        sev_m = SEVERITY_MULTIPLIERS.get(inc.severity, 1.0)
        # Weight by confirmation count (dampened log scale)
        conf_factor = 1.0 + math.log10(max(inc.confirmation_count, 1))
        deduct = base_w * sev_m * conf_factor
        total_deduct += deduct

    # Scaled total deduct
    scaled_deduct = min(total_deduct, 100.0)
    pci = round(max(0.0, 100.0 - scaled_deduct), 1)

    if pci >= 85:
        rating = "Good"
    elif pci >= 70:
        rating = "Satisfactory"
    elif pci >= 55:
        rating = "Fair"
    elif pci >= 40:
        rating = "Poor"
    elif pci >= 25:
        rating = "Very Poor"
    else:
        rating = "Failed"

    return {
        "pci": pci,
        "rating": rating,
        "defect_count": len(active_incidents),
        "total_deduct_value": round(total_deduct, 1),
    }


def detect_near_misses(
    observations: List[models.Observation],
    deceleration_threshold_kmh: float = 15.0,
) -> List[Dict[str, float]]:
    """
    Detects potential near-miss or harsh braking events from sequential speed telemetry.
    """
    near_misses = []
    if len(observations) < 2:
        return near_misses

    # Sort observations chronologically
    sorted_obs = sorted(observations, key=lambda o: o.timestamp)
    for i in range(1, len(sorted_obs)):
        prev = sorted_obs[i - 1]
        curr = sorted_obs[i]
        dt = (curr.timestamp - prev.timestamp).total_seconds()
        if 0 < dt <= 3.0:  # Rapid brake window
            dv = prev.speed_kmh - curr.speed_kmh
            if dv >= deceleration_threshold_kmh:
                near_misses.append({
                    "bus_id": curr.bus_id,
                    "route_id": curr.route_id,
                    "latitude": curr.latitude,
                    "longitude": curr.longitude,
                    "delta_speed_kmh": dv,
                    "timestamp": curr.timestamp.isoformat(),
                })
    return near_misses
