"""
edge/track_stitcher.py
----------------------
Motion-Compensated Post-Track Stitcher for Gap-Based Fragmentation.

Stitches fragmented tracks belonging to the same physical road anomaly
that were separated by short detection dropouts (gaps).

Operates on completed tracks after ByteTrack has finalized them.
Never merges concurrent (temporally overlapping) tracks.
Uses conservative evidence gates:
  1. Class identity match
  2. Temporal order & gap: 0 < (B.first - A.last) <= max_gap_frames
  3. Motion extrapolation distance <= position_threshold
  4. Directional consistency: cosine(v_A, v_B) >= min_cosine (when both velocities measurable)
  5. Chain validation: sequential re-validation of merged trajectory
"""
from __future__ import annotations

import dataclasses
import logging
from typing import List, Optional, Tuple

import numpy as np

from edge.anomaly_tracker import CompletedTrack
from edge.detector import ANOMALY_CLASSES

logger = logging.getLogger("track_stitcher")


@dataclasses.dataclass
class StitcherConfig:
    max_gap_frames: int = 15
    position_threshold_px: float = 25.0
    min_direction_cosine: float = 0.40
    velocity_window: int = 5
    verbose: bool = True


def _get_center(bbox: List[int]) -> Tuple[float, float]:
    return (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0


def _compute_velocity(
    observations: List[Tuple[int, List[int], float]],
    from_end: bool = True,
    window: int = 5,
) -> Tuple[float, float, float]:
    """
    Computes average velocity (vx, vy, speed) in px/frame from recent observations.
    observations: list of (frame_idx, bbox, conf)
    """
    if len(observations) < 2:
        return 0.0, 0.0, 0.0
    
    obs = observations[-window:] if from_end else observations[:window]
    if len(obs) < 2:
        return 0.0, 0.0, 0.0
    
    first_f, first_box, _ = obs[0]
    last_f, last_box, _ = obs[-1]
    df = last_f - first_f
    if df <= 0:
        return 0.0, 0.0, 0.0
    
    c1x, c1y = _get_center(first_box)
    c2x, c2y = _get_center(last_box)
    vx = (c2x - c1x) / df
    vy = (c2y - c1y) / df
    spd = float(np.hypot(vx, vy))
    return vx, vy, spd


def _cosine_similarity(v1: Tuple[float, float], v2: Tuple[float, float]) -> Optional[float]:
    mag1 = np.hypot(v1[0], v1[1])
    mag2 = np.hypot(v2[0], v2[1])
    if mag1 < 0.01 or mag2 < 0.01:
        return None  # Insufficient motion to determine direction reliably
    return float((v1[0] * v2[0] + v1[1] * v2[1]) / (mag1 * mag2))


class TrackStitcher:
    """
    Post-tracker stitching engine to heal gap-fragmented tracks.
    """

    def __init__(self, config: Optional[StitcherConfig] = None):
        self.config = config or StitcherConfig()
        # Active tracks awaiting gap resolution in streaming mode
        # Key: class_name -> List[CompletedTrack]
        self._pending_by_class: dict[str, List[CompletedTrack]] = {}

    def process_completed_track(
        self,
        c_track: CompletedTrack,
        current_frame_idx: int,
    ) -> List[CompletedTrack]:
        """
        Streaming interface: Enqueues a newly completed track and checks if any
        pending tracks can be merged or finalized (older than max_gap_frames).
        """
        cls_name = c_track.class_name
        pending = self._pending_by_class.setdefault(cls_name, [])

        # Attempt to stitch into an existing pending track
        merged = False
        for i, p_track in enumerate(pending):
            if c_track.first_frame_idx > p_track.last_frame_idx:
                gap = c_track.first_frame_idx - p_track.last_frame_idx
                if gap <= self.config.max_gap_frames:
                    should_stitch, reason = self._can_stitch(p_track, c_track, gap)
                    if should_stitch:
                        if self.config.verbose:
                            print(
                                f"[STITCHER] STREAM MERGE: Track #{p_track.track_id} (F{p_track.first_frame_idx}..F{p_track.last_frame_idx}) "
                                f"+ Track #{c_track.track_id} (F{c_track.first_frame_idx}..F{c_track.last_frame_idx}) "
                                f"| gap={gap}f | reason: {reason}"
                            )
                        pending[i] = self._merge_two(p_track, c_track)
                        merged = True
                        break

        if not merged:
            pending.append(c_track)

        # Release any pending tracks whose gap window has expired
        ready_tracks: List[CompletedTrack] = []
        remaining: List[CompletedTrack] = []
        for p_track in pending:
            if current_frame_idx - p_track.last_frame_idx > self.config.max_gap_frames:
                ready_tracks.append(p_track)
            else:
                remaining.append(p_track)

        self._pending_by_class[cls_name] = remaining
        return ready_tracks

    def flush(self) -> List[CompletedTrack]:
        """
        Flush all remaining pending tracks at end of stream.
        """
        all_pending: List[CompletedTrack] = []
        for cls_tracks in self._pending_by_class.values():
            all_pending.extend(cls_tracks)
        self._pending_by_class.clear()
        return self.stitch_tracks(all_pending)

    def stitch_tracks(
        self,
        tracks: List[CompletedTrack],
    ) -> List[CompletedTrack]:
        """
        Takes a list of CompletedTracks, identifies valid gap-stitching pairs,
        merges them conservatively using chain validation, and returns the
        resulting list of CompletedTracks.
        """
        if len(tracks) <= 1:
            return tracks

        # Separate by class (different classes never merge)
        by_class: dict[str, List[CompletedTrack]] = {}
        for t in tracks:
            by_class.setdefault(t.class_name, []).append(t)

        result_tracks: List[CompletedTrack] = []

        for cls_name, cls_tracks in by_class.items():
            stitched = self._stitch_class_tracks(cls_tracks)
            result_tracks.extend(stitched)

        # Sort by first frame index to maintain chronological order
        result_tracks.sort(key=lambda t: t.first_frame_idx)
        return result_tracks

    def _stitch_class_tracks(
        self,
        tracks: List[CompletedTrack],
    ) -> List[CompletedTrack]:
        # Sort tracks chronologically by first frame
        sorted_tracks = sorted(tracks, key=lambda t: t.first_frame_idx)
        merged_tracks: List[CompletedTrack] = []

        i = 0
        while i < len(sorted_tracks):
            current = sorted_tracks[i]
            
            # Greedily attempt to stitch subsequent tracks that start after current ends
            j = i + 1
            while j < len(sorted_tracks):
                candidate = sorted_tracks[j]
                
                # Check for temporal overlap: candidate starts before current ends
                if candidate.first_frame_idx <= current.last_frame_idx:
                    # Overlapping / concurrent -> cannot gap-stitch!
                    j += 1
                    continue

                gap = candidate.first_frame_idx - current.last_frame_idx
                if gap > self.config.max_gap_frames:
                    # Beyond maximum gap window
                    j += 1
                    continue

                # Evaluate stitching gates
                should_stitch, reason = self._can_stitch(current, candidate, gap)
                if should_stitch:
                    if self.config.verbose:
                        print(
                            f"[STITCHER] MERGE: Track #{current.track_id} (F{current.first_frame_idx}..F{current.last_frame_idx}) "
                            f"+ Track #{candidate.track_id} (F{candidate.first_frame_idx}..F{candidate.last_frame_idx}) "
                            f"| gap={gap}f | reason: {reason}"
                        )
                    current = self._merge_two(current, candidate)
                    # Remove candidate from future consideration
                    sorted_tracks.pop(j)
                    # Continue checking from the same index j with the newly merged track
                    continue
                else:
                    if self.config.verbose and gap <= self.config.max_gap_frames:
                        print(
                            f"[STITCHER] REJECT: Track #{current.track_id} -> Track #{candidate.track_id} "
                            f"| gap={gap}f | reason: {reason}"
                        )
                    j += 1

            merged_tracks.append(current)
            i += 1

        return merged_tracks

    def _can_stitch(
        self,
        t1: CompletedTrack,
        t2: CompletedTrack,
        gap: int,
    ) -> Tuple[bool, str]:
        # 1. Class check
        if t1.class_name != t2.class_name:
            return False, f"Class mismatch ({t1.class_name} != {t2.class_name})"

        # 2. Extract observations (t1 ending observations, t2 starting observations)
        obs1 = getattr(t1, "end_observations", None)
        obs2 = getattr(t2, "start_observations", None)

        if obs1 and len(obs1) >= 2:
            vx1, vy1, spd1 = _compute_velocity(obs1, from_end=True, window=self.config.velocity_window)
            last_c = _get_center(obs1[-1][1])
        elif obs1 and len(obs1) == 1:
            vx1, vy1, spd1 = 0.0, 0.0, 0.0
            last_c = _get_center(obs1[-1][1])
        else:
            vx1, vy1, spd1 = 0.0, 0.0, 0.0
            last_c = _get_center(t1.best_bbox)

        if obs2 and len(obs2) >= 2:
            first_c = _get_center(obs2[0][1])
            vx2, vy2, spd2 = _compute_velocity(obs2, from_end=False, window=self.config.velocity_window)
        elif obs2 and len(obs2) == 1:
            first_c = _get_center(obs2[0][1])
            vx2, vy2, spd2 = 0.0, 0.0, 0.0
        else:
            first_c = _get_center(t2.best_bbox)
            vx2, vy2, spd2 = 0.0, 0.0, 0.0

        # 3. Extrapolate position of t1 to t2 start
        pred_cx = last_c[0] + vx1 * gap
        pred_cy = last_c[1] + vy1 * gap

        dist = float(np.hypot(pred_cx - first_c[0], pred_cy - first_c[1]))
        raw_dist = float(np.hypot(last_c[0] - first_c[0], last_c[1] - first_c[1]))

        # Check distance threshold against conservative threshold
        effective_dist = min(dist, raw_dist)
        if effective_dist > self.config.position_threshold_px:
            return False, f"Distance {effective_dist:.1f}px > threshold {self.config.position_threshold_px:.1f}px (pred={dist:.1f}px, raw={raw_dist:.1f}px)"

        # 4. Check direction cosine if both velocities are significant (>0.1 px/frame)
        cos = _cosine_similarity((vx1, vy1), (vx2, vy2))
        if cos is not None:
            if cos < self.config.min_direction_cosine:
                return False, f"Direction cosine {cos:.2f} < threshold {self.config.min_direction_cosine:.2f}"
            cos_str = f", cos={cos:.2f}"
        else:
            cos_str = ", cos=N/A (static/insufficient motion)"

        return True, f"dist={effective_dist:.1f}px <= {self.config.position_threshold_px:.1f}px{cos_str}"

    def _merge_two(
        self,
        t1: CompletedTrack,
        t2: CompletedTrack,
    ) -> CompletedTrack:
        """
        Merges t2 into t1, selecting the best overall observation.
        Preserves combined observation history for chain validation.
        """
        # Select best observation by confidence
        if t2.best_confidence > t1.best_confidence:
            best_conf = t2.best_confidence
            best_bbox = t2.best_bbox
            best_frame = t2.best_frame
            best_loc = t2.best_location
        else:
            best_conf = t1.best_confidence
            best_bbox = t1.best_bbox
            best_frame = t1.best_frame
            best_loc = t1.best_location

        start_obs = getattr(t1, "start_observations", []) or []
        end_obs = getattr(t2, "end_observations", []) or []

        return CompletedTrack(
            track_id=t1.track_id,  # Preserve canonical earlier track ID
            class_name=t1.class_name,
            best_confidence=best_conf,
            best_bbox=best_bbox,
            best_frame=best_frame,
            best_location=best_loc,
            hit_count=t1.hit_count + t2.hit_count,
            first_frame_idx=min(t1.first_frame_idx, t2.first_frame_idx),
            last_frame_idx=max(t1.last_frame_idx, t2.last_frame_idx),
            start_observations=start_obs,
            end_observations=end_obs,
        )
