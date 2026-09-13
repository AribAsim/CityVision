"""
edge/event_builder.py
----------------------
Orchestrates the full frame-level post-YOLO pipeline:
  1. Severity scoring  (spec §4)
  2. Spatial + temporal deduplication  (spec §3)
  3. Evidence snapshot save
  4. HTTP POST to FastAPI /api/ingest (multipart/form-data)

All spec constants match brain/07_EVENT_ENGINE.md exactly.
"""
from __future__ import annotations

import io
import json
import math
import os
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import requests

from edge.detector import RawDetection
from edge.gps_simulator import LocationData
from edge.anomaly_tracker import CompletedTrack

# ---------------------------------------------------------------------------
# Spec constants (brain/07_EVENT_ENGINE.md §3 & §4)
# ---------------------------------------------------------------------------
COOLDOWN_SECONDS = 2.5           # per anomaly class
SPATIAL_RADIUS_M = 12.0          # suppression radius

BASE_SCORES = {
    "Pothole": 70,
    "Crack-Severe": 55,
    "Crack": 30,
    "Speed-Bump": 20,
}
LARGE_BBOX_BONUS = 15            # added when bbox > 4% screen area
LARGE_BBOX_THRESHOLD = 0.04      # fraction of frame w*h

# Severity tiers
def _score_to_severity(score: float) -> str:
    if score >= 75:
        return "Critical"
    elif score >= 50:
        return "High"
    elif score >= 30:
        return "Medium"
    return "Low"


# Default FastAPI endpoint
DEFAULT_API_URL = "http://localhost:8000/api/ingest"
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "data" / "evidence"


# ---------------------------------------------------------------------------
# Haversine helper (metres between two GPS points)
# ---------------------------------------------------------------------------
def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Deduplicator state per (bus_id, class_name)
# ---------------------------------------------------------------------------
class _DeduplicatorState:
    def __init__(self):
        self.last_time: float = 0.0
        self.last_lat: float = 0.0
        self.last_lon: float = 0.0


