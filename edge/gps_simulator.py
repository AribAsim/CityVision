"""
edge/gps_simulator.py
----------------------
Interpolates GPS coordinates (lat, lon, heading) along a predefined
waypoint list as the video progresses frame by frame.

Contract:
  gps = GPSSimulator(waypoints=[...], total_frames=500, fps=30)
  location = gps.get_location(frame_idx=142)
  # -> LocationData(latitude=..., longitude=..., heading_deg=...)
"""
from __future__ import annotations

import dataclasses
import math
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Pre-defined routes – (lat, lon) tuples
# Representative area: Connaught Place, New Delhi, India
# ---------------------------------------------------------------------------
ROUTE_RED = [
    (28.6329, 77.2195),
    (28.6340, 77.2210),
    (28.6355, 77.2225),
    (28.6370, 77.2245),
    (28.6385, 77.2260),
    (28.6400, 77.2280),
    (28.6415, 77.2295),
    (28.6430, 77.2310),
]

ROUTE_BLUE = [
    (28.6139, 77.2090),
    (28.6150, 77.2105),
    (28.6162, 77.2120),
    (28.6175, 77.2140),
    (28.6188, 77.2155),
    (28.6200, 77.2170),
    (28.6212, 77.2185),
    (28.6225, 77.2200),
]

ROUTE_GREEN = [
    (28.6560, 77.2410),
    (28.6575, 77.2430),
    (28.6590, 77.2450),
    (28.6605, 77.2470),
    (28.6620, 77.2490),
    (28.6635, 77.2510),
    (28.6650, 77.2530),
    (28.6665, 77.2550),
]

ROUTE_WAYPOINTS = {
    "ROUTE-RED": ROUTE_RED,
    "ROUTE-BLUE": ROUTE_BLUE,
    "ROUTE-GREEN": ROUTE_GREEN,
}


@dataclasses.dataclass
class LocationData:
    latitude: float
    longitude: float
    heading_deg: float       # 0=North, 90=East, 180=South, 270=West


def _bearing(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate compass bearing from p1 to p2 in degrees."""
    lat1 = math.radians(p1[0])
    lat2 = math.radians(p2[0])
    dlon = math.radians(p2[1] - p1[1])
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    brng = math.degrees(math.atan2(x, y))
    return (brng + 360) % 360


class GPSSimulator:
    """
    Linear interpolation between route waypoints based on frame progress.

    Args:
        route_id: Key into ROUTE_WAYPOINTS dict.
        total_frames: Number of video frames (determines interpolation speed).
    """

    def __init__(self, route_id: str = "ROUTE-RED", total_frames: int = 300):
        waypoints = ROUTE_WAYPOINTS.get(route_id)
        if waypoints is None:
            # Fall back to ROUTE-RED for unknown routes
            waypoints = ROUTE_RED
        self._waypoints = waypoints
        self._total_frames = max(total_frames, 1)

    def get_location(self, frame_idx: int) -> LocationData:
        """Return interpolated location for the given frame index."""
        wp = self._waypoints
        n = len(wp)

        # Map frame_idx → [0, n-1] as a float progress value
        progress = min(frame_idx / self._total_frames, 1.0) * (n - 1)
        seg_idx = int(progress)
        seg_idx = min(seg_idx, n - 2)   # clamp to avoid overrun
        t = progress - seg_idx           # fractional position within segment

        p0 = wp[seg_idx]
        p1 = wp[seg_idx + 1]
        lat = p0[0] + t * (p1[0] - p0[0])
        lon = p0[1] + t * (p1[1] - p0[1])
        heading = _bearing(p0, p1)

        return LocationData(latitude=lat, longitude=lon, heading_deg=heading)
