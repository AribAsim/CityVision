"""
Tests for Telemetry router and Reports router.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


class TestTelemetryRouter:
    def test_density_post_and_get(self):
        payload = {
            "segment_key": "ROUTE-RED:28.613:77.209",
            "route_id": "ROUTE-RED",
            "bus_id": "BUS-01",
            "lat": 28.6139,
            "lon": 77.2090,
            "count_person": 3,
            "count_car": 15,
            "count_bus": 2,
            "count_truck": 1,
            "total_count": 21,
        }
        res = client.post("/api/telemetry/density", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["segment_key"] == payload["segment_key"]
        assert data["congestion_index"] > 0
        assert data["total_count"] == 21

        # GET density list
        res_get = client.get("/api/telemetry/density?route_id=ROUTE-RED")
        assert res_get.status_code == 200
        items = res_get.json()
        assert len(items) >= 1
        assert any(it["segment_key"] == payload["segment_key"] for it in items)

    def test_bottlenecks_endpoint(self):
        res = client.get("/api/telemetry/density/bottlenecks?top_n=5")
        assert res.status_code == 200
        bottlenecks = res.json()
        assert isinstance(bottlenecks, list)

    def test_route_delay_endpoint(self):
        res = client.get("/api/telemetry/density/delay?route_id=ROUTE-RED")
        assert res.status_code == 200
        delay_info = res.json()
        assert "baseline_minutes" in delay_info
        assert "actual_minutes" in delay_info
        assert "delay_minutes" in delay_info

    def test_od_endpoint(self):
        res = client.get("/api/telemetry/density/od")
        assert res.status_code == 200
        assert isinstance(res.json(), list)


class TestReportsRouter:
    def test_infra_deficiency_json(self):
        res = client.get("/api/reports/infrastructure-deficiency")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "deficiency_score" in data[0]

    def test_infra_deficiency_pdf(self):
        res = client.get("/api/reports/infrastructure-deficiency.pdf")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/pdf"
        assert len(res.content) > 1000

    def test_route_performance_json(self):
        res = client.get("/api/reports/route-performance?route_id=ROUTE-RED")
        assert res.status_code == 200
        data = res.json()
        assert "baseline_minutes" in data
        assert "delay_minutes" in data

    def test_route_performance_pdf(self):
        res = client.get("/api/reports/route-performance.pdf?route_id=ROUTE-RED")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/pdf"
        assert len(res.content) > 1000
