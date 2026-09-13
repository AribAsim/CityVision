import io
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.routers.scan import scan_jobs

client = TestClient(app)


def test_start_scan_invalid_bus_id():
    response = client.post(
        "/api/scan/start",
        data={"bus_id": "BUS-99"},
        files={"video_file": ("test.mp4", io.BytesIO(b"fake mp4 content"), "video/mp4")},
    )
    assert response.status_code == 400
    assert "Invalid bus_id" in response.json()["detail"]


def test_start_scan_invalid_file_extension():
    response = client.post(
        "/api/scan/start",
        data={"bus_id": "BUS-01"},
        files={"video_file": ("test.txt", io.BytesIO(b"not a video"), "text/plain")},
    )
    assert response.status_code == 400
    assert "Only .mp4 video files are supported" in response.json()["detail"]


def test_get_scan_status_not_found():
    response = client.get("/api/scan/status/non-existent-uuid")
    assert response.status_code == 404
    assert response.json()["detail"] == "Scan job not found"


@patch("backend.app.routers.scan.threading.Thread")
def test_start_scan_valid(mock_thread):
    mock_instance = mock_thread.return_value
    mock_instance.start.return_value = None
    response = client.post(
        "/api/scan/start",
        data={"bus_id": "BUS-01", "route_id": "ROUTE-RED"},
        files={"video_file": ("road_sample.mp4", io.BytesIO(b"sample video bytes"), "video/mp4")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PROCESSING"

    job_id = data["job_id"]
    status_resp = client.get(f"/api/scan/status/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] == "PROCESSING"
    assert status_data["events_dispatched"] == 0


def test_scan_status_reflection():
    dummy_job_id = "test-job-123"
    scan_jobs[dummy_job_id] = {
        "job_id": dummy_job_id,
        "bus_id": "BUS-02",
        "route_id": "ROUTE-BLUE",
        "filename": "demo.mp4",
        "status": "COMPLETED",
        "events_dispatched": 5,
        "error": None,
    }

    res = client.get(f"/api/scan/status/{dummy_job_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["events_dispatched"] == 5
    assert data["error"] is None
