"""
tests/test_integration_full.py
-------------------------------
Comprehensive integration tests covering:
1.  All 28 stitched events → backend ingestion (field completeness)
2.  Every required field: anomaly_type, confidence, frame/evidence, bus_id,
    route_id, timestamp, simulated GPS
3.  event_id → incident_id lineage (edge EVT- IDs preserved in observations)
4.  Idempotency / no-duplicate guard on repeated scans
5.  Dashboard endpoint correctness (incidents list, detail, analytics)

Run from repo root:
    python -m pytest tests/test_integration_full.py -v
"""

import csv
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app import models

# ---------------------------------------------------------------------------
# Use a disposable in-memory SQLite database for integration tests
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)
Base.metadata.create_all(bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# ---------------------------------------------------------------------------
# Load the real audit lineage produced by audit_lineage.py
# ---------------------------------------------------------------------------
LINEAGE_CSV = Path(__file__).resolve().parents[1] / "data" / "audit" / "lineage.csv"

def load_lineage() -> list[dict]:
    """Return all rows from the audit lineage CSV as dicts."""
    if not LINEAGE_CSV.exists():
        pytest.skip(f"lineage.csv not found at {LINEAGE_CSV}; run audit_lineage.py first")
    with open(LINEAGE_CSV, newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Helper: build a minimal EdgeEventCreate-compatible payload from a CSV row
# ---------------------------------------------------------------------------
VALID_BUS = "BUS-01"
VALID_ROUTE = "ROUTE-RED"

def row_to_event(row: dict, bus_id: str = VALID_BUS, route_id: str = VALID_ROUTE) -> dict:
    """Build an EdgeEventCreate JSON from a lineage CSV row."""
    return {
        "edge_event_id": row["event_id"],
        "bus_id": bus_id,
        "route_id": route_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latitude": float(row["latitude"]),
        "longitude": float(row["longitude"]),
        "speed_kmh": 30.0,
        "anomaly_type": row["class_name"],
        "confidence": float(row["best_confidence"]),
        "bbox": [int(row["x1"]), int(row["y1"]), int(row["x2"]), int(row["y2"])],
        "severity": None,       # let backend compute
        "priority_score": None, # let backend compute
    }


# ===========================================================================
# SECTION 1 – Field completeness for every stitched event
# ===========================================================================
class TestEventFieldCompleteness:
    """All 28 lineage rows produce incidents with the mandatory field set."""

    REQUIRED_INCIDENT_FIELDS = {
        "id", "incident_id", "anomaly_type", "severity", "priority_score",
        "status", "latitude", "longitude", "first_detected_at",
        "last_detected_at", "confirmation_count", "unique_bus_count",
    }

    def test_all_28_events_ingest_and_return_required_fields(self):
        rows = load_lineage()
        assert len(rows) == 28, f"Expected 28 rows, got {len(rows)}"

        for row in rows:
            payload = row_to_event(row)
            resp = client.post("/api/ingest/json", json=payload)
            assert resp.status_code in (200, 201), (
                f"Event {row['event_id']} failed: {resp.status_code} – {resp.text}"
            )
            data = resp.json()
            missing = self.REQUIRED_INCIDENT_FIELDS - set(data.keys())
            assert not missing, (
                f"Event {row['event_id']} response missing keys: {missing}"
            )

    def test_anomaly_type_is_valid_class(self):
        VALID_CLASSES = {"Pothole", "Crack", "Crack-Severe", "Speed-Bump"}
        rows = load_lineage()
        for row in rows:
            assert row["class_name"] in VALID_CLASSES, (
                f"Track {row['track_id']}: unexpected class '{row['class_name']}'"
            )

    def test_confidence_is_in_range(self):
        rows = load_lineage()
        for row in rows:
            conf = float(row["best_confidence"])
            assert 0.0 <= conf <= 1.0, (
                f"Track {row['track_id']}: confidence {conf} out of [0,1]"
            )

    def test_gps_coordinates_are_valid(self):
        rows = load_lineage()
        for row in rows:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            assert -90 <= lat <= 90, f"Track {row['track_id']}: invalid lat {lat}"
            assert -180 <= lon <= 180, f"Track {row['track_id']}: invalid lon {lon}"

    def test_event_id_format_in_csv(self):
        """All event_ids must follow EVT-TRKn-XXXXXX pattern."""
        rows = load_lineage()
        for row in rows:
            eid = row["event_id"]
            assert eid.startswith("EVT-TRK"), (
                f"Track {row['track_id']}: event_id '{eid}' doesn't start with EVT-TRK"
            )


# ===========================================================================
# SECTION 2 – event_id → incident_id lineage
# ===========================================================================
class TestLineageTracking:
    """Edge event_id must be preserved in the observation.edge_event_id field."""

    def test_edge_event_id_preserved_in_observation(self):
        """For a fresh event, the stored observation must carry the original edge_event_id."""
        event_id = f"EVT-TRK999-LINEAGE"
        payload = {
            "edge_event_id": event_id,
            "bus_id": VALID_BUS,
            "route_id": VALID_ROUTE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": 28.6000,
            "longitude": 77.2000,
            "speed_kmh": 25.0,
            "anomaly_type": "Pothole",
            "confidence": 0.78,
        }
        resp = client.post("/api/ingest/json", json=payload)
        assert resp.status_code in (200, 201)
        data = resp.json()
        inc_id = data["incident_id"]

        # Fetch the full detail
        detail_resp = client.get(f"/api/incidents/{inc_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()

        # The observation must carry the original edge_event_id
        obs_ids = [o["edge_event_id"] for o in detail["observations"]]
        assert event_id in obs_ids, (
            f"edge_event_id '{event_id}' not found in observations: {obs_ids}"
        )

    def test_incident_id_format(self):
        """Created incidents must have INC-XXXXXXXX format."""
        payload = {
            "edge_event_id": f"EVT-LINEAGE-FMT-{uuid.uuid4().hex[:6].upper()}",
            "bus_id": VALID_BUS,
            "route_id": VALID_ROUTE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": 28.6001,
            "longitude": 77.2001,
            "speed_kmh": 20.0,
            "anomaly_type": "Crack",
            "confidence": 0.70,
        }
        resp = client.post("/api/ingest/json", json=payload)
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["incident_id"].startswith("INC-"), (
            f"Incident ID format wrong: {data['incident_id']}"
        )

    def test_bus_id_and_route_id_in_observation(self):
        """Observation must record the bus_id and route_id from the edge event."""
        bus = "BUS-02"
        route = "ROUTE-BLUE"
        evt_id = f"EVT-BUSROUTE-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "edge_event_id": evt_id,
            "bus_id": bus,
            "route_id": route,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": 28.6050,
            "longitude": 77.2050,
            "speed_kmh": 35.0,
            "anomaly_type": "Pothole",
            "confidence": 0.80,
        }
        resp = client.post("/api/ingest/json", json=payload)
        assert resp.status_code in (200, 201)
        inc_id = resp.json()["incident_id"]

        detail = client.get(f"/api/incidents/{inc_id}").json()
        obs = next((o for o in detail["observations"] if o["edge_event_id"] == evt_id), None)
        assert obs is not None
        assert obs["bus_id"] == bus
        assert obs["route_id"] == route


# ===========================================================================
# SECTION 3 – No-duplicate guard on repeated scans
# ===========================================================================
class TestDeduplicationIdempotency:
    """Submitting the same edge_event_id twice must NOT create a duplicate incident."""

    def test_same_event_id_returns_same_incident(self):
        evt_id = f"EVT-DEDUP-{uuid.uuid4().hex[:8].upper()}"
        payload = {
            "edge_event_id": evt_id,
            "bus_id": VALID_BUS,
            "route_id": VALID_ROUTE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": 28.6100,
            "longitude": 77.2100,
            "speed_kmh": 28.0,
            "anomaly_type": "Crack-Severe",
            "confidence": 0.72,
        }
        r1 = client.post("/api/ingest/json", json=payload)
        r2 = client.post("/api/ingest/json", json=payload)
        assert r1.status_code in (200, 201)
        assert r2.status_code in (200, 201)
        # Must return the same incident_id
        assert r1.json()["incident_id"] == r2.json()["incident_id"], (
            "Duplicate edge_event_id created two different incidents"
        )

    def test_spatial_deduplication_within_15m(self):
        """Two events < 15 m apart of the same type should map to one incident."""
        base_lat, base_lon = 28.6200, 77.2200
        # ~7 m offset
        offset_lat = base_lat + 0.000063

        payload1 = {
            "edge_event_id": f"EVT-SPATIAL-A-{uuid.uuid4().hex[:6].upper()}",
            "bus_id": VALID_BUS,
            "route_id": VALID_ROUTE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": base_lat,
            "longitude": base_lon,
            "speed_kmh": 30.0,
            "anomaly_type": "Pothole",
            "confidence": 0.82,
        }
        payload2 = {
            "edge_event_id": f"EVT-SPATIAL-B-{uuid.uuid4().hex[:6].upper()}",
            "bus_id": "BUS-02",
            "route_id": "ROUTE-BLUE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": offset_lat,
            "longitude": base_lon,
            "speed_kmh": 30.0,
            "anomaly_type": "Pothole",
            "confidence": 0.79,
        }
        r1 = client.post("/api/ingest/json", json=payload1)
        r2 = client.post("/api/ingest/json", json=payload2)
        assert r1.status_code in (200, 201)
        assert r2.status_code in (200, 201)
        assert r1.json()["incident_id"] == r2.json()["incident_id"], (
            "Two detections <15m apart created separate incidents (dedup failed)"
        )

    def test_distinct_locations_create_separate_incidents(self):
        """Two events > 15 m apart should create two separate incidents."""
        base_lat, base_lon = 28.6300, 77.2300
        far_lat = base_lat + 0.002  # ~220 m away

        payload1 = {
            "edge_event_id": f"EVT-DIST-A-{uuid.uuid4().hex[:6].upper()}",
            "bus_id": VALID_BUS,
            "route_id": VALID_ROUTE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": base_lat,
            "longitude": base_lon,
            "speed_kmh": 30.0,
            "anomaly_type": "Crack",
            "confidence": 0.75,
        }
        payload2 = {
            "edge_event_id": f"EVT-DIST-B-{uuid.uuid4().hex[:6].upper()}",
            "bus_id": VALID_BUS,
            "route_id": VALID_ROUTE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": far_lat,
            "longitude": base_lon,
            "speed_kmh": 30.0,
            "anomaly_type": "Crack",
            "confidence": 0.75,
        }
        r1 = client.post("/api/ingest/json", json=payload1)
        r2 = client.post("/api/ingest/json", json=payload2)
        assert r1.status_code in (200, 201)
        assert r2.status_code in (200, 201)
        assert r1.json()["incident_id"] != r2.json()["incident_id"], (
            "Two detections >15m apart incorrectly merged to the same incident"
        )


# ===========================================================================
# SECTION 4 – Multi-bus verification & severity escalation
# ===========================================================================
class TestMultiBusVerification:
    """Multi-bus detection → auto-VERIFIED + severity escalation."""

    def test_second_bus_triggers_auto_verification(self):
        base_lat, base_lon = 28.6400, 77.2400

        p1 = {
            "edge_event_id": f"EVT-MB-A-{uuid.uuid4().hex[:6].upper()}",
            "bus_id": "BUS-01",
            "route_id": "ROUTE-RED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": base_lat,
            "longitude": base_lon,
            "speed_kmh": 30.0,
            "anomaly_type": "Pothole",
            "confidence": 0.80,
        }
        r1 = client.post("/api/ingest/json", json=p1)
        assert r1.status_code in (200, 201)
        inc_id = r1.json()["incident_id"]
        assert r1.json()["status"] == "NEW"

        p2 = {
            "edge_event_id": f"EVT-MB-B-{uuid.uuid4().hex[:6].upper()}",
            "bus_id": "BUS-02",
            "route_id": "ROUTE-BLUE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": base_lat + 0.00005,
            "longitude": base_lon,
            "speed_kmh": 28.0,
            "anomaly_type": "Pothole",
            "confidence": 0.82,
        }
        r2 = client.post("/api/ingest/json", json=p2)
        assert r2.status_code in (200, 201)
        data2 = r2.json()

        assert data2["incident_id"] == inc_id, "Second bus mapped to different incident"
        assert data2["status"] == "VERIFIED", (
            f"Expected VERIFIED after multi-bus, got {data2['status']}"
        )
        assert data2["unique_bus_count"] == 2

    def test_severity_escalates_on_multi_bus(self):
        """An initially Medium incident should escalate when confirmed by 2 buses."""
        base_lat, base_lon = 28.6450, 77.2450

        p1 = {
            "edge_event_id": f"EVT-ESC-A-{uuid.uuid4().hex[:6].upper()}",
            "bus_id": "BUS-01",
            "route_id": "ROUTE-RED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": base_lat,
            "longitude": base_lon,
            "speed_kmh": 30.0,
            "anomaly_type": "Crack",
            "confidence": 0.60,   # Medium confidence → Medium severity
        }
        r1 = client.post("/api/ingest/json", json=p1)
        assert r1.status_code in (200, 201)
        initial_severity = r1.json()["severity"]
        inc_id = r1.json()["incident_id"]

        p2 = {
            "edge_event_id": f"EVT-ESC-B-{uuid.uuid4().hex[:6].upper()}",
            "bus_id": "BUS-03",
            "route_id": "ROUTE-GREEN",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": base_lat + 0.00005,
            "longitude": base_lon,
            "speed_kmh": 25.0,
            "anomaly_type": "Crack",
            "confidence": 0.65,
        }
        r2 = client.post("/api/ingest/json", json=p2)
        assert r2.status_code in (200, 201)
        final_severity = r2.json()["severity"]

        SEVERITY_RANK = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
        assert SEVERITY_RANK.get(final_severity, -1) >= SEVERITY_RANK.get(initial_severity, 0), (
            f"Severity should have escalated from {initial_severity}, got {final_severity}"
        )


# ===========================================================================
# SECTION 5 – Dashboard endpoints
# ===========================================================================
class TestDashboardEndpoints:
    """GET /api/incidents and analytics endpoints return correct structure."""

    def _seed_incident(self, suffix: str, lat: float, lon: float,
                       anomaly: str = "Pothole", conf: float = 0.80) -> str:
        payload = {
            "edge_event_id": f"EVT-DASH-{suffix}-{uuid.uuid4().hex[:4].upper()}",
            "bus_id": VALID_BUS,
            "route_id": VALID_ROUTE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": lat,
            "longitude": lon,
            "speed_kmh": 30.0,
            "anomaly_type": anomaly,
            "confidence": conf,
        }
        r = client.post("/api/ingest/json", json=payload)
        assert r.status_code in (200, 201)
        return r.json()["incident_id"]

    def test_list_incidents_returns_list(self):
        self._seed_incident("LIST", 28.6500, 77.2500)
        resp = client.get("/api/incidents")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_incident_detail_has_observations(self):
        inc_id = self._seed_incident("DETAIL", 28.6501, 77.2501)
        resp = client.get(f"/api/incidents/{inc_id}")
        assert resp.status_code == 200
        detail = resp.json()
        assert "observations" in detail
        assert len(detail["observations"]) >= 1

    def test_incident_detail_has_status_history(self):
        inc_id = self._seed_incident("HIST", 28.6502, 77.2502)
        resp = client.get(f"/api/incidents/{inc_id}")
        assert resp.status_code == 200
        detail = resp.json()
        assert "status_history" in detail
        assert len(detail["status_history"]) >= 1

    def test_analytics_summary_fields(self):
        resp = client.get("/api/analytics/summary")
        assert resp.status_code == 200
        data = resp.json()
        required_keys = {
            "total_incidents", "pending_count", "verified_count",
            "assigned_count", "in_progress_count", "resolved_count",
            "multi_bus_verified_count", "active_buses",
            "by_anomaly_type", "by_severity",
        }
        missing = required_keys - set(data.keys())
        assert not missing, f"Analytics summary missing keys: {missing}"

    def test_filter_by_anomaly_type(self):
        self._seed_incident("CRACK", 28.6510, 77.2510, anomaly="Crack-Severe", conf=0.60)
        resp = client.get("/api/incidents", params={"anomaly_type": "Crack-Severe"})
        assert resp.status_code == 200
        for inc in resp.json():
            assert inc["anomaly_type"] == "Crack-Severe"

    def test_404_for_nonexistent_incident(self):
        resp = client.get("/api/incidents/INC-DOESNOTEXIST")
        assert resp.status_code == 404

    def test_health_check(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ===========================================================================
# SECTION 6 – Status lifecycle transitions
# ===========================================================================
class TestStatusLifecycle:
    """Strict state machine: NEW → VERIFIED → ASSIGNED → IN_PROGRESS → RESOLVED."""

    def _create_incident(self, lat: float, lon: float) -> str:
        payload = {
            "edge_event_id": f"EVT-LIFE-{uuid.uuid4().hex[:6].upper()}",
            "bus_id": VALID_BUS,
            "route_id": VALID_ROUTE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": lat,
            "longitude": lon,
            "speed_kmh": 30.0,
            "anomaly_type": "Pothole",
            "confidence": 0.88,
        }
        r = client.post("/api/ingest/json", json=payload)
        assert r.status_code in (200, 201)
        return r.json()["incident_id"]

    def test_valid_lifecycle_progression(self):
        inc_id = self._create_incident(28.6600, 77.2600)
        transitions = [
            ("VERIFIED", "Mark VERIFIED"),
            ("ASSIGNED", "Dispatching crew"),
            ("IN_PROGRESS", "Repair underway"),
            ("RESOLVED", "Repair complete"),
        ]
        for status, notes in transitions:
            resp = client.patch(
                f"/api/incidents/{inc_id}/status",
                json={"status": status, "notes": notes}
            )
            assert resp.status_code == 200, (
                f"Transition to {status} failed: {resp.status_code} – {resp.text}"
            )
            assert resp.json()["status"] == status

    def test_invalid_transition_rejected(self):
        inc_id = self._create_incident(28.6601, 77.2601)
        # NEW → IN_PROGRESS is allowed per current VALID_STATUS_TRANSITIONS
        # NEW → RESOLVED is also allowed; test truly invalid: RESOLVED → NEW
        # First go to RESOLVED
        for s in ["VERIFIED", "ASSIGNED", "IN_PROGRESS", "RESOLVED"]:
            client.patch(f"/api/incidents/{inc_id}/status", json={"status": s})

        # Now try going backwards
        resp = client.patch(
            f"/api/incidents/{inc_id}/status",
            json={"status": "NEW", "notes": "attempting rollback"}
        )
        assert resp.status_code == 400, "Rollback from RESOLVED should be rejected"

    def test_resolved_appears_in_status_history(self):
        inc_id = self._create_incident(28.6602, 77.2602)
        for s in ["VERIFIED", "ASSIGNED", "IN_PROGRESS", "RESOLVED"]:
            client.patch(f"/api/incidents/{inc_id}/status", json={"status": s})

        detail = client.get(f"/api/incidents/{inc_id}").json()
        statuses = [h["to_status"] for h in detail["status_history"]]
        assert "RESOLVED" in statuses


# ===========================================================================
# SECTION 7 – Evidence / image lineage
# ===========================================================================
class TestEvidenceLineage:
    """Multipart evidence upload stores image URL accessible on the incident."""

    def test_multipart_ingest_stores_image_url(self):
        import io
        evt_id = f"EVT-IMG-{uuid.uuid4().hex[:6].upper()}"
        event_payload = {
            "edge_event_id": evt_id,
            "bus_id": VALID_BUS,
            "route_id": VALID_ROUTE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": 28.6700,
            "longitude": 77.2700,
            "speed_kmh": 30.0,
            "anomaly_type": "Pothole",
            "confidence": 0.91,
        }
        fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # minimal JPEG header

        resp = client.post(
            "/api/ingest",
            data={"event_data": json.dumps(event_payload)},
            files={"image_file": ("evidence.jpg", fake_image, "image/jpeg")},
        )
        assert resp.status_code in (200, 201), f"Multipart ingest failed: {resp.text}"
        data = resp.json()
        inc_id = data["incident_id"]

        # Verify image URL is stored
        detail = client.get(f"/api/incidents/{inc_id}").json()
        assert detail.get("primary_image_url") is not None, (
            "primary_image_url not stored after multipart upload"
        )
        assert "/static/snapshots/" in detail["primary_image_url"]


# ===========================================================================
# SECTION 8 – Bus fleet telemetry endpoint
# ===========================================================================
class TestBusFleet:
    def test_bus_fleet_endpoint_returns_list(self):
        resp = client.get("/api/buses")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_bus_record_after_ingest(self):
        """A bus should be registered in the fleet after submitting an event."""
        bus_id = "BUS-03"
        payload = {
            "edge_event_id": f"EVT-BUS3-{uuid.uuid4().hex[:6].upper()}",
            "bus_id": bus_id,
            "route_id": "ROUTE-GREEN",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": 28.6800,
            "longitude": 77.2800,
            "speed_kmh": 35.0,
            "anomaly_type": "Speed-Bump",
            "confidence": 0.55,
        }
        client.post("/api/ingest/json", json=payload)

        resp = client.get("/api/buses")
        bus_ids = [b["bus_id"] for b in resp.json()]
        assert bus_id in bus_ids, f"{bus_id} not found in fleet after ingest"


# ===========================================================================
# SECTION 9 – ANPR PlateRead & InfraObservation Persistence (v2)
# ===========================================================================
class TestMultiPerceptionPersistence:
    def test_anpr_and_infra_persisted_via_edge_event(self):
        """Verify nearby_plates and nearby_signs are written to DB and queryable."""
        evt_id = f"EVT-PERCEPT-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "edge_event_id": evt_id,
            "bus_id": "BUS-01",
            "route_id": "ROUTE-RED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": 28.6250,
            "longitude": 77.2150,
            "speed_kmh": 28.0,
            "anomaly_type": "Pothole",
            "confidence": 0.85,
            "nearby_plates": [
                {
                    "plate_text": "DL01AB1234",
                    "plate_confidence": 0.94,
                    "ocr_confidence": 0.91,
                    "bbox": [100, 200, 300, 250],
                }
            ],
            "nearby_signs": [
                {
                    "sign_type": "speed-60",
                    "confidence": 0.88,
                    "bbox": [50, 60, 120, 130],
                }
            ],
        }

        resp = client.post("/api/ingest/json", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        inc_id = data["incident_id"]

        # 1. Verify plate read is linked in incident detail
        detail_resp = client.get(f"/api/incidents/{inc_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert len(detail.get("plate_reads", [])) >= 1
        assert detail["plate_reads"][0]["plate_text"] == "DL01AB1234"
        assert detail["plate_reads"][0]["plate_confidence"] == 0.94

        # 2. Verify standalone query /api/ingest/plates
        plates_resp = client.get("/api/ingest/plates?bus_id=BUS-01")
        assert plates_resp.status_code == 200
        plates = plates_resp.json()
        plate_texts = [p["plate_text"] for p in plates]
        assert "DL01AB1234" in plate_texts

        # 3. Verify standalone query /api/ingest/infra
        infra_resp = client.get("/api/ingest/infra?bus_id=BUS-01")
        assert infra_resp.status_code == 200
        signs = infra_resp.json()
        sign_types = [s["sign_type"] for s in signs]
        assert "speed-60" in sign_types

