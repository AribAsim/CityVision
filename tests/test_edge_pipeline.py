"""
edge/test_edge_pipeline.py
--------------------------
Lightweight unit test for the edge pipeline.
Does NOT require the YOLO model or a real video.
Tests severity scoring, deduplication, and event payload structure.

Run from repo root:
  python -m pytest edge/test_edge_pipeline.py -v
"""
import dataclasses
import time
from pathlib import Path

import numpy as np
import pytest

from edge.detector import ANOMALY_CLASSES, RawDetection
from edge.event_builder import (
    COOLDOWN_SECONDS,
    SPATIAL_RADIUS_M,
    EventBuilder,
    _haversine_m,
    _score_to_severity,
)
from edge.gps_simulator import GPSSimulator, LocationData
from edge.anomaly_tracker import AnomalyTracker
from edge.bus_simulator import BusSimulator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def blank_frame(w: int = 640, h: int = 480) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)


def make_detection(cls: str = "Pothole", conf: float = 0.85,
                   bbox: list | None = None) -> RawDetection:
    if bbox is None:
        bbox = [100, 100, 300, 300]
    return RawDetection(class_name=cls, confidence=conf, bbox=bbox)


def make_location(lat: float = 28.6329, lon: float = 77.2195) -> LocationData:
    return LocationData(latitude=lat, longitude=lon, heading_deg=90.0)


def make_builder(dry_run: bool = True, tmp_path: Path | None = None) -> EventBuilder:
    evidence_dir = tmp_path or Path("/tmp/evidence_test")
    return EventBuilder(
        bus_id="BUS-01",
        route_id="ROUTE-RED",
        dry_run=dry_run,
        evidence_dir=evidence_dir,
    )


# ---------------------------------------------------------------------------
# Tests: severity scoring
# ---------------------------------------------------------------------------
class TestSeverityScoring:
    def test_pothole_high_confidence_is_critical(self):
        """Pothole@100% + large bbox → score = 70*1.0 + 15 = 85 → Critical"""
        # 200x200 bbox on 640x480 frame → area ≈ 13% > 4% → +15 bonus
        det = make_detection("Pothole", 1.0, [100, 100, 300, 300])
        builder = make_builder()
        score = builder._score(det, 640, 480)
        assert score >= 75, f"Expected Critical score (≥75), got {score}"
        assert _score_to_severity(score) == "Critical"

    def test_pothole_mid_confidence_is_high(self):
        """Pothole@85% + large bbox → score = 70*0.85 + 15 = 74.5 → High"""
        det = make_detection("Pothole", 0.85, [100, 100, 300, 300])
        builder = make_builder()
        score = builder._score(det, 640, 480)
        assert 50 <= score < 75, f"Expected High range (50-74), got {score}"
        assert _score_to_severity(score) == "High"

    def test_crack_low_confidence_is_low(self):
        det = make_detection("Crack", 0.38, [10, 10, 20, 20])  # tiny bbox
        builder = make_builder()
        score = builder._score(det, 640, 480)
        assert _score_to_severity(score) == "Low"

    def test_speed_bump_is_low(self):
        det = make_detection("Speed-Bump", 0.50, [10, 10, 20, 20])
        builder = make_builder()
        score = builder._score(det, 640, 480)
        # 20 * 0.5 = 10 → Low
        assert _score_to_severity(score) == "Low"

    def test_score_clamped_at_100(self):
        det = make_detection("Pothole", 1.0, [0, 0, 640, 480])
        builder = make_builder()
        assert builder._score(det, 640, 480) <= 100.0


# ---------------------------------------------------------------------------
# Tests: GPS simulator
# ---------------------------------------------------------------------------
class TestGPSSimulator:
    def test_returns_location_data(self):
        gps = GPSSimulator(route_id="ROUTE-RED", total_frames=100)
        loc = gps.get_location(0)
        assert isinstance(loc, LocationData)
        assert -90 <= loc.latitude <= 90
        assert -180 <= loc.longitude <= 180

    def test_heading_is_valid(self):
        gps = GPSSimulator(route_id="ROUTE-RED", total_frames=100)
        loc = gps.get_location(50)
        assert 0 <= loc.heading_deg < 360

    def test_unknown_route_falls_back_gracefully(self):
        gps = GPSSimulator(route_id="ROUTE-UNKNOWN", total_frames=100)
        loc = gps.get_location(0)
        assert loc.latitude != 0.0

    def test_final_frame_within_bounds(self):
        gps = GPSSimulator(route_id="ROUTE-BLUE", total_frames=200)
        loc = gps.get_location(200)
        assert isinstance(loc, LocationData)


