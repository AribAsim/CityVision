"""
edge/anpr/plate_detector.py
----------------------------
YOLO-based license plate localizer.
Trained on Indian vehicle registration plates.
"""
from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import List, Tuple

import numpy as np
from ultralytics import YOLO

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLATE_MODEL_PATH = str(
    _REPO_ROOT
    / "RoadDetectionModel"
    / "ANPRPlateDetector_yolov8n"
    / "weights"
    / "best.pt"
)

CONFIDENCE_THRESHOLD = 0.35


@dataclasses.dataclass
class PlateBBox:
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]
    crop: np.ndarray


class PlateDetector:
    """
    Detects license plates in video frames and extracts cropped image snippets.
    """

    def __init__(self, model_path: str = DEFAULT_PLATE_MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Plate detector model not found at {model_path}. "
                "Run python scripts/download_models.py first."
            )
        print(f"[ANPR] Loading Plate Detector from: {model_path}")
        self._model = YOLO(model_path)
        print(f"[ANPR] Plate Detector loaded. Classes: {list(self._model.names.values())}")

    def detect_plates(self, frame: np.ndarray) -> List[PlateBBox]:
        results = self._model.predict(
            source=frame,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False,
        )

        plates: List[PlateBBox] = []
        h, w = frame.shape[:2]
        for r in results:
            boxes = r.boxes
            if boxes is None or len(boxes) == 0:
                continue
            for box in boxes:
                conf = float(box.conf[0].item())
                xyxy = [int(v) for v in box.xyxy[0].tolist()]
                x1, y1, x2, y2 = xyxy

                # Bound check
                x1c = max(0, min(x1, w - 1))
                y1c = max(0, min(y1, h - 1))
                x2c = max(x1c + 1, min(x2, w))
                y2c = max(y1c + 1, min(y2, h))

                crop = frame[y1c:y2c, x1c:x2c].copy()
                plates.append(
                    PlateBBox(
                        confidence=conf,
                        bbox=[x1c, y1c, x2c, y2c],
                        crop=crop,
                    )
                )
        return plates
