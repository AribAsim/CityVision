"""
Unit tests for edge/behavior_analyzer.py, edge/density_accumulator.py,
and edge/waterlogging_heuristic.py.
"""

from collections import deque
import numpy as np
import pytest

from edge.behavior_analyzer import (
    ANPR_TRIGGER_FRAMES,
    VRU_PROXIMITY_PX,
    check_hit_and_run,
    should_run_anpr,
    vru_proximity_risk,
)
from edge.density_accumulator import DensityAccumulator, compute_segment_key
from edge.waterlogging_heuristic import detect_waterlogging


class TestDensityAccumulator:
    def test_compute_segment_key(self):
        key = compute_segment_key("ROUTE-RED", 28.6139, 77.2090)
        assert key.startswith("ROUTE-RED:")
        assert "28.610" in key or "28.613" in key or "28.615" in key

    def test_accumulator_tracks_counts_and_flushes(self):
        acc = DensityAccumulator()
        seg_key = "ROUTE-RED:28.610:77.205"

        mock_detections = [
            {"class_name": "car", "confidence": 0.9, "bbox": [10, 10, 50, 50]},
            {"class_name": "car", "confidence": 0.85, "bbox": [60, 10, 100, 50]},
            {"class_name": "motorcycle", "confidence": 0.8, "bbox": [110, 10, 140, 50]},
            {"class_name": "person", "confidence": 0.75, "bbox": [150, 10, 170, 50]},
        ]
        acc.add_frame(seg_key, mock_detections)

        payload = acc.flush(
            segment_key=seg_key,
            lat=28.613,
            lon=77.209,
            route_id="ROUTE-RED",
            bus_id="BUS-01",
        )

        assert payload["segment_key"] == seg_key
        assert payload["count_car"] == 2
        assert payload["count_motorcycle"] == 1
        assert payload["count_person"] == 1
        assert payload["total_count"] == 4

        # Verify state is cleared
        assert acc.counts["car"] == 0
        assert acc.frame_count == 0


class TestBehaviorAnalyzer:
    def test_should_run_anpr(self):
        assert should_run_anpr(None, 100) is False
        assert should_run_anpr(100, 100) is True
        assert should_run_anpr(100, 100 + ANPR_TRIGGER_FRAMES) is True
        assert should_run_anpr(100, 100 + ANPR_TRIGGER_FRAMES + 1) is False
        assert should_run_anpr(100, 99) is False

    def test_vru_proximity_risk_triggered(self):
        # Car and pedestrian close together in pixel space
        vehicles = [{"class_name": "car", "confidence": 0.9, "bbox": [100, 100, 200, 200]}]
        vrus = [{"class_name": "person", "confidence": 0.85, "bbox": [120, 110, 140, 170]}]
        class MockLoc:
            latitude = 28.61
            longitude = 77.20

        risk = vru_proximity_risk(vehicles + vrus, [], MockLoc())
        assert risk is not None
        assert risk["event_type"] == "VRU-Proximity"
        assert risk["candidate_only"] is True
        assert "pixel_distance" in risk["details"]

    def test_vru_proximity_risk_not_triggered_when_far(self):
        # Car and pedestrian far apart
        vehicles = [{"class_name": "car", "confidence": 0.9, "bbox": [10, 10, 50, 50]}]
        vrus = [{"class_name": "person", "confidence": 0.85, "bbox": [500, 500, 530, 560]}]
        class MockLoc:
            latitude = 28.61
            longitude = 77.20

        risk = vru_proximity_risk(vehicles + vrus, [], MockLoc())
        assert risk is None

    def test_hit_and_run_candidate_detection(self):
        history = deque(maxlen=60)
        # Frames 0-10: Vehicle and Pedestrian close together
        for f in range(10):
            history.append({
                "frame_idx": f,
                "tracks": [
                    {"track_id": 1, "class_name": "person", "bbox": [100, 100, 120, 150]},
                    {"track_id": 2, "class_name": "car", "bbox": [110, 100, 180, 160]},
                ]
            })
        # Frames 11-20: Pedestrian abruptly lost (disappeared), car continues moving
        for f in range(10, 20):
            history.append({
                "frame_idx": f,
                "tracks": [
                    {"track_id": 2, "class_name": "car", "bbox": [110 + (f * 10), 100, 180 + (f * 10), 160]},
                ]
            })

        candidate = check_hit_and_run(history)
        assert candidate is not None
        assert candidate["event_type"] == "HitAndRun-Candidate"
        assert candidate["candidate_only"] is True
        assert candidate["details"]["vehicle_track_id"] == 2


class TestWaterloggingHeuristic:
    def test_dry_road_does_not_trigger(self):
        # Dark non-specular asphalt
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (50, 50, 50)
        assert detect_waterlogging(frame, None) is None

    def test_large_specular_region_triggers_candidate(self):
        # Lower half has large bright specular white region
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[300:480, 100:540] = (255, 255, 255)
        result = detect_waterlogging(frame, None)
        assert result is not None
        assert result["event_type"] == "Waterlogging-Candidate"
        assert result["heuristic_only"] is True
