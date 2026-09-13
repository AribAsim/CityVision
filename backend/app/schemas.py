from datetime import datetime
from typing import Optional, List, Dict, Union
from pydantic import BaseModel, Field, ConfigDict


# --- Bus Schemas ---
class BusBase(BaseModel):
    bus_id: str
    route_id: str
    status: str = "Active"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class BusCreate(BusBase):
    pass


class BusResponse(BusBase):
    id: int
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Edge Ingestion Schema ---
class EdgeEventCreate(BaseModel):
    schema_version: Optional[int] = Field(default=1, description="Schema version: 1 (MVP) or 2 (Multi-perception)")
    edge_event_id: Optional[str] = Field(default=None, description="UUID or client ID from edge device")
    message_id: Optional[str] = Field(default=None, description="Idempotency key / MQTT message ID")
    bus_id: str
    route_id: str
    timestamp: Optional[datetime] = None
    latitude: float
    longitude: float
    speed_kmh: Optional[float] = 0.0
    anomaly_type: str = Field(..., description="Pothole, Crack, Crack-Severe, Speed-Bump")
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: Optional[List[int]] = None
    severity: Optional[str] = None
    priority_score: Optional[Union[int, float]] = None
    image_url: Optional[str] = None
    # Optional Multi-Perception v2 fields
    nearby_plates: Optional[List[Dict[str, Union[str, float, List[int]]]]] = Field(default_factory=list)
    nearby_signs: Optional[List[Dict[str, Union[str, float, List[int]]]]] = Field(default_factory=list)


# --- Observation Schemas ---
class ObservationResponse(BaseModel):
    id: int
    edge_event_id: str
    message_id: Optional[str] = None
    bus_id: str
    route_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    speed_kmh: float
    confidence: float
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Status History Schemas ---
class StatusHistoryResponse(BaseModel):
    id: int
    from_status: Optional[str] = None
    to_status: str
    changed_at: datetime
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Multi-Perception Schemas (ANPR & Infra) ---
class PlateReadBase(BaseModel):
    incident_id: Optional[int] = None
    edge_event_id: Optional[str] = None
    bus_id: str
    route_id: str
    timestamp: Optional[datetime] = None
    latitude: float
    longitude: float
    plate_text: str
    plate_confidence: float = 0.0
    ocr_confidence: float = 0.0
    image_url: Optional[str] = None


class PlateReadCreate(PlateReadBase):
    pass


class PlateReadResponse(PlateReadBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class InfraObservationBase(BaseModel):
    sign_type: str
    confidence: float
    bus_id: str
    route_id: str
    timestamp: Optional[datetime] = None
    latitude: float
    longitude: float
    image_url: Optional[str] = None


class InfraObservationCreate(InfraObservationBase):
    pass


class InfraObservationResponse(InfraObservationBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Incident Schemas ---
class IncidentSummaryResponse(BaseModel):
    id: int
    incident_id: str
    anomaly_type: str
    severity: str
    priority_score: int
    status: str
    latitude: float
    longitude: float
    first_detected_at: datetime
    last_detected_at: datetime
    confirmation_count: int
    unique_bus_count: int
    primary_image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IncidentDetailResponse(IncidentSummaryResponse):
    observations: List[ObservationResponse] = []
    status_history: List[StatusHistoryResponse] = []
    plate_reads: List[PlateReadResponse] = []

    model_config = ConfigDict(from_attributes=True)


class IncidentStatusUpdate(BaseModel):
    status: str = Field(..., description="NEW, VERIFIED, ASSIGNED, IN_PROGRESS, RESOLVED")
    notes: Optional[str] = None


# --- Analytics Schemas ---
class AnalyticsSummary(BaseModel):
    total_incidents: int
    pending_count: int  # For backwards compatibility / summary
    verified_count: int
    assigned_count: int
    in_progress_count: int
    resolved_count: int
    multi_bus_verified_count: int
    active_buses: int
    by_anomaly_type: Dict[str, int]
    by_severity: Dict[str, int]
    pci: Optional[float] = 78.5
    pci_rating: Optional[str] = "Satisfactory"


# --- Scan Schemas ---
class ScanStartResponse(BaseModel):
    job_id: str
    status: str = "PROCESSING"
    message: str = "Scan initiated"


class ScanStatusResponse(BaseModel):
    job_id: str
    status: str  # "UPLOADING", "PROCESSING", "COMPLETED", "FAILED"
    events_dispatched: int = 0
    error: Optional[str] = None

