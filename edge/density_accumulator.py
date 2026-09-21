"""
Density Accumulator for Vehicle Detections.

Buffers vehicle detection counts per GPS segment cell (~250m bucket)
and flushes aggregated summaries to the backend telemetry service.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone


def compute_segment_key(route_id: str, lat: float, lon: float) -> str:
    """
    Computes a ~250m discrete spatial cell bucket.
    Formula: f"{route_id}:{int(lat*200)/200:.3f}:{int(lon*200)/200:.3f}"
    """
    lat_bucket = int(lat * 200) / 200.0
    lon_bucket = int(lon * 200) / 200.0
    return f"{route_id}:{lat_bucket:.3f}:{lon_bucket:.3f}"


class DensityAccumulator:
    """
    Aggregates vehicle counts across frames for a given segment cell.
    Maintains maximum observed concurrent count per class in that segment
    or accumulated sum across frames.
    Per standard traffic monitoring: we track peak/concurrent counts or sum of occurrences.
    Here we maintain peak concurrent count per frame across the segment window to avoid
    overcounting the same stationary/moving vehicles on every video frame.
    """

    def __init__(self):
        self.current_segment_key: Optional[str] = None
        self.counts: Dict[str, int] = {
            "person": 0,
            "bicycle": 0,
            "car": 0,
            "motorcycle": 0,
            "bus": 0,
            "truck": 0,
        }
        self.frame_count: int = 0
        self.sum_counts: Dict[str, int] = {
            "person": 0,
            "bicycle": 0,
            "car": 0,
            "motorcycle": 0,
            "bus": 0,
            "truck": 0,
        }

    def add_frame(self, segment_key: str, vehicle_detections: list) -> None:
        """
        Record vehicle detections for a frame.
        Counts each class detected in this frame.
        Keeps max peak per frame as well as tracking frame samples.
        """
        if self.current_segment_key is None:
            self.current_segment_key = segment_key

        frame_class_counts: Dict[str, int] = {
            "person": 0,
            "bicycle": 0,
            "car": 0,
            "motorcycle": 0,
            "bus": 0,
            "truck": 0,
        }

        for det in vehicle_detections:
            cls = det.class_name.lower() if hasattr(det, "class_name") else str(det.get("class_name", "")).lower()
            if cls in frame_class_counts:
                frame_class_counts[cls] += 1

        # Track peak concurrent count observed in any single frame in this segment
        for k, v in frame_class_counts.items():
            if v > self.counts[k]:
                self.counts[k] = v
            self.sum_counts[k] += v

        self.frame_count += 1

    def flush(
        self,
        segment_key: str,
        lat: float,
        lon: float,
        route_id: str,
        bus_id: str,
        use_peak: bool = True
    ) -> Dict[str, Any]:
        """
        Builds payload for POST /api/telemetry/density and resets counters.
        """
        selected_counts = dict(self.counts) if use_peak else dict(self.sum_counts)
        total_count = sum(selected_counts.values())

        payload = {
            "segment_key": segment_key,
            "route_id": route_id,
            "bus_id": bus_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "count_person": selected_counts.get("person", 0),
            "count_bicycle": selected_counts.get("bicycle", 0),
            "count_car": selected_counts.get("car", 0),
            "count_motorcycle": selected_counts.get("motorcycle", 0),
            "count_bus": selected_counts.get("bus", 0),
            "count_truck": selected_counts.get("truck", 0),
            "total_count": total_count,
        }

        self.reset()
        self.current_segment_key = None
        return payload

    def reset(self) -> None:
        """Reset internal accumulator state."""
        self.counts = {
            "person": 0,
            "bicycle": 0,
            "car": 0,
            "motorcycle": 0,
            "bus": 0,
            "truck": 0,
        }
        self.sum_counts = {
            "person": 0,
            "bicycle": 0,
            "car": 0,
            "motorcycle": 0,
            "bus": 0,
            "truck": 0,
        }
        self.frame_count = 0
