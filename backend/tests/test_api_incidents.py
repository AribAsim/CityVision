import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database import Base, get_db


# Set up isolated in-memory test database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_json_creates_incident(client):
    payload = {
        "edge_event_id": "EVT-TEST-API-01",
        "bus_id": "BUS-01",
        "route_id": "ROUTE-RED",
        "anomaly_type": "Pothole",
        "confidence": 0.88,
        "latitude": 28.6329,
        "longitude": 77.2195,
        "speed_kmh": 32.0,
    }
    res = client.post("/api/ingest/json", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    assert data["anomaly_type"] == "Pothole"
    assert data["status"] == "NEW"
    assert data["confirmation_count"] == 1
    assert data["unique_bus_count"] == 1


def test_ingest_multipart_form(client):
    event_payload = {
        "edge_event_id": "EVT-TEST-MULTI-01",
        "bus_id": "BUS-02",
        "route_id": "ROUTE-BLUE",
        "anomaly_type": "Crack-Severe",
        "confidence": 0.90,
        "latitude": 28.6139,
        "longitude": 77.2090,
    }
    # Simulate multipart upload
    res = client.post(
        "/api/ingest",
        data={"event_data": json.dumps(event_payload)},
        files={"image_file": ("test_snapshot.jpg", b"fake-jpg-binary-bytes", "image/jpeg")},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["anomaly_type"] == "Crack-Severe"
    assert data["primary_image_url"] is not None
    assert "/static/snapshots/" in data["primary_image_url"]


def test_multi_bus_ingestion_and_incident_lifecycle(client):
    # 1. Ingest observation 1 from BUS-01
    p1 = {
        "edge_event_id": "EVT-B1",
        "bus_id": "BUS-01",
        "route_id": "ROUTE-RED",
        "anomaly_type": "Pothole",
        "confidence": 0.70,
        "latitude": 28.632900,
        "longitude": 77.219500,
    }
    r1 = client.post("/api/ingest/json", json=p1)
    assert r1.status_code == 201
    inc1 = r1.json()
    inc_id = inc1["incident_id"]
    assert inc1["status"] == "NEW"
    assert inc1["unique_bus_count"] == 1

    # 2. Ingest observation 2 from BUS-02 at same location (~5m away)
    p2 = {
        "edge_event_id": "EVT-B2",
        "bus_id": "BUS-02",
        "route_id": "ROUTE-BLUE",
        "anomaly_type": "Pothole",
        "confidence": 0.82,
        "latitude": 28.632940,
        "longitude": 77.219520,
    }
    r2 = client.post("/api/ingest/json", json=p2)
    assert r2.status_code == 201
    inc2 = r2.json()
    assert inc2["incident_id"] == inc_id  # Clustered into same incident!
    assert inc2["unique_bus_count"] == 2
    assert inc2["status"] == "VERIFIED"   # Auto-verified by multi-bus!

    # 3. GET /api/incidents list
    list_res = client.get("/api/incidents")
    assert list_res.status_code == 200
    incidents = list_res.json()
    assert len(incidents) == 1
    assert incidents[0]["incident_id"] == inc_id

    # 4. GET /api/incidents/{id} detail
    detail_res = client.get(f"/api/incidents/{inc_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["observations"]) == 2
    assert len(detail["status_history"]) >= 2  # NEW -> VERIFIED

    # 5. PATCH /api/incidents/{id}/status - valid transition: VERIFIED -> ASSIGNED
    patch_res = client.patch(
        f"/api/incidents/{inc_id}/status",
        json={"status": "ASSIGNED", "notes": "Dispatched maintenance vehicle"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "ASSIGNED"

    # 6. Valid transition: ASSIGNED -> IN_PROGRESS
    patch_prog = client.patch(
        f"/api/incidents/{inc_id}/status",
        json={"status": "IN_PROGRESS"}
    )
    assert patch_prog.status_code == 200
    assert patch_prog.json()["status"] == "IN_PROGRESS"

    # 7. Valid transition: IN_PROGRESS -> RESOLVED
    patch_res2 = client.patch(
        f"/api/incidents/{inc_id}/status",
        json={"status": "RESOLVED", "notes": "Road repair complete"}
    )
    assert patch_res2.status_code == 200
    assert patch_res2.json()["status"] == "RESOLVED"

    # 8. Invalid transition: RESOLVED -> NEW should fail with 400
    bad_patch = client.patch(
        f"/api/incidents/{inc_id}/status",
        json={"status": "NEW"}
    )
    assert bad_patch.status_code == 400
    assert "Invalid status transition" in bad_patch.json()["detail"]


def test_analytics_summary_endpoint(client):
    # Ingest one pothole
    client.post("/api/ingest/json", json={
        "edge_event_id": "EVT-ANALYTICS-01",
        "bus_id": "BUS-01",
        "route_id": "ROUTE-RED",
        "anomaly_type": "Pothole",
        "confidence": 0.88,
        "latitude": 28.6329,
        "longitude": 77.2195,
    })

    res = client.get("/api/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_incidents"] == 1
    assert data["pending_count"] == 1  # NEW
    assert data["active_buses"] >= 1
    assert "Pothole" in data["by_anomaly_type"]
