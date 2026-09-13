from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base


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
    
    first_detected_at = Column(DateTime, default=utc_now, nullable=False)
    last_detected_at = Column(DateTime, default=utc_now, nullable=False)
    
    confirmation_count = Column(Integer, default=1, nullable=False)
    unique_bus_count = Column(Integer, default=1, nullable=False)
    primary_image_url = Column(String, nullable=True)

    # Relationships
    observations = relationship("Observation", back_populates="incident", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="incident", cascade="all, delete-orphan")


class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    edge_event_id = Column(String, unique=True, index=True, nullable=False)
    bus_id = Column(String, index=True, nullable=False)
    route_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
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
