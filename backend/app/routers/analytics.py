from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary", response_model=schemas.AnalyticsSummary)
def get_analytics_summary(db: Session = Depends(get_db)):
    """Summary metrics for the municipal authority dashboard."""
    total_incidents = db.query(models.Incident).count()

    new_count = db.query(models.Incident).filter(models.Incident.status == "NEW").count()
    verified_count = db.query(models.Incident).filter(models.Incident.status == "VERIFIED").count()
    assigned_count = db.query(models.Incident).filter(models.Incident.status == "ASSIGNED").count()
    in_progress_count = db.query(models.Incident).filter(models.Incident.status == "IN_PROGRESS").count()
    resolved_count = db.query(models.Incident).filter(models.Incident.status == "RESOLVED").count()

    multi_bus_verified = (
        db.query(models.Incident)
        .filter(models.Incident.unique_bus_count >= 2)
        .count()
    )

    active_buses = db.query(models.Bus).filter(models.Bus.status == "Active").count()

    # Breakdown by anomaly_type
    type_counts = (
        db.query(models.Incident.anomaly_type, func.count(models.Incident.id))
        .group_by(models.Incident.anomaly_type)
        .all()
    )
    by_anomaly_type = {t: count for t, count in type_counts}

    # Breakdown by severity
    severity_counts = (
        db.query(models.Incident.severity, func.count(models.Incident.id))
        .group_by(models.Incident.severity)
        .all()
    )
    by_severity = {s: count for s, count in severity_counts}

    # Calculate real Segment PCI
    from ..services.analytics_engine import calculate_segment_pci
    pci_data = calculate_segment_pci(db)

    return schemas.AnalyticsSummary(
        total_incidents=total_incidents,
        pending_count=new_count,  # mapped to new/pending for dashboard summary
        verified_count=verified_count,
        assigned_count=assigned_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        multi_bus_verified_count=multi_bus_verified,
        active_buses=active_buses,
        by_anomaly_type=by_anomaly_type,
        by_severity=by_severity,
        pci=pci_data["pci"],
        pci_rating=pci_data["rating"],
    )