class EventBuilder:
    """
    Maintains deduplication state across frames and dispatches confirmed
    events to the FastAPI backend.
    """

    def __init__(
        self,
        bus_id: str,
        route_id: str,
        api_url: str = DEFAULT_API_URL,
        evidence_dir: Optional[Path] = None,
        dry_run: bool = False,      # set True in unit tests
    ):
        self.bus_id = bus_id
        self.route_id = route_id
        self.api_url = api_url
        self.evidence_dir = Path(evidence_dir) if evidence_dir else EVIDENCE_DIR
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.dry_run = dry_run

        # key → (class_name,)  (per bus; extend to per-bus if needed)
        self._dedup: dict[str, _DeduplicatorState] = {}
        self.metrics = {
            "events_created": 0,
            "events_dispatched": 0,
        }

    # ------------------------------------------------------------------
    # Public: process a completed physical anomaly track
    # ------------------------------------------------------------------
    def process_track(
        self,
        completed_track: CompletedTrack,
        frame_w: int,
        frame_h: int,
    ) -> Optional[dict]:
        """
        Evaluate a CompletedTrack from ByteTrack. Returns the dispatched
        event dict on success, or None if not an anomaly class.
        Constructs an event from the highest-confidence observation of the track.
        """
        cls = completed_track.class_name
        if cls not in BASE_SCORES:
            return None

        # Synthesize detection from best observation for scoring
        det = RawDetection(
            class_name=cls,
            confidence=completed_track.best_confidence,
            bbox=completed_track.best_bbox,
        )

        score = self._score(det, frame_w, frame_h)
        severity = _score_to_severity(score)

        # Save evidence snapshot from best frame
        evidence_path = self._save_evidence(
            det, completed_track.best_frame, cls, score
        )

        evt_uuid = f"EVT-TRK{completed_track.track_id}-{uuid.uuid4().hex[:6].upper()}"
        event = {
            "edge_event_id": evt_uuid,
            "event_id": evt_uuid,
            "anomaly_type": cls,
            "event_type": cls,
            "confidence": round(completed_track.best_confidence, 4),
            "severity": severity,
            "priority_score": round(min(score, 100), 1),
            "latitude": completed_track.best_location.latitude,
            "longitude": completed_track.best_location.longitude,
            "bus_id": self.bus_id,
            "route_id": self.route_id,
            "evidence_path": str(evidence_path),
            "status": "Pending",
            "track_id": completed_track.track_id,
            "hit_count": completed_track.hit_count,
        }

        self.metrics["events_created"] += 1

        if not self.dry_run:
            self._post(event, evidence_path)

        self.metrics["events_dispatched"] += 1
        return event

    # ------------------------------------------------------------------
    # Public: process a single detection (kept for backward compatibility)
    # ------------------------------------------------------------------
    def process(
        self,
        detection: RawDetection,
        location: LocationData,
        frame: np.ndarray,
        frame_w: int,
        frame_h: int,
    ) -> Optional[dict]:
        """
        Evaluate a single RawDetection. Returns the dispatched event dict
        on success, or None if deduplicated / not anomaly.
        """
        cls = detection.class_name
        if cls not in BASE_SCORES:
            return None   # not a tracked anomaly

        key = cls
        state = self._dedup.setdefault(key, _DeduplicatorState())
        now = time.time()

        # --- Temporal cooldown check ---
        if now - state.last_time < COOLDOWN_SECONDS:
            return None

        # --- Spatial suppression check (if we have a previous location) ---
        if state.last_time > 0:
            dist = _haversine_m(
                state.last_lat, state.last_lon,
                location.latitude, location.longitude,
            )
            if dist < SPATIAL_RADIUS_M:
                return None

        # --- Severity score ---
        score = self._score(detection, frame_w, frame_h)
        severity = _score_to_severity(score)

        # --- Evidence snapshot ---
        evidence_path = self._save_evidence(detection, frame, cls, score)

        # --- Build event payload ---
        evt_uuid = f"EVT-{uuid.uuid4().hex[:10].upper()}"
        event = {
            "edge_event_id": evt_uuid,
            "event_id": evt_uuid,
            "anomaly_type": cls,
            "event_type": cls,
            "confidence": round(detection.confidence, 4),
            "severity": severity,
            "priority_score": round(min(score, 100), 1),
            "latitude": location.latitude,
            "longitude": location.longitude,
            "bus_id": self.bus_id,
            "route_id": self.route_id,
            "evidence_path": str(evidence_path),
            "status": "Pending",
        }

        # --- Dispatch ---
        if not self.dry_run:
            self._post(event, evidence_path)

        # --- Update dedup state ---
        state.last_time = now
        state.last_lat = location.latitude
        state.last_lon = location.longitude

        return event

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _score(self, det: RawDetection, fw: int, fh: int) -> float:
        base = BASE_SCORES.get(det.class_name, 20)
        score = base * det.confidence
        # bbox area bonus
        x1, y1, x2, y2 = det.bbox
        area_frac = ((x2 - x1) * (y2 - y1)) / max(fw * fh, 1)
        if area_frac > LARGE_BBOX_THRESHOLD:
            score += LARGE_BBOX_BONUS
        return min(score, 100.0)

    def _save_evidence(
        self,
        det: RawDetection,
        frame: np.ndarray,
        cls: str,
        score: float,
    ) -> Path:
        x1, y1, x2, y2 = det.bbox
        # Add small padding without going OOB
        h, w = frame.shape[:2]
        pad = 10
        x1c = max(x1 - pad, 0)
        y1c = max(y1 - pad, 0)
        x2c = min(x2 + pad, w)
        y2c = min(y2 + pad, h)

        # Also draw bounding box on the snippet for clarity
        snippet = frame[y1c:y2c, x1c:x2c].copy()
        label = f"{cls} {det.confidence:.0%}"
        cv2.putText(snippet, label, (4, 18), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (0, 255, 0), 2)

        ts = int(time.time() * 1000)
        fname = f"{cls.replace('-', '_')}_{ts}.jpg"
        fpath = self.evidence_dir / fname
        cv2.imwrite(str(fpath), snippet, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return fpath

    def _post(self, event: dict, evidence_path: Path) -> None:
        """Fire-and-forget HTTP POST with evidence image attached."""
        try:
            with open(evidence_path, "rb") as fh:
                resp = requests.post(
                    self.api_url,
                    data={"event_data": json.dumps(event)},
                    files={"image_file": (evidence_path.name, fh, "image/jpeg")},
                    timeout=5,
                )
            if resp.status_code not in (200, 201):
                print(f"[DISPATCHER] Unexpected status {resp.status_code}: {resp.text[:120]}")
            else:
                print(f"[DISPATCHER] ✓ {event['event_type']} | {event['severity']} | {resp.status_code}")
        except requests.exceptions.ConnectionError:
            print("[DISPATCHER] ✗ Backend unreachable — event dropped (normal if API not running)")
        except Exception as exc:
            print(f"[DISPATCHER] ✗ POST failed: {exc}")