# ---------------------------------------------------------------------------
# Tests: deduplication
# ---------------------------------------------------------------------------
class TestDeduplication:
    def test_first_detection_is_dispatched(self, tmp_path):
        builder = make_builder(dry_run=True, tmp_path=tmp_path)
        frame = blank_frame()
        det = make_detection("Pothole", 0.85, [100, 100, 300, 300])
        loc = make_location()
        event = builder.process(det, loc, frame, 640, 480)
        assert event is not None
        assert event["event_type"] == "Pothole"

    def test_duplicate_within_cooldown_is_suppressed(self, tmp_path):
        builder = make_builder(dry_run=True, tmp_path=tmp_path)
        frame = blank_frame()
        det = make_detection("Pothole", 0.85, [100, 100, 300, 300])
        loc = make_location()
        first = builder.process(det, loc, frame, 640, 480)
        second = builder.process(det, loc, frame, 640, 480)
        assert first is not None
        assert second is None  # suppressed by cooldown

    def test_detection_passes_after_cooldown(self, tmp_path):
        builder = make_builder(dry_run=True, tmp_path=tmp_path)
        frame = blank_frame()
        det = make_detection("Crack", 0.80, [100, 100, 300, 300])
        loc = make_location()
        builder.process(det, loc, frame, 640, 480)
        # Manually expire the cooldown
        builder._dedup["Crack"].last_time -= COOLDOWN_SECONDS + 1
        # Move location far enough away
        builder._dedup["Crack"].last_lat += 0.01
        builder._dedup["Crack"].last_lon += 0.01
        event = builder.process(det, loc, frame, 640, 480)
        assert event is not None


# ---------------------------------------------------------------------------
# Tests: haversine
# ---------------------------------------------------------------------------
class TestHaversine:
    def test_zero_distance(self):
        assert _haversine_m(28.0, 77.0, 28.0, 77.0) == pytest.approx(0.0, abs=0.001)

    def test_known_distance(self):
        # ~111 km per degree of latitude
        d = _haversine_m(0.0, 0.0, 1.0, 0.0)
        assert 110_000 < d < 112_000

    def test_spatial_suppression(self):
        """Two points 5 m apart should be within SPATIAL_RADIUS_M."""
        # ~9e-5 degrees ≈ 10 m, so 4.5e-5 ≈ 5 m
        d = _haversine_m(28.0, 77.0, 28.000045, 77.0)
        assert d < SPATIAL_RADIUS_M


# ---------------------------------------------------------------------------
# Tests: event payload structure
# ---------------------------------------------------------------------------
class TestEventPayload:
    def test_event_has_required_fields(self, tmp_path):
        builder = make_builder(dry_run=True, tmp_path=tmp_path)
        frame = blank_frame()
        det = make_detection("Pothole", 0.85, [100, 100, 300, 300])
        loc = make_location(28.6329, 77.2195)
        event = builder.process(det, loc, frame, 640, 480)
        assert event is not None

        required = {
            "event_id", "event_type", "confidence", "severity",
            "priority_score", "latitude", "longitude",
            "bus_id", "route_id", "evidence_path", "status",
        }
        missing = required - set(event.keys())
        assert not missing, f"Missing keys: {missing}"

    def test_non_anomaly_class_is_ignored(self, tmp_path):
        builder = make_builder(dry_run=True, tmp_path=tmp_path)
        frame = blank_frame()
        det = make_detection("Car", 0.90)
        loc = make_location()
        result = builder.process(det, loc, frame, 640, 480)
        assert result is None


# ---------------------------------------------------------------------------
# Tests: bus simulator
# ---------------------------------------------------------------------------
class TestBusSimulator:
    def test_known_bus(self):
        bus = BusSimulator("BUS-02")
        assert bus.bus_id == "BUS-02"
        assert bus.route_id == "ROUTE-BLUE"

    def test_unknown_bus_raises(self):
        with pytest.raises(ValueError):
            BusSimulator("BUS-99")

    def test_speed_in_range(self):
        bus = BusSimulator("BUS-01")
        for _ in range(20):
            s = bus.current_speed()
            assert 25 <= s <= 42


