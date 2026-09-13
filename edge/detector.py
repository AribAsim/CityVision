"""
edge/detector.py
-----------------
Thin wrapper around the existing YOLOv8m model.
Only responsible for inference and returning structured detections.
Does NOT know about GPS, events, or the network layer.
"""
from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import List

import numpy as np
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# Paths (relative to repo root so the file works from any cwd)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = str(
    _REPO_ROOT
    / "RoadDetectionModel"
    / "RoadModel_yolov8m.pt_rounds120_b9"
    / "weights"
    / "best.pt"
)

# Classes the MVP cares about (others are still visible in the preview window
# but NOT dispatched as anomaly events)
ANOMALY_CLASSES = {"Pothole", "Crack", "Crack-Severe", "Speed-Bump"}

CONFIDENCE_THRESHOLD = 0.35


@dataclasses.dataclass
class RawDetection:
    class_name: str
    confidence: float
    bbox: List[int]          # [x1, y1, x2, y2] in pixels


class RoadDetector:
    """
    Wraps the existing YOLOv8m best.pt model.
    Call detect(frame) on every video frame.
    """

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                "Run from the repo root and make sure model weights are present."
            )
        print(f"[DETECTOR] Loading model from: {model_path}")
        self._model = YOLO(model_path)
        print(f"[DETECTOR] Model loaded. Classes: {list(self._model.names.values())}")

    def detect(self, frame: np.ndarray) -> List[RawDetection]:
        """
        Run inference on a BGR frame (OpenCV format).
        Returns ALL detections above the confidence threshold.
        """
        results = self._model.predict(
            frame,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False,
        )[0]

        detections: List[RawDetection] = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            cls_name = self._model.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            detections.append(RawDetection(
                class_name=cls_name,
                confidence=conf,
                bbox=[x1, y1, x2, y2],
            ))

        return detections

    def anomaly_detections(self, frame: np.ndarray) -> List[RawDetection]:
        """Filter detect() to only MVP anomaly classes."""
        return [d for d in self.detect(frame) if d.class_name in ANOMALY_CLASSES]
