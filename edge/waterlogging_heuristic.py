"""
Waterlogging Heuristic Detector for Edge Pipeline.

Classical CV heuristic: detects flat high-specular-reflection regions
in the lower 40% of the frame (road surface zone) using HSV thresholding.
"""

from typing import Dict, Any, Optional
import cv2
import numpy as np


WATERLOG_MIN_AREA_FRACTION = 0.08  # Flag if specular surface covers >8% of frame


def detect_waterlogging(frame: np.ndarray, location: Any) -> Optional[Dict[str, Any]]:
    """
    HSV-based flat specular reflection region detector.
    - Inspects only lower 40% of the frame (road surface zone).
    - Checks for low saturation (S < 45) and high brightness (V > 195).
    - If total mask area exceeds WATERLOG_MIN_AREA_FRACTION of the total frame,
      returns a safety event dict tagged heuristic_only: True.
    """
    if frame is None or frame.size == 0:
        return None

    h, w = frame.shape[:2]
    roi_top = int(h * 0.6)  # lower 40%
    roi = frame[roi_top:h, :]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    # Reflective wet road: low saturation, high value
    lower_specular = np.array([0, 0, 195], dtype=np.uint8)
    upper_specular = np.array([180, 45, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower_specular, upper_specular)

    # Morphological cleanup to avoid random single-pixel highlights
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)

    white_pixels = int(cv2.countNonZero(cleaned))
    total_frame_pixels = h * w
    area_fraction = white_pixels / max(total_frame_pixels, 1)

    if area_fraction >= WATERLOG_MIN_AREA_FRACTION:
        confidence = min(0.85, round(0.5 + (area_fraction * 2.0), 2))
        return {
            "event_type": "Waterlogging-Candidate",
            "confidence": confidence,
            "heuristic_only": True,
            "details": {
                "area_fraction": round(area_fraction, 4),
                "threshold": WATERLOG_MIN_AREA_FRACTION,
                "roi": "lower_40_pct",
            }
        }

    return None