# ---------------------------------------------------------------------------
# Tests: physical anomaly tracking (9 synthetic scenarios)
# ---------------------------------------------------------------------------
class TestAnomalyTracker:
    def test_scenario_1_one_pothole_50_consecutive_frames(self, tmp_path):
        tracker = AnomalyTracker(lost_track_buffer=30)
        builder = make_builder(dry_run=True, tmp_path=tmp_path)
        frame = blank_frame()
        loc = make_location()
        events = []

        for f in range(50):
            det = make_detection("Pothole", 0.85, [100, 100, 200, 200])
            completed = tracker.update([det], frame, loc, f)
            for c in completed:
                evt = builder.process_track(c, 640, 480)
                if evt:
                    events.append(evt)

        for c in tracker.flush():
            evt = builder.process_track(c, 640, 480)
            if evt:
                events.append(evt)

        assert len(events) == 1
        assert events[0]["event_type"] == "Pothole"
        assert events[0]["hit_count"] == 50

    def test_scenario_2_one_pothole_gradually_moving(self, tmp_path):
        tracker = AnomalyTracker(lost_track_buffer=30)
        builder = make_builder(dry_run=True, tmp_path=tmp_path)
        frame = blank_frame()
        loc = make_location()
        events = []

        for f in range(30):
            y_offset = f * 4
            det = make_detection("Pothole", 0.85, [100, 100 + y_offset, 200, 200 + y_offset])
            completed = tracker.update([det], frame, loc, f)
            for c in completed:
                evt = builder.process_track(c, 640, 480)
                if evt:
                    events.append(evt)

        for c in tracker.flush():
            evt = builder.process_track(c, 640, 480)
            if evt:
                events.append(evt)

        assert len(events) == 1
        assert events[0]["event_type"] == "Pothole"
        assert events[0]["hit_count"] == 30

    def test_scenario_3_one_pothole_temporarily_missed_and_reacquired(self, tmp_path):
        tracker = AnomalyTracker(lost_track_buffer=30)
        builder = make_builder(dry_run=True, tmp_path=tmp_path)
        frame = blank_frame()
        loc = make_location()
        events = []

        for f in range(10):
            det = make_detection("Pothole", 0.85, [100, 100, 200, 200])
            completed = tracker.update([det], frame, loc, f)
            for c in completed:
                evt = builder.process_track(c, 640, 480)
                if evt:
                    events.append(evt)

        # 15 missed frames (< lost_track_buffer=30)
        for f in range(10, 25):
            completed = tracker.update([], frame, loc, f)
            for c in completed:
                evt = builder.process_track(c, 640, 480)
                if evt:
                    events.append(evt)

        # Reacquired
        for f in range(25, 35):
            det = make_detection("Pothole", 0.88, [100, 100, 200, 200])
            completed = tracker.update([det], frame, loc, f)
            for c in completed:
                evt = builder.process_track(c, 640, 480)
                if evt:
                    events.append(evt)

        for c in tracker.flush():
            evt = builder.process_track(c, 640, 480)
            if evt:
                events.append(evt)

        assert len(events) == 1
        assert events[0]["event_type"] == "Pothole"
        assert events[0]["hit_count"] == 20

    def test_scenario_4_two_distinct_potholes_simultaneously(self, tmp_path):
        tracker = AnomalyTracker(lost_track_buffer=30)
        builder = make_builder(dry_run=True, tmp_path=tmp_path)
        frame = blank_frame()
        loc = make_location()
        events = []

        for f in range(10):
            det1 = make_detection("Pothole", 0.85, [50, 50, 150, 150])
            det2 = make_detection("Pothole", 0.80, [300, 300, 400, 400])
            completed = tracker.update([det1, det2], frame, loc, f)
            for c in completed:
                evt = builder.process_track(c, 640, 480)
                if evt:
                    events.append(evt)

        for c in tracker.flush():
            evt = builder.process_track(c, 640, 480)
            if evt:
                events.append(evt)

        assert len(events) == 2
        assert all(e["event_type"] == "Pothole" for e in events)

    def test_scenario_5_three_distinct_potholes_simultaneously(self, tmp_path):
        tracker = AnomalyTracker(lost_track_buffer=30)
        builder = make_builder(dry_run=True, tmp_path=tmp_path)
        frame = blank_frame()
        loc = make_location()
        events = []

        for f in range(10):
            det1 = make_detection("Pothole", 0.85, [50, 50, 120, 120])
            det2 = make_detection("Pothole", 0.80, [200, 200, 270, 270])
            det3 = make_detection("Pothole", 0.75, [350, 350, 420, 420])
            completed = tracker.update([det1, det2, det3], frame, loc, f)
            for c in completed:
                evt = builder.process_track(c, 640, 480)
                if evt:
                    events.append(evt)

        for c in tracker.flush():
            evt = builder.process_track(c, 640, 480)
            if evt:
                events.append(evt)

        assert len(events) == 3
        assert all(e["event_type"] == "Pothole" for e in events)

    def test_scenario_6_two_potholes_close_together(self, tmp_path):
        tracker = AnomalyTracker(lost_track_buffer=30)
        builder = make_builder(dry_run=True, tmp_path=tmp_path)
        frame = blank_frame()
        loc = make_location()
        events = []

        for f in range(10):
            det1 = make_detection("Pothole", 0.85, [100, 100, 180, 180])
            det2 = make_detection("Pothole", 0.82, [190, 100, 270, 180])
            completed = tracker.update([det1, det2], frame, loc, f)
            for c in completed:
                evt = builder.process_track(c, 640, 480)
                if evt:
                    events.append(evt)

        for c in tracker.flush():
            evt = builder.process_track(c, 640, 480)
            if evt:
                events.append(evt)

        assert len(events) == 2

    def test_scenario_7_pothole_plus_crack_same_location(self, tmp_path):
        tracker = AnomalyTracker(lost_track_buffer=30)
        builder = make_builder(dry_run=True, tmp_path=tmp_path)
        frame = blank_frame()
        loc = make_location()
        events = []

        for f in range(10):
            det1 = make_detection("Pothole", 0.85, [100, 100, 200, 200])
            det2 = make_detection("Crack", 0.70, [100, 100, 200, 200])
            completed = tracker.update([det1, det2], frame, loc, f)
            for c in completed:
                evt = builder.process_track(c, 640, 480)
                if evt:
                    events.append(evt)

        for c in tracker.flush():
            evt = builder.process_track(c, 640, 480)
            if evt:
                events.append(evt)

        assert len(events) == 2
        types = {e["event_type"] for e in events}
        assert types == {"Pothole", "Crack"}

    def test_scenario_8_pothole_leaves_another_enters(self, tmp_path):
        tracker = AnomalyTracker(lost_track_buffer=20)
        builder = make_builder(dry_run=True, tmp_path=tmp_path)
        frame = blank_frame()
        loc = make_location()
        events = []

        # Pothole A in frames 0..9
        for f in range(10):
            det1 = make_detection("Pothole", 0.85, [100, 400, 200, 500])
            completed = tracker.update([det1], frame, loc, f)
            for c in completed:
                evt = builder.process_track(c, 640, 480)
                if evt:
                    events.append(evt)

        # Empty frames 10..35 (> lost_track_buffer=20) -> Pothole A track completes
        for f in range(10, 36):
            completed = tracker.update([], frame, loc, f)
            for c in completed:
                evt = builder.process_track(c, 640, 480)
                if evt:
                    events.append(evt)

        # Pothole B enters in frames 36..45
        for f in range(36, 46):
            det2 = make_detection("Pothole", 0.88, [100, 50, 200, 150])
            completed = tracker.update([det2], frame, loc, f)
            for c in completed:
                evt = builder.process_track(c, 640, 480)
                if evt:
                    events.append(evt)

        for c in tracker.flush():
            evt = builder.process_track(c, 640, 480)
            if evt:
                events.append(evt)

        assert len(events) == 2
        assert all(e["event_type"] == "Pothole" for e in events)

    def test_scenario_9_backend_spatial_deduplication(self):
        from backend.app.services.deduplication import calculate_haversine_meters
        lat1, lon1 = 28.6329, 77.2195
        # ~5 meters away
        lat2, lon2 = 28.6329 + 0.000045, 77.2195
        dist = calculate_haversine_meters(lat1, lon1, lat2, lon2)
        assert dist <= 15.0, f"Expected <= 15.0m, got {dist}"

        # ~50 meters away
        lat3, lon3 = 28.6329 + 0.00045, 77.2195
        dist_far = calculate_haversine_meters(lat1, lon1, lat3, lon3)
        assert dist_far > 15.0, f"Expected > 15.0m, got {dist_far}"

