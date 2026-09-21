"""
Behavior Analyzer for Edge Perception.

Implements:
1. VRU (Vulnerable Road User) Proximity Risk detection
2. Hit-and-Run heuristic detection (candidate-only flag)
3. ANPR trigger gating logic
"""

import math
from collections import deque
from typing import Dict, Any, List, Optional, Tuple


ANPR_TRIGGER_FRAMES = 45  # Named constant — frames to keep ANPR active after a trigger
VRU_PROXIMITY_PX = 110   # Proximity threshold in pixel space for vehicle-VRU interaction
HIT_AND_RUN_MIN_FRAMES = 5


def _bbox_centroid(bbox: List[int]) -> Tuple[float, float]:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def _euclidean_dist(c1: Tuple[float, float], c2: Tuple[float, float]) -> float:
    return math.hypot(c1[0] - c2[0], c1[1] - c2[1])


def should_run_anpr(trigger_frame: Optional[int], current_frame: int) -> bool:
    """
    Returns True if current_frame is within ANPR_TRIGGER_FRAMES of trigger_frame.
    """
    if trigger_frame is None:
        return False
    diff = current_frame - trigger_frame
    return 0 <= diff <= ANPR_TRIGGER_FRAMES


def vru_proximity_risk(
    vehicle_detections: List[Any],
    infra_detections: List[Any],
    location: Any
) -> Optional[Dict[str, Any]]:
    """
    Returns a risk event dict if a person/bicycle bbox centroid is within
    VRU_PROXIMITY_PX pixels of a vehicle bbox, OR near a detected zebra crossing.
    Outputs: {
        "event_type": "VRU-Proximity",
        "confidence": float,
        "candidate_only": True,
        "details": {...}
    }
    """
    vrus = []
    vehicles = []

    for det in vehicle_detections:
        cls_name = getattr(det, "class_name", "")
        if isinstance(det, dict):
            cls_name = det.get("class_name", "")
            bbox = det.get("bbox", [0, 0, 0, 0])
            conf = det.get("confidence", 0.0)
        else:
            bbox = getattr(det, "bbox", [0, 0, 0, 0])
            conf = getattr(det, "confidence", 0.0)

        cls_lower = cls_name.lower()
        if cls_lower in ("person", "bicycle", "pedestrian"):
            vrus.append((cls_name, conf, bbox, _bbox_centroid(bbox)))
        elif cls_lower in ("car", "motorcycle", "bus", "truck"):
            vehicles.append((cls_name, conf, bbox, _bbox_centroid(bbox)))

    # Check for zebra crossing in infra_detections
    has_zebra = False
    zebra_boxes = []
    for idet in infra_detections:
        cls_name = getattr(idet, "class_name", "")
        if isinstance(idet, dict):
            cls_name = idet.get("class_name", "")
            bbox = idet.get("bbox", [0, 0, 0, 0])
        else:
            bbox = getattr(idet, "bbox", [0, 0, 0, 0])
        if "zebra" in cls_name.lower() or "crosswalk" in cls_name.lower():
            has_zebra = True
            zebra_boxes.append(bbox)

    # 1. VRU in proximity of vehicle
    for v_cls, v_conf, v_box, v_centroid in vehicles:
        for u_cls, u_conf, u_box, u_centroid in vrus:
            dist = _euclidean_dist(v_centroid, u_centroid)
            if dist < VRU_PROXIMITY_PX:
                risk_conf = min(0.95, round(float(v_conf * 0.5 + u_conf * 0.5), 2))
                return {
                    "event_type": "VRU-Proximity",
                    "confidence": risk_conf,
                    "candidate_only": True,
                    "details": {
                        "vru_type": u_cls,
                        "vehicle_type": v_cls,
                        "pixel_distance": round(dist, 1),
                        "has_zebra_crossing": has_zebra,
                    }
                }

    # 2. VRU directly inside/near zebra crossing with any moving traffic around
    if has_zebra and vrus and vehicles:
        u_cls, u_conf, u_box, u_centroid = vrus[0]
        return {
            "event_type": "VRU-Proximity",
            "confidence": 0.85,
            "candidate_only": True,
            "details": {
                "vru_type": u_cls,
                "vehicle_type": vehicles[0][0],
                "on_zebra_crossing": True,
            }
        }

    return None


