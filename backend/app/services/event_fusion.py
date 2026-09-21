import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from .. import models, schemas
from .deduplication import find_matching_incident, is_rapid_duplicate_observation
from .severity import calculate_base_severity, compute_priority_score, evaluate_incident_severity
from .telemetry import update_bus_telemetry


VALID_STATUSES = ["NEW", "VERIFIED", "ASSIGNED", "IN_PROGRESS", "RESOLVED"]

VALID_STATUS_TRANSITIONS = {
    "NEW": ["VERIFIED", "ASSIGNED", "IN_PROGRESS", "RESOLVED"],
    "VERIFIED": ["ASSIGNED", "IN_PROGRESS", "RESOLVED"],
    "ASSIGNED": ["IN_PROGRESS", "RESOLVED"],
    "IN_PROGRESS": ["RESOLVED"],
    "RESOLVED": []  # Terminal state
}


def transition_incident_status(
    db: Session,
    incident: models.Incident,
    new_status: str,
    notes: Optional[str] = None
) -> models.Incident:
    """
    Validate and apply a status transition for an incident.
    Records an entry in StatusHistory.
    """
    current_status = incident.status
    if new_status == current_status:
        return incident

    allowed = VALID_STATUS_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Invalid status transition from '{current_status}' to '{new_status}'. Allowed transitions: {allowed}"
        )

    incident.status = new_status
    history = models.StatusHistory(
        incident_id=incident.id,
        from_status=current_status,
        to_status=new_status,
        changed_at=datetime.now(timezone.utc),
        notes=notes
    )
    db.add(history)
    db.commit()
    db.refresh(incident)
    return incident


