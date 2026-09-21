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
import sqlite3
import threading
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
    "Rash-Driving": 90,
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
        camera_id: str = "FRONT",
        api_url: str = DEFAULT_API_URL,
        evidence_dir: Optional[Path] = None,
        dry_run: bool = False,      # set True in unit tests
    ):
        self.bus_id = bus_id
        self.route_id = route_id
        self.camera_id = camera_id
        self.api_url = api_url
        self.evidence_dir = Path(evidence_dir) if evidence_dir else EVIDENCE_DIR
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.dry_run = dry_run
        
        self.db_path = self.evidence_dir / "outbox.db"
        self._init_db()
        self._outbox_thread = threading.Thread(target=self._outbox_worker, daemon=True)
        self._outbox_thread.start()

        # key → (class_name,)  (per bus; extend to per-bus if needed)
        self._dedup: dict[str, _DeduplicatorState] = {}
        self.metrics = {
            "events_created": 0,
            "events_dispatched": 0,
        }

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS outbox (
                            event_id TEXT PRIMARY KEY,
                            payload TEXT,
                            evidence_path TEXT,
                            created_at REAL,
                            retry_count INTEGER,
                            last_attempt REAL,
                            status TEXT)''')

    def _outbox_worker(self):
        while True:
            time.sleep(5)
            try:
                with sqlite3.connect(self.db_path) as conn:
                    c = conn.execute("SELECT event_id, payload, evidence_path, retry_count, last_attempt FROM outbox WHERE status='Pending'")
                    rows = c.fetchall()
                    for row in rows:
                        event_id, payload, ev_path, retry_count, last_attempt = row
                        now = time.time()
                        
                        # Exponential backoff (max 60 seconds)
                        backoff = min((2 ** retry_count) * 5, 60)
                        if now - last_attempt < backoff:
                            continue
                        
                        success = False
                        try:
                            with open(ev_path, "rb") as fh:
                                resp = requests.post(
                                    self.api_url,
                                    data={"event_data": payload},
                                    files={"image_file": (Path(ev_path).name, fh, "image/jpeg")},
                                    timeout=5,
                                )
                            if resp.status_code in (200, 201):
                                success = True
                                print(f"[OUTBOX] ✓ Flushed event {event_id}")
                        except Exception:
                            pass
                        
                        if success:
                            conn.execute("DELETE FROM outbox WHERE event_id=?", (event_id,))
                        else:
                            conn.execute("UPDATE outbox SET retry_count=?, last_attempt=? WHERE event_id=?", 
                                         (retry_count + 1, now, event_id))
                    conn.commit()
            except Exception as e:
                print(f"[OUTBOX] Worker error: {e}")

    # ------------------------------------------------------------------
    # Public: process a completed physical anomaly track
    # ------------------------------------------------------------------
    def process_track(
        self,
        completed_track: CompletedTrack,
        frame_w: int,
        frame_h: int,
        nearby_plates: Optional[list[dict]] = None,
        nearby_signs: Optional[list[dict]] = None,
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
        msg_id = f"MSG-{uuid.uuid4().hex[:12].upper()}"
        event = {
            "schema_version": 2 if (nearby_plates or nearby_signs) else 1,
            "edge_event_id": evt_uuid,
            "event_id": evt_uuid,
            "message_id": msg_id,
            "anomaly_type": cls,
            "event_type": cls,
            "confidence": round(completed_track.best_confidence, 4),
            "severity": severity,
            "priority_score": round(min(score, 100), 1),
            "latitude": completed_track.best_location.latitude,
            "longitude": completed_track.best_location.longitude,
            "bus_id": self.bus_id,
            "route_id": self.route_id,
            "camera_id": self.camera_id,
            "evidence_path": str(evidence_path),
            "status": "Pending",
            "track_id": completed_track.track_id,
            "hit_count": completed_track.hit_count,
            "nearby_plates": nearby_plates or [],
            "nearby_signs": nearby_signs or [],
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
        nearby_plates: Optional[list[dict]] = None,
        nearby_signs: Optional[list[dict]] = None,
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
        msg_id = f"MSG-{uuid.uuid4().hex[:12].upper()}"
        event = {
            "schema_version": 2 if (nearby_plates or nearby_signs) else 1,
            "edge_event_id": evt_uuid,
            "event_id": evt_uuid,
            "message_id": msg_id,
            "anomaly_type": cls,
            "event_type": cls,
            "confidence": round(detection.confidence, 4),
            "severity": severity,
            "priority_score": round(min(score, 100), 1),
            "latitude": location.latitude,
            "longitude": location.longitude,
            "bus_id": self.bus_id,
            "route_id": self.route_id,
            "camera_id": self.camera_id,
            "evidence_path": str(evidence_path),
            "status": "Pending",
            "nearby_plates": nearby_plates or [],
            "nearby_signs": nearby_signs or [],
        }

        # --- Dispatch ---
        if not self.dry_run:
            self._post(event, evidence_path)

        # --- Update dedup state ---
        state.last_time = now
        state.last_lat = location.latitude
        state.last_lon = location.longitude

        return event

    def dispatch_safety_event(
        self,
        event_type: str,
        location: LocationData,
        frame: Optional[np.ndarray] = None,
        confidence: float = 0.9,
        details: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        Dispatches a vehicle/driver safety event (such as Rash-Driving or near-miss).
        """
        key = event_type
        state = self._dedup.setdefault(key, _DeduplicatorState())
        now = time.time()

        if now - state.last_time < COOLDOWN_SECONDS:
            return None

        base = BASE_SCORES.get(event_type, 80)
        score = base * confidence
        severity = _score_to_severity(score)

        evidence_path = self.evidence_dir / f"safety_{int(now * 1000)}.jpg"
        if frame is not None:
            snippet = frame.copy()
            cv2.putText(snippet, f"{event_type} {confidence:.0%}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.imwrite(str(evidence_path), snippet, [cv2.IMWRITE_JPEG_QUALITY, 85])
        else:
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank, f"SAFETY EVENT: {event_type}", (20, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.imwrite(str(evidence_path), blank, [cv2.IMWRITE_JPEG_QUALITY, 85])

        evt_uuid = f"EVT-SAF-{uuid.uuid4().hex[:8].upper()}"
        msg_id = f"MSG-{uuid.uuid4().hex[:12].upper()}"
        event = {
            "schema_version": 1,
            "edge_event_id": evt_uuid,
            "event_id": evt_uuid,
            "message_id": msg_id,
            "anomaly_type": event_type,
            "event_type": event_type,
            "confidence": round(confidence, 4),
            "severity": severity,
            "priority_score": round(min(score, 100), 1),
            "latitude": location.latitude,
            "longitude": location.longitude,
            "speed_kmh": details.get("speed_kmh", 0.0) if details else 0.0,
            "bus_id": self.bus_id,
            "route_id": self.route_id,
            "camera_id": self.camera_id,
            "evidence_path": str(evidence_path),
            "status": "Pending",
        }

        self.metrics["events_created"] += 1
        if not self.dry_run:
            self._post(event, evidence_path)
        self.metrics["events_dispatched"] += 1

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
        x1, y1, x2, y2 = [int(v) for v in det.bbox]
        # Preserve full contextual frame from dashcam with bounding box
        evidence_frame = frame.copy()
        color = (0, 255, 0) if cls in {"Pothole", "Crack", "Crack-Severe", "Speed-Bump"} else (0, 200, 255)
        cv2.rectangle(evidence_frame, (x1, y1), (x2, y2), color, 3)
        label = f"{cls} {det.confidence:.0%}"
        cv2.putText(
            evidence_frame,
            label,
            (x1, max(y1 - 10, 25)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )

        ts = int(time.time() * 1000)
        fname = f"{cls.replace('-', '_')}_{ts}.jpg"
        fpath = self.evidence_dir / fname
        cv2.imwrite(str(fpath), evidence_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return fpath

    def _post(self, event: dict, evidence_path: Path) -> None:
        """Attempt immediate HTTP POST. Fall back to outbox on failure."""
        event_id = event["event_id"]
        payload = json.dumps(event)
        now = time.time()
        success = False
        try:
            with open(evidence_path, "rb") as fh:
                resp = requests.post(
                    self.api_url,
                    data={"event_data": payload},
                    files={"image_file": (evidence_path.name, fh, "image/jpeg")},
                    timeout=5,
                )
            if resp.status_code in (200, 201):
                success = True
                print(f"[DISPATCHER] ✓ {event['event_type']} | {event['severity']} | {resp.status_code}")
            else:
                print(f"[DISPATCHER] Unexpected status {resp.status_code}: {resp.text[:120]}")
        except requests.exceptions.ConnectionError:
            print("[DISPATCHER] ✗ Backend unreachable — buffering event to outbox")
        except Exception as exc:
            print(f"[DISPATCHER] ✗ POST failed: {exc}")
            
        if not success:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''INSERT OR IGNORE INTO outbox 
                                    (event_id, payload, evidence_path, created_at, retry_count, last_attempt, status) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                 (event_id, payload, str(evidence_path), now, 1, now, "Pending"))
            except Exception as e:
                print(f"[DISPATCHER] Outbox DB Error: {e}")