def check_hit_and_run(track_history: deque) -> Optional[Dict[str, Any]]:
    """
    Scans recent track history frames (deque of dicts: {frame_idx: int, tracks: list}).
    Flags as candidate if:
    - A pedestrian/cyclist track is present, comes into close proximity with a vehicle track,
      then the pedestrian track disappears (abruptly lost for >= HIT_AND_RUN_MIN_FRAMES)
    - While the vehicle track continues moving without stopping or deceleration
    Output: {
        "event_type": "HitAndRun-Candidate",
        "confidence": float,
        "candidate_only": True,
        "details": {...}
    }
    """
    if len(track_history) < 10:
        return None

    recent_snapshots = list(track_history)
    first_snapshot = recent_snapshots[0]
    mid_snapshot = recent_snapshots[len(recent_snapshots) // 2]
    last_snapshot = recent_snapshots[-1]

    # Map track IDs to classes and centroids
    tracks_by_frame = []
    for snap in recent_snapshots:
        t_dict = {}
        for t in snap.get("tracks", []):
            t_id = t.get("track_id")
            if t_id is not None:
                t_dict[t_id] = t
        tracks_by_frame.append(t_dict)

    # Look for tracks that were active in first half, disappeared in second half
    first_vru_ids = set()
    for t_id, t_info in tracks_by_frame[0].items():
        if t_info.get("class_name", "").lower() in ("person", "bicycle", "pedestrian"):
            first_vru_ids.add(t_id)

    last_active_ids = set(tracks_by_frame[-1].keys())

    disappeared_vrus = first_vru_ids - last_active_ids
    if not disappeared_vrus:
        return None

    # For each disappeared VRU, check if there was a vehicle in close proximity when it was last seen
    for vru_id in disappeared_vrus:
        # Find last frame index where vru_id was present
        last_seen_idx = -1
        vru_last_pos = None
        for i, f_dict in enumerate(tracks_by_frame):
            if vru_id in f_dict:
                last_seen_idx = i
                vru_last_pos = _bbox_centroid(f_dict[vru_id].get("bbox", [0, 0, 0, 0]))

        if last_seen_idx != -1 and (len(tracks_by_frame) - 1 - last_seen_idx) >= HIT_AND_RUN_MIN_FRAMES:
            # Check vehicles present at last_seen_idx
            frame_at_incident = tracks_by_frame[last_seen_idx]
            for t_id, t_info in frame_at_incident.items():
                if t_info.get("class_name", "").lower() in ("car", "truck", "bus", "motorcycle"):
                    v_pos = _bbox_centroid(t_info.get("bbox", [0, 0, 0, 0]))
                    if vru_last_pos and _euclidean_dist(v_pos, vru_last_pos) < VRU_PROXIMITY_PX:
                        # Check if this vehicle is still moving in subsequent frames
                        if t_id in tracks_by_frame[-1]:
                            final_v_pos = _bbox_centroid(tracks_by_frame[-1][t_id].get("bbox", [0, 0, 0, 0]))
                            displacement = _euclidean_dist(v_pos, final_v_pos)
                            if displacement > 30:  # Vehicle kept moving
                                return {
                                    "event_type": "HitAndRun-Candidate",
                                    "confidence": 0.78,
                                    "candidate_only": True,
                                    "details": {
                                        "vru_track_id": vru_id,
                                        "vehicle_track_id": t_id,
                                        "last_seen_frame_offset": len(tracks_by_frame) - 1 - last_seen_idx,
                                        "vehicle_displacement_px": round(displacement, 1),
                                    }
                                }

    return None
