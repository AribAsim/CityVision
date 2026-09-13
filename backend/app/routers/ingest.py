import os
import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas
from ..services.event_fusion import fuse_edge_event

router = APIRouter(prefix="/api/ingest", tags=["Ingest"])

SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "snapshots")
os.makedirs(SNAPSHOT_DIR, exist_ok=True)


@router.post("", response_model=schemas.IncidentSummaryResponse, status_code=201)
async def ingest_edge_event(
    event_data: Optional[str] = Form(None),
    event: Optional[str] = Form(None),  # compatibility alias
    image_file: Optional[UploadFile] = File(None),
    evidence: Optional[UploadFile] = File(None),  # compatibility alias
    db: Session = Depends(get_db)
):
    """
    Multipart ingest endpoint:
    - Accepts 'event_data' JSON string matching EdgeEventCreate
    - Accepts optional binary image file ('image_file' or 'evidence')
    """
    raw_json = event_data or event
    if not raw_json:
        raise HTTPException(status_code=400, detail="Missing required 'event_data' field in multipart form")

    try:
        data_dict = json.loads(raw_json)
        # Adapt field names if edge used event_type instead of anomaly_type
        if "event_type" in data_dict and "anomaly_type" not in data_dict:
            data_dict["anomaly_type"] = data_dict["event_type"]
        if "event_id" in data_dict and "edge_event_id" not in data_dict:
            data_dict["edge_event_id"] = data_dict["event_id"]

        event_create = schemas.EdgeEventCreate(**data_dict)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid event JSON structure: {str(e)}")

    # Handle image file if uploaded
    image = image_file or evidence
    image_rel_url = None
    if image and image.filename:
        file_id = event_create.edge_event_id or str(uuid.uuid4())
        ext = os.path.splitext(image.filename)[1] or ".jpg"
        filename = f"{file_id}{ext}"
        filepath = os.path.join(SNAPSHOT_DIR, filename)
        content = await image.read()
        with open(filepath, "wb") as f:
            f.write(content)
        image_rel_url = f"/static/snapshots/{filename}"

    incident = fuse_edge_event(db=db, event_data=event_create, image_url=image_rel_url)
    return incident


@router.post("/json", response_model=schemas.IncidentSummaryResponse, status_code=201)
def ingest_edge_event_json(
    event_in: schemas.EdgeEventCreate,
    db: Session = Depends(get_db)
):
    """Direct JSON ingest endpoint without file upload."""
    incident = fuse_edge_event(db=db, event_data=event_in, image_url=event_in.image_url)
    return incident


@router.get("/plates", response_model=list[schemas.PlateReadResponse])
def list_plate_reads(
    bus_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Retrieve ANPR license plate detections."""
    from .. import models
    q = db.query(models.PlateRead)
    if bus_id:
        q = q.filter(models.PlateRead.bus_id == bus_id)
    return q.order_by(models.PlateRead.timestamp.desc()).limit(limit).all()


@router.get("/infra", response_model=list[schemas.InfraObservationResponse])
def list_infra_observations(
    bus_id: Optional[str] = None,
    sign_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Retrieve road infrastructure and traffic sign observations."""
    from .. import models
    q = db.query(models.InfraObservation)
    if bus_id:
        q = q.filter(models.InfraObservation.bus_id == bus_id)
    if sign_type:
        q = q.filter(models.InfraObservation.sign_type == sign_type)
    return q.order_by(models.InfraObservation.timestamp.desc()).limit(limit).all()


@router.post("/plate", response_model=schemas.PlateReadResponse, status_code=201)
def ingest_plate_read(
    plate_in: schemas.PlateReadCreate,
    db: Session = Depends(get_db)
):
    """Direct standalone ANPR plate read ingestion."""
    from datetime import timezone
    from .. import models
    now = plate_in.timestamp or datetime.now(timezone.utc)
    entry = models.PlateRead(
        incident_id=plate_in.incident_id,
        edge_event_id=plate_in.edge_event_id,
        bus_id=plate_in.bus_id,
        route_id=plate_in.route_id,
        timestamp=now,
        latitude=plate_in.latitude,
        longitude=plate_in.longitude,
        plate_text=plate_in.plate_text,
        plate_confidence=plate_in.plate_confidence,
        ocr_confidence=plate_in.ocr_confidence,
        image_url=plate_in.image_url,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/infra", response_model=schemas.InfraObservationResponse, status_code=201)
def ingest_infra_observation(
    infra_in: schemas.InfraObservationCreate,
    db: Session = Depends(get_db)
):
    """Direct standalone traffic sign observation ingestion."""
    from datetime import timezone
    from .. import models
    now = infra_in.timestamp or datetime.now(timezone.utc)
    entry = models.InfraObservation(
        sign_type=infra_in.sign_type,
        confidence=infra_in.confidence,
        bus_id=infra_in.bus_id,
        route_id=infra_in.route_id,
        timestamp=now,
        latitude=infra_in.latitude,
        longitude=infra_in.longitude,
        image_url=infra_in.image_url,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

