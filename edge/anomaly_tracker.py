"""
edge/anomaly_tracker.py
-----------------------
Physical road anomaly tracking layer powered by ByteTrack.

Maintains persistent track identities for physical road anomalies across frames.
Differentiates between multiple distinct potholes vs repeated detections of the same pothole.
Emits a single CompletedTrack when an anomaly track finishes, selecting the
highest-confidence observation for evidence, bbox, and GPS localization.
"""
from __future__ import annotations

import dataclasses
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import supervision as sv

from edge.detector import ANOMALY_CLASSES, RawDetection
from edge.gps_simulator import LocationData


@dataclasses.dataclass
class CompletedTrack:
    """Represents a completed physical anomaly track with its best observation."""
    track_id: int
    class_name: str
    best_confidence: float
    best_bbox: List[int]       # [x1, y1, x2, y2]
    best_frame: np.ndarray     # BGR frame snapshot at best observation
    best_location: LocationData
    hit_count: int             # Number of frames this anomaly was detected
    first_frame_idx: int
    last_frame_idx: int
    start_observations: List[Tuple[int, List[int], float]] = dataclasses.field(default_factory=list)
    end_observations: List[Tuple[int, List[int], float]] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class _TrackRecord:
    track_id: int
    class_name: str
    best_confidence: float
    best_bbox: List[int]
    best_frame: np.ndarray
    best_location: LocationData
    hit_count: int
    first_frame_idx: int
    last_frame_idx: int
    start_observations: List[Tuple[int, List[int], float]] = dataclasses.field(default_factory=list)
    end_observations: List[Tuple[int, List[int], float]] = dataclasses.field(default_factory=list)