def fuse_edge_event(
    db: Session,
    event_data: schemas.EdgeEventCreate,
    image_url: Optional[str] = None
) -> models.Incident:
    """
    Core Intelligence Layer:
    1. Spatial clustering and deduplication.
    2. Incident creation or observation aggregation.
    3. Multi-bus confirmation and dynamic severity escalation.
    4. Status lifecycle management (auto-verification on multi-bus).
    5. Telemetry update for reporting bus.
    """
    now = event_data.timestamp or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    edge_id = event_data.edge_event_id or f"EVT-{uuid.uuid4().hex[:8].upper()}"
    final_image_url = image_url or event_data.image_url

    # Check if observation already exists with this exact edge_event_id
    existing_obs = db.query(models.Observation).filter(models.Observation.edge_event_id == edge_id).first()
    if existing_obs:
        return existing_obs.incident

    # Spatial correlation: check within 15 meters
    matched_incident = find_matching_incident(
        db=db,
        anomaly_type=event_data.anomaly_type,
        lat=event_data.latitude,
        lon=event_data.longitude,
        radius_meters=15.0
    )

    if matched_incident:
        target_incident = matched_incident
        # Check rapid spam from the same bus
        is_spam = is_rapid_duplicate_observation(
            db=db,
            incident_id=matched_incident.id,
            bus_id=event_data.bus_id,
            current_time=now,
            cooldown_seconds=2.0
        )

        if not is_spam:
            # Register new observation
            bind = db.get_bind()
            geom_val = None
            if bind and bind.dialect.name == "postgresql":
                from geoalchemy2.functions import ST_SetSRID, ST_MakePoint
                geom_val = ST_SetSRID(ST_MakePoint(event_data.longitude, event_data.latitude), 4326)

            obs = models.Observation(
                incident_id=matched_incident.id,
                edge_event_id=edge_id,
                message_id=event_data.message_id,
                bus_id=event_data.bus_id,
                route_id=event_data.route_id,
                timestamp=now,
                latitude=event_data.latitude,
                longitude=event_data.longitude,
                geom=geom_val,
                speed_kmh=event_data.speed_kmh or 0.0,
                confidence=event_data.confidence,
                image_url=final_image_url
            )
            db.add(obs)
            db.flush()

            # Update observation counts
            matched_incident.confirmation_count += 1
            
            # Recalculate unique bus count
            unique_buses = (
                db.query(func.count(distinct(models.Observation.bus_id)))
                .filter(models.Observation.incident_id == matched_incident.id)
                .scalar()
            ) or 1
            matched_incident.unique_bus_count = unique_buses

            # Recalculate centroid coordinates (running average)
            n = matched_incident.confirmation_count
            matched_incident.latitude = ((matched_incident.latitude * (n - 1)) + event_data.latitude) / n
            matched_incident.longitude = ((matched_incident.longitude * (n - 1)) + event_data.longitude) / n
            if bind and bind.dialect.name == "postgresql":
                from geoalchemy2.functions import ST_SetSRID, ST_MakePoint
                matched_incident.geom = ST_SetSRID(ST_MakePoint(matched_incident.longitude, matched_incident.latitude), 4326)
            matched_incident.last_detected_at = now

            if final_image_url:
                matched_incident.primary_image_url = final_image_url

            # Evaluate severity & priority score escalation
            matched_incident.severity = evaluate_incident_severity(
                initial_severity=matched_incident.severity,
                confirmation_count=matched_incident.confirmation_count,
                unique_bus_count=matched_incident.unique_bus_count
            )
            matched_incident.priority_score = compute_priority_score(
                anomaly_type=matched_incident.anomaly_type,
                confidence=max(event_data.confidence, 0.7),
                confirmation_count=matched_incident.confirmation_count,
                unique_bus_count=matched_incident.unique_bus_count
            )

            # Auto-verification if confirmed by multiple buses
            if matched_incident.unique_bus_count >= 2 and matched_incident.status == "NEW":
                matched_incident.status = "VERIFIED"
                history = models.StatusHistory(
                    incident_id=matched_incident.id,
                    from_status="NEW",
                    to_status="VERIFIED",
                    changed_at=now,
                    notes=f"Auto-verified: confirmed by {matched_incident.unique_bus_count} unique buses"
                )
                db.add(history)

        target_incident = matched_incident

    else:
        # Create fresh incident
        inc_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        base_sev = event_data.severity or calculate_base_severity(event_data.confidence)
        raw_prio = event_data.priority_score if event_data.priority_score is not None else compute_priority_score(
            anomaly_type=event_data.anomaly_type,
            confidence=event_data.confidence,
            confirmation_count=1,
            unique_bus_count=1
        )
        base_prio = int(round(float(raw_prio)))

        bind = db.get_bind()
        geom_val = None
        if bind and bind.dialect.name == "postgresql":
            from geoalchemy2.functions import ST_SetSRID, ST_MakePoint
            geom_val = ST_SetSRID(ST_MakePoint(event_data.longitude, event_data.latitude), 4326)

        new_incident = models.Incident(
            incident_id=inc_id,
            anomaly_type=event_data.anomaly_type,
            severity=base_sev,
            priority_score=base_prio,
            status="NEW",
            latitude=event_data.latitude,
            longitude=event_data.longitude,
            geom=geom_val,
            first_detected_at=now,
            last_detected_at=now,
            confirmation_count=1,
            unique_bus_count=1,
            primary_image_url=final_image_url
        )
        db.add(new_incident)
        db.flush()

        # Initial StatusHistory
        history = models.StatusHistory(
            incident_id=new_incident.id,
            from_status=None,
            to_status="NEW",
            changed_at=now,
            notes="Initial defect detection logged by edge sensor"
        )
        db.add(history)

        # First Observation
        obs = models.Observation(
            incident_id=new_incident.id,
            edge_event_id=edge_id,
            message_id=event_data.message_id,
            bus_id=event_data.bus_id,
            route_id=event_data.route_id,
            timestamp=now,
            latitude=event_data.latitude,
            longitude=event_data.longitude,
            geom=geom_val,
            speed_kmh=event_data.speed_kmh or 0.0,
            confidence=event_data.confidence,
            image_url=final_image_url
        )
        db.add(obs)
        target_incident = new_incident

    # Persist optional v2 perception data (PlateRead & InfraObservation)
    if event_data.nearby_plates:
        for p in event_data.nearby_plates:
            plate_entry = models.PlateRead(
                incident_id=target_incident.id,
                edge_event_id=edge_id,
                bus_id=event_data.bus_id,
                route_id=event_data.route_id,
                timestamp=now,
                latitude=event_data.latitude,
                longitude=event_data.longitude,
                plate_text=str(p.get("plate_text", "")),
                plate_confidence=float(p.get("plate_confidence", 0.0)),
                ocr_confidence=float(p.get("ocr_confidence", 0.0)),
                image_url=final_image_url,
            )
            db.add(plate_entry)

    if event_data.nearby_signs:
        for s in event_data.nearby_signs:
            infra_entry = models.InfraObservation(
                sign_type=str(s.get("sign_type", s.get("class_name", "unknown"))),
                confidence=float(s.get("confidence", 0.0)),
                bus_id=event_data.bus_id,
                route_id=event_data.route_id,
                timestamp=now,
                latitude=event_data.latitude,
                longitude=event_data.longitude,
                image_url=final_image_url,
            )
            db.add(infra_entry)

    # Update bus telemetry
    update_bus_telemetry(db, event_data.bus_id, event_data.route_id, event_data.latitude, event_data.longitude)

    db.commit()
    db.refresh(target_incident)
    return target_incident
