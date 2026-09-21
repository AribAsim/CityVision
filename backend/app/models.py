from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.orm import relationship
try:
    from geoalchemy2 import Geometry
except ImportError:
    Geometry = None
from .database import Base, DATABASE_URL


def utc_now():
    return datetime.now(timezone.utc)


class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(String, unique=True, index=True, nullable=False)
    route_id = Column(String, index=True, nullable=False)
    status = Column(String, default="Active", nullable=False)  # Active, Idle, Maintenance
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    last_seen = Column(DateTime, default=utc_now, onupdate=utc_now)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, unique=True, index=True, nullable=False)  # INC-XXXXXX
    anomaly_type = Column(String, index=True, nullable=False)  # Pothole, Crack, Crack-Severe, Speed-Bump
    severity = Column(String, index=True, nullable=False, default="Medium")  # Low, Medium, High, Critical
    priority_score = Column(Integer, nullable=False, default=50)  # 0 - 100
    status = Column(String, index=True, nullable=False, default="NEW")  # NEW -> VERIFIED -> ASSIGNED -> IN_PROGRESS -> RESOLVED
    
    # Centroid coordinates
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Optional PostGIS geometry column (Geometry when PostgreSQL is active, String/Text placeholder when SQLite)
    if "postgres" in DATABASE_URL and Geometry is not None:
        geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    else:
        geom = Column(String, nullable=True)
    
    first_detected_at = Column(DateTime, default=utc_now, nullable=False)
    last_detected_at = Column(DateTime, default=utc_now, nullable=False)
    
    confirmation_count = Column(Integer, default=1, nullable=False)
    unique_bus_count = Column(Integer, default=1, nullable=False)
    primary_image_url = Column(String, nullable=True)

    # Relationships
    observations = relationship("Observation", back_populates="incident", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="incident", cascade="all, delete-orphan")
    plate_reads = relationship("PlateRead", backref="incident")


class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    edge_event_id = Column(String, unique=True, index=True, nullable=False)
    message_id = Column(String, unique=True, index=True, nullable=True)  # MQTT / Event lineage
    bus_id = Column(String, index=True, nullable=False)
    route_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    if "postgres" in DATABASE_URL and Geometry is not None:
        geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    else:
        geom = Column(String, nullable=True)
    speed_kmh = Column(Float, default=0.0, nullable=False)
    confidence = Column(Float, nullable=False)
    image_url = Column(String, nullable=True)

    incident = relationship("Incident", back_populates="observations")


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=False)
    changed_at = Column(DateTime, default=utc_now, nullable=False)
    notes = Column(Text, nullable=True)

    incident = relationship("Incident", back_populates="status_history")


class PlateRead(Base):
    __tablename__ = "plate_reads"

    id = Column(Integer, primary_key=True, index=True)
    # Critical requirement from Mistake #4: PlateRead.incident_id must be NULLABLE
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    edge_event_id = Column(String, index=True, nullable=True)
    bus_id = Column(String, index=True, nullable=False)
    route_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    plate_text = Column(String, index=True, nullable=False)
    plate_confidence = Column(Float, nullable=False)
    ocr_confidence = Column(Float, nullable=False)
    image_url = Column(String, nullable=True)


class InfraObservation(Base):
    __tablename__ = "infra_observations"

    id = Column(Integer, primary_key=True, index=True)
    sign_type = Column(String, index=True, nullable=False)  # e.g., 'speed-100', 'no-parking'
    confidence = Column(Float, nullable=False)
    bus_id = Column(String, index=True, nullable=False)
    route_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    image_url = Column(String, nullable=True)


class TrafficDensity(Base):
    __tablename__ = "traffic_density"

    id = Column(Integer, primary_key=True, index=True)
    segment_key = Column(String, index=True, nullable=False)  # e.g. "ROUTE-RED:28.613:77.209"
    route_id = Column(String, index=True, nullable=False)
    bus_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    count_person = Column(Integer, default=0, nullable=False)
    count_bicycle = Column(Integer, default=0, nullable=False)
    count_car = Column(Integer, default=0, nullable=False)
    count_motorcycle = Column(Integer, default=0, nullable=False)
    count_bus = Column(Integer, default=0, nullable=False)
    count_truck = Column(Integer, default=0, nullable=False)
    total_count = Column(Integer, default=0, nullable=False)
    congestion_index = Column(Float, default=0.0, nullable=False)

