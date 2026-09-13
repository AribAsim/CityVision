import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app import models, schemas
from backend.app.services.deduplication import (
    calculate_haversine_meters,
    find_matching_incident,
    is_rapid_duplicate_observation,
)
from backend.app.services.severity import (
    calculate_base_severity,
    escalate_tier,
    compute_priority_score,
    evaluate_incident_severity,
    SeverityRulesConfig,
)
from backend.app.services.event_fusion import (
    fuse_edge_event,
    transition_incident_status,
    VALID_STATUS_TRANSITIONS,
)


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite session for tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Deduplication & Spatial Tests
# ---------------------------------------------------------------------------
def test_haversine_meters_calculation():
    # 0 distance between identical coords
    assert calculate_haversine_meters(28.6139, 77.2090, 28.6139, 77.2090) == pytest.approx(0.0, abs=0.01)
    
    # Approx 111 meters for 0.001 deg latitude
    dist = calculate_haversine_meters(28.6139, 77.2090, 28.6149, 77.2090)
    assert 100 < dist < 120


def test_find_matching_incident_within_15m(db_session):
    now = datetime.now(timezone.utc)
    inc = models.Incident(
        incident_id="INC-TEST01",
        anomaly_type="Pothole",
        severity="High",
        priority_score=80,
        status="NEW",
        latitude=28.613900,
        longitude=77.209000,
        first_detected_at=now,
        last_detected_at=now,
        confirmation_count=1,
        unique_bus_count=1,
    )
    db_session.add(inc)
    db_session.commit()

    # Query within ~5 meters -> should match
    matched = find_matching_incident(
        db_session,
        anomaly_type="Pothole",
        lat=28.613940,
        lon=77.209000,
        radius_meters=15.0
    )
    assert matched is not None
    assert matched.incident_id == "INC-TEST01"

    # Query ~50 meters away -> should NOT match
    no_match = find_matching_incident(
        db_session,
        anomaly_type="Pothole",
        lat=28.614500,
        lon=77.209000,
        radius_meters=15.0
    )
    assert no_match is None


def test_find_matching_incident_ignores_resolved(db_session):
    now = datetime.now(timezone.utc)
    resolved_inc = models.Incident(
        incident_id="INC-RESOLVED",
        anomaly_type="Pothole",
        severity="High",
        priority_score=80,
        status="RESOLVED",
        latitude=28.613900,
        longitude=77.209000,
        first_detected_at=now,
        last_detected_at=now,
        confirmation_count=1,
        unique_bus_count=1,
    )
    db_session.add(resolved_inc)
    db_session.commit()

    matched = find_matching_incident(
        db_session,
        anomaly_type="Pothole",
        lat=28.613900,
        lon=77.209000,
        radius_meters=15.0
    )
    assert matched is None


def test_is_rapid_duplicate_observation(db_session):
    now = datetime.now(timezone.utc)
    inc = models.Incident(
        incident_id="INC-TEST02",
        anomaly_type="Crack",
        severity="Medium",
        priority_score=50,
        status="NEW",
        latitude=28.613900,
        longitude=77.209000,
        first_detected_at=now,
        last_detected_at=now,
    )
    db_session.add(inc)
    db_session.commit()

    obs = models.Observation(
        incident_id=inc.id,
        edge_event_id="EVT-001",
        bus_id="BUS-01",
        route_id="ROUTE-RED",
        timestamp=now,
        latitude=28.613900,
        longitude=77.209000,
        confidence=0.8
    )
    db_session.add(obs)
    db_session.commit()

    # Same bus 1 second later -> rapid duplicate (cooldown 2.0s)
    is_dup = is_rapid_duplicate_observation(
        db_session, inc.id, "BUS-01", now + timedelta(seconds=1.0), cooldown_seconds=2.0
    )
    assert is_dup is True

    # Different bus -> not duplicate
    diff_bus = is_rapid_duplicate_observation(
        db_session, inc.id, "BUS-02", now + timedelta(seconds=1.0), cooldown_seconds=2.0
    )
    assert diff_bus is False

    # Same bus after 3 seconds -> not duplicate
    after_cooldown = is_rapid_duplicate_observation(
        db_session, inc.id, "BUS-01", now + timedelta(seconds=3.0), cooldown_seconds=2.0
    )
    assert after_cooldown is False


# ---------------------------------------------------------------------------
# Severity & Escalation Tests
# ---------------------------------------------------------------------------
def test_calculate_base_severity_rules():
    assert calculate_base_severity(0.85) == "High"
    assert calculate_base_severity(0.92) == "High"
    assert calculate_base_severity(0.70) == "Medium"
    assert calculate_base_severity(0.65) == "Medium"
    assert calculate_base_severity(0.64) == "Low"
    assert calculate_base_severity(0.40) == "Low"


def test_escalate_tier():
    assert escalate_tier("Low", 1) == "Medium"
    assert escalate_tier("Medium", 1) == "High"
    assert escalate_tier("High", 1) == "Critical"
    assert escalate_tier("Critical", 1) == "Critical"  # Capped at Critical


