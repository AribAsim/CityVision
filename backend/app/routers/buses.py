from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/buses", tags=["Buses"])


@router.get("", response_model=List[schemas.BusResponse])
def get_all_buses(db: Session = Depends(get_db)):
    """Retrieve all active/monitored buses with their latest telemetry."""
    buses = db.query(models.Bus).order_by(models.Bus.last_seen.desc()).all()
    return buses
