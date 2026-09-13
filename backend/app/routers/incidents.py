from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from ..services.event_fusion import transition_incident_status

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.get("", response_model=List[schemas.IncidentSummaryResponse])
def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status: NEW, VERIFIED, ASSIGNED, IN_PROGRESS, RESOLVED"),
    severity: Optional[str] = Query(None, description="Filter by severity: Low, Medium, High, Critical"),
    anomaly_type: Optional[str] = Query(None, description="Filter by anomaly type: Pothole, Crack, etc."),
    db: Session = Depends(get_db)
):
    """Retrieve road defect incidents with optional filtering."""
    query = db.query(models.Incident)
    if status:
        query = query.filter(models.Incident.status == status)
    if severity:
        query = query.filter(models.Incident.severity == severity)
    if anomaly_type:
        query = query.filter(models.Incident.anomaly_type == anomaly_type)

    return query.order_by(models.Incident.last_detected_at.desc()).all()


@router.get("/{incident_id}", response_model=schemas.IncidentDetailResponse)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """Retrieve full incident details including observations and status history."""
    incident = (
        db.query(models.Incident)
        .filter(
            (models.Incident.incident_id == incident_id) |
            (models.Incident.id == int(incident_id) if incident_id.isdigit() else False)
        )
        .first()
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}/status", response_model=schemas.IncidentDetailResponse)
def update_incident_status(
    incident_id: str,
    update_data: schemas.IncidentStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update incident lifecycle status with strict transition validation.
    Status flow: NEW -> VERIFIED -> ASSIGNED -> IN_PROGRESS -> RESOLVED.
    """
    incident = (
        db.query(models.Incident)
        .filter(
            (models.Incident.incident_id == incident_id) |
            (models.Incident.id == int(incident_id) if incident_id.isdigit() else False)
        )
        .first()
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    try:
        updated = transition_incident_status(
            db=db,
            incident=incident,
            new_status=update_data.status,
            notes=update_data.notes
        )
        return updated
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))


@router.get("/{incident_id}/report.pdf")
def get_incident_pdf_report(incident_id: str, db: Session = Depends(get_db)):
    """Generate and return a formal Municipal Work Order PDF for this incident."""
    from fastapi.responses import Response
    from ..services.pdf_report import generate_incident_pdf

    incident = (
        db.query(models.Incident)
        .filter(
            (models.Incident.incident_id == incident_id) |
            (models.Incident.id == int(incident_id) if incident_id.isdigit() else False)
        )
        .first()
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    pdf_bytes = generate_incident_pdf(incident)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=WorkOrder_{incident.incident_id}.pdf"},
    )