def test_evaluate_incident_severity_multi_bus():
    # Single bus -> stays Medium
    s1 = evaluate_incident_severity(initial_severity="Medium", confirmation_count=1, unique_bus_count=1)
    assert s1 == "Medium"

    # Multi-bus (2 buses) -> escalates from Medium to High
    s2 = evaluate_incident_severity(initial_severity="Medium", confirmation_count=2, unique_bus_count=2)
    assert s2 == "High"

    # Multi-bus starting from High -> escalates to Critical
    s3 = evaluate_incident_severity(initial_severity="High", confirmation_count=2, unique_bus_count=2)
    assert s3 == "Critical"


def test_priority_score_calculation():
    # Pothole (base 70) with 0.9 confidence -> 63
    p1 = compute_priority_score("Pothole", 0.90, confirmation_count=1, unique_bus_count=1)
    assert p1 == 63

    # With repeat confirmation (>=3) -> +10 points
    p2 = compute_priority_score("Pothole", 0.90, confirmation_count=3, unique_bus_count=1)
    assert p2 == 73

    # With multi-bus (>=2) -> +15 points
    p3 = compute_priority_score("Pothole", 0.90, confirmation_count=3, unique_bus_count=2)
    assert p3 == 88


# ---------------------------------------------------------------------------
# Status Workflow & Event Fusion Tests
# ---------------------------------------------------------------------------
def test_valid_status_transitions(db_session):
    now = datetime.now(timezone.utc)
    inc = models.Incident(
        incident_id="INC-STATE01",
        anomaly_type="Pothole",
        severity="High",
        priority_score=80,
        status="NEW",
        latitude=28.613900,
        longitude=77.209000,
        first_detected_at=now,
        last_detected_at=now,
    )
    db_session.add(inc)
    db_session.commit()

    # NEW -> VERIFIED
    inc = transition_incident_status(db_session, inc, "VERIFIED", notes="Verified by operator")
    assert inc.status == "VERIFIED"
    assert len(inc.status_history) == 1
    assert inc.status_history[0].to_status == "VERIFIED"

    # VERIFIED -> ASSIGNED
    inc = transition_incident_status(db_session, inc, "ASSIGNED", notes="Assigned to Road Crew A")
    assert inc.status == "ASSIGNED"

    # ASSIGNED -> IN_PROGRESS
    inc = transition_incident_status(db_session, inc, "IN_PROGRESS", notes="Repair crew dispatched")
    assert inc.status == "IN_PROGRESS"

    # IN_PROGRESS -> RESOLVED
    inc = transition_incident_status(db_session, inc, "RESOLVED", notes="Pothole patched")
    assert inc.status == "RESOLVED"

    # Invalid: RESOLVED -> NEW should raise ValueError
    with pytest.raises(ValueError):
        transition_incident_status(db_session, inc, "NEW")


def test_fuse_edge_event_creates_new_incident(db_session):
    event_payload = schemas.EdgeEventCreate(
        edge_event_id="EVT-ORIG-01",
        bus_id="BUS-01",
        route_id="ROUTE-RED",
        anomaly_type="Pothole",
        confidence=0.88,
        latitude=28.6329,
        longitude=77.2195,
        speed_kmh=35.0,
    )

    inc = fuse_edge_event(db_session, event_payload, image_url="/static/snapshots/pothole1.jpg")
    assert inc.id is not None
    assert inc.status == "NEW"
    assert inc.confirmation_count == 1
    assert inc.unique_bus_count == 1
    assert inc.primary_image_url == "/static/snapshots/pothole1.jpg"
    assert len(inc.observations) == 1
    assert inc.observations[0].bus_id == "BUS-01"
    assert len(inc.status_history) == 1
    assert inc.status_history[0].to_status == "NEW"


def test_fuse_edge_event_deduplication_and_multi_bus_auto_verify(db_session):
    # Observation 1 from BUS-01
    evt1 = schemas.EdgeEventCreate(
        edge_event_id="EVT-B1-01",
        bus_id="BUS-01",
        route_id="ROUTE-RED",
        anomaly_type="Pothole",
        confidence=0.75,
        latitude=28.632900,
        longitude=77.219500,
        speed_kmh=30.0,
    )
    inc = fuse_edge_event(db_session, evt1)
    assert inc.confirmation_count == 1
    assert inc.unique_bus_count == 1
    assert inc.status == "NEW"
    assert inc.severity == "Medium"

    # Observation 2 from BUS-02 near the same location (~3m away)
    evt2 = schemas.EdgeEventCreate(
        edge_event_id="EVT-B2-01",
        bus_id="BUS-02",
        route_id="ROUTE-BLUE",
        anomaly_type="Pothole",
        confidence=0.80,
        latitude=28.632925,
        longitude=77.219520,
        speed_kmh=28.0,
    )
    inc_fused = fuse_edge_event(db_session, evt2)
    assert inc_fused.id == inc.id  # Same incident!
    assert inc_fused.confirmation_count == 2
    assert inc_fused.unique_bus_count == 2
    # Auto-verification triggered on multi-bus!
    assert inc_fused.status == "VERIFIED"
    # Severity escalated Medium -> High on multi-bus!
    assert inc_fused.severity == "High"
    assert len(inc_fused.observations) == 2