class AnomalyTracker:
    """
    Multi-object tracker for physical road anomalies.
    Maintains per-class ByteTrack trackers to ensure class consistency
    (e.g., a Crack and a Pothole at the same position will never merge).
    """

    def __init__(
        self,
        track_activation_threshold: float = 0.30,
        lost_track_buffer: int = 30,
        minimum_matching_threshold: float = 0.8,
        frame_rate: int = 30,
        min_hits: int = 2,
    ):
        """
        Args:
            track_activation_threshold: Min confidence to start a track.
            lost_track_buffer: Number of frames to keep a lost track alive (30 = 1 sec at 30 fps).
            minimum_matching_threshold: Min IoU threshold for matching.
            frame_rate: Video frame rate.
            min_hits: Minimum detection frames required before a track is considered valid
                      (filters out transient single-frame false positives).
        """
        self.track_activation_threshold = track_activation_threshold
        self.lost_track_buffer = lost_track_buffer
        self.minimum_matching_threshold = minimum_matching_threshold
        self.frame_rate = frame_rate
        self.min_hits = min_hits

        self._trackers: Dict[str, sv.ByteTrack] = {
            cls_name: sv.ByteTrack(
                track_activation_threshold=self.track_activation_threshold,
                lost_track_buffer=self.lost_track_buffer,
                minimum_matching_threshold=self.minimum_matching_threshold,
                frame_rate=self.frame_rate,
                minimum_consecutive_frames=1,
            )
            for cls_name in ANOMALY_CLASSES
        }

        # Key: (class_name, tracker_internal_id) -> _TrackRecord
        self._active_records: Dict[Tuple[str, int], _TrackRecord] = {}
        self._next_track_id = 1

    def update(
        self,
        detections: List[RawDetection],
        frame: np.ndarray,
        location: LocationData,
        frame_idx: int,
    ) -> List[CompletedTrack]:
        """
        Update the tracker with detections from current frame.
        Returns any tracks that completed in this frame.
        """
        # 1. Filter only anomaly classes
        anomaly_dets = [d for d in detections if d.class_name in ANOMALY_CLASSES]

        # Group by class
        by_class: Dict[str, List[RawDetection]] = {cls: [] for cls in ANOMALY_CLASSES}
        for det in anomaly_dets:
            by_class[det.class_name].append(det)

        completed_tracks: List[CompletedTrack] = []

        # 2. Update each class's ByteTrack
        for cls_name, cls_dets in by_class.items():
            tracker = self._trackers[cls_name]

            if cls_dets:
                xyxy = np.array([d.bbox for d in cls_dets], dtype=np.float32)
                conf = np.array([d.confidence for d in cls_dets], dtype=np.float32)
                sv_dets = sv.Detections(xyxy=xyxy, confidence=conf)
            else:
                sv_dets = sv.Detections.empty()

            tracked = tracker.update_with_detections(sv_dets)

            # Update active records with matched detections
            if tracked.tracker_id is not None and len(tracked.tracker_id) > 0:
                for i, sv_tid in enumerate(tracked.tracker_id):
                    tid = int(sv_tid)
                    if tid < 0:
                        continue
                    box = [int(v) for v in tracked.xyxy[i].tolist()]
                    conf = float(tracked.confidence[i]) if tracked.confidence is not None else 0.5
                    key = (cls_name, tid)

                    if key not in self._active_records:
                        track_id = self._next_track_id
                        self._next_track_id += 1
                        obs_tuple = (frame_idx, box, conf)
                        self._active_records[key] = _TrackRecord(
                            track_id=track_id,
                            class_name=cls_name,
                            best_confidence=conf,
                            best_bbox=box,
                            best_frame=frame.copy(),
                            best_location=location,
                            hit_count=1,
                            first_frame_idx=frame_idx,
                            last_frame_idx=frame_idx,
                            start_observations=[obs_tuple],
                            end_observations=[obs_tuple],
                        )
                    else:
                        rec = self._active_records[key]
                        rec.hit_count += 1
                        rec.last_frame_idx = frame_idx
                        obs_tuple = (frame_idx, box, conf)
                        if len(rec.start_observations) < 10:
                            rec.start_observations.append(obs_tuple)
                        rec.end_observations.append(obs_tuple)
                        if len(rec.end_observations) > 10:
                            rec.end_observations.pop(0)
                        if conf > rec.best_confidence:
                            rec.best_confidence = conf
                            rec.best_bbox = box
                            rec.best_frame = frame.copy()
                            rec.best_location = location

            # Check removed tracks from this tracker
            if hasattr(tracker, "removed_tracks"):
                for removed in tracker.removed_tracks:
                    r_id = getattr(removed, "external_track_id", None)
                    if r_id is None or r_id < 0:
                        continue
                    key = (cls_name, int(r_id))
                    if key in self._active_records:
                        rec = self._active_records.pop(key)
                        if rec.hit_count >= self.min_hits:
                            completed_tracks.append(
                                CompletedTrack(
                                    track_id=rec.track_id,
                                    class_name=rec.class_name,
                                    best_confidence=rec.best_confidence,
                                    best_bbox=rec.best_bbox,
                                    best_frame=rec.best_frame,
                                    best_location=rec.best_location,
                                    hit_count=rec.hit_count,
                                    first_frame_idx=rec.first_frame_idx,
                                    last_frame_idx=rec.last_frame_idx,
                                    start_observations=rec.start_observations,
                                    end_observations=rec.end_observations,
                                )
                            )

        return completed_tracks

    def flush(self) -> List[CompletedTrack]:
        """
        Flush all remaining active tracks at end of stream.
        """
        completed: List[CompletedTrack] = []
        for key, rec in list(self._active_records.items()):
            if rec.hit_count >= self.min_hits:
                completed.append(
                    CompletedTrack(
                        track_id=rec.track_id,
                        class_name=rec.class_name,
                        best_confidence=rec.best_confidence,
                        best_bbox=rec.best_bbox,
                        best_frame=rec.best_frame,
                        best_location=rec.best_location,
                        hit_count=rec.hit_count,
                        first_frame_idx=rec.first_frame_idx,
                        last_frame_idx=rec.last_frame_idx,
                        start_observations=rec.start_observations,
                        end_observations=rec.end_observations,
                    )
                )
        self._active_records.clear()
        return completed

    @property
    def active_track_count(self) -> int:
        return len(self._active_records)
